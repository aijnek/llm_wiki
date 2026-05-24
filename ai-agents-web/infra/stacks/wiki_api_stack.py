from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3 as s3,
)
from constructs import Construct


class WikiApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        runtime_arn: str,
        raw_bucket: s3.IBucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda コードは api/src/ を共有（ProcessorFn / OrchestratorFn で同じパッケージ）
        code = lambda_.Code.from_asset("../api/src")

        # ProcessorFn: AgentCore Runtime を呼んで WebSocket に結果を送り返す
        # 非同期呼び出し専用。API GW の 29s 制約を受けない。
        processor_fn = lambda_.Function(
            self,
            "ProcessorFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.processor_handler",
            code=code,
            timeout=Duration.minutes(15),
            environment={
                "RUNTIME_ARN": runtime_arn,
            },
        )
        # AWS は bedrock-agentcore:InvokeAgentRuntime のチェックをベース ARN と
        # /runtime-endpoint/* ARN の両方に対して行うため resources=["*"] で両方カバーする
        processor_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock-agentcore:InvokeAgentRuntime"],
            resources=["*"],
        ))

        # OrchestratorFn: WebSocket ルートを受け取り ProcessorFn を非同期 invoke して即返す
        orchestrator_fn = lambda_.Function(
            self,
            "OrchestratorFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.websocket_handler",
            code=code,
            timeout=Duration.seconds(25),  # API GW WebSocket integration timeout は 29s
            environment={
                "PROCESSOR_FUNCTION_NAME": processor_fn.function_name,
            },
        )
        processor_fn.grant_invoke(orchestrator_fn)

        # WebSocket API
        ws_api = apigwv2.WebSocketApi(
            self,
            "WsApi",
            api_name="ai-agents-wiki-ws",
            connect_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_integrations.WebSocketLambdaIntegration(
                    "ConnectInt", orchestrator_fn
                )
            ),
            disconnect_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_integrations.WebSocketLambdaIntegration(
                    "DisconnectInt", orchestrator_fn
                )
            ),
            default_route_options=apigwv2.WebSocketRouteOptions(
                integration=apigwv2_integrations.WebSocketLambdaIntegration(
                    "DefaultInt", orchestrator_fn
                )
            ),
        )

        stage = apigwv2.WebSocketStage(
            self,
            "WsStage",
            web_socket_api=ws_api,
            stage_name="prod",
            auto_deploy=True,
        )

        # OrchestratorFn と ProcessorFn の両方に WebSocket postToConnection 権限を付与
        connections_arn = (
            f"arn:{self.partition}:execute-api:{self.region}:{self.account}"
            f":{ws_api.api_id}/{stage.stage_name}/POST/@connections/*"
        )
        for fn in (orchestrator_fn, processor_fn):
            fn.add_to_role_policy(iam.PolicyStatement(
                actions=["execute-api:ManageConnections"],
                resources=[connections_arn],
            ))

        CfnOutput(self, "WsApiUrl", value=stage.url, export_name="WikiWsApiUrl")
        CfnOutput(
            self,
            "ProcessorFnName",
            value=processor_fn.function_name,
            export_name="WikiProcessorFnName",
        )

        # ------------------------------------------------------------------ #
        # Presign Lambda — presigned PUT URL を発行して raw_bucket に直接アップロード
        # ------------------------------------------------------------------ #
        presign_fn = lambda_.Function(
            self,
            "PresignFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.presign_handler",
            code=code,
            timeout=Duration.seconds(10),
            environment={
                "RAW_BUCKET_NAME": raw_bucket.bucket_name,
            },
        )
        raw_bucket.grant_put(presign_fn)

        # HTTP API（CORS 設定済み）
        http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            api_name="ai-agents-wiki-http",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.POST, apigwv2.CorsHttpMethod.OPTIONS],
                allow_headers=["Content-Type"],
                max_age=Duration.hours(1),
            ),
        )

        http_api.add_routes(
            path="/presign-upload",
            methods=[apigwv2.HttpMethod.POST],
            integration=apigwv2_integrations.HttpLambdaIntegration(
                "PresignInt", presign_fn
            ),
        )

        CfnOutput(
            self,
            "HttpApiUrl",
            value=http_api.url or "",
            export_name="WikiHttpApiUrl",
        )

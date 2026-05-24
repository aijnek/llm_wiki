from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class WikiInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------ #
        # VPC
        # Private isolated subnets + S3 Gateway Endpoint（S3 Files BYO 用）
        #
        # AgentCore Runtime が Anthropic API への outbound を自前ネットワークで
        # 処理する場合は nat_gateways=0 のままで良い。
        # もし VPC 経由のインターネットアクセスが必要と判明したら
        # nat_gateways=1 に変更すること（~$32/月 のコスト増）。
        # ------------------------------------------------------------------ #
        self.vpc = vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        # S3 VPC Gateway Endpoint（無料。private subnet から S3 に到達するために必須）
        vpc.add_gateway_endpoint(
            "S3GatewayEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # AgentCore Runtime 用セキュリティグループ
        self.runtime_sg = runtime_sg = ec2.SecurityGroup(
            self,
            "RuntimeSg",
            vpc=vpc,
            description="Bedrock AgentCore Runtime — AI Agents Wiki",
            allow_all_outbound=True,
        )

        # ------------------------------------------------------------------ #
        # S3 バケット
        # ------------------------------------------------------------------ #
        self.wiki_bucket = wiki_bucket = s3.Bucket(
            self,
            "WikiBucket",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        self.raw_bucket = raw_bucket = s3.Bucket(
            self,
            "RawBucket",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )

        # ------------------------------------------------------------------ #
        # ECR リポジトリ（agent-runtime Docker イメージ）
        # ------------------------------------------------------------------ #
        self.ecr_repo = ecr_repo = ecr.Repository(
            self,
            "RuntimeRepo",
            repository_name="ai-agents-wiki-runtime",
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ------------------------------------------------------------------ #
        # IAM ロール（AgentCore Runtime が引き受ける）
        # ------------------------------------------------------------------ #
        self.agentcore_role = agentcore_role = iam.Role(
            self,
            "AgentCoreRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Execution role for AI Agents Wiki — Bedrock AgentCore Runtime",
        )
        wiki_bucket.grant_read_write(agentcore_role)
        raw_bucket.grant_read_write(agentcore_role)
        ecr_repo.grant_pull(agentcore_role)

        # ------------------------------------------------------------------ #
        # Outputs
        # AgentCore Runtime 定義（Phase 2.5）で参照する値をすべてここに出力する
        # ------------------------------------------------------------------ #
        CfnOutput(self, "VpcId", value=vpc.vpc_id, export_name="WikiVpcId")
        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join(s.subnet_id for s in vpc.isolated_subnets),
            export_name="WikiPrivateSubnetIds",
        )
        CfnOutput(
            self,
            "RuntimeSgId",
            value=runtime_sg.security_group_id,
            export_name="WikiRuntimeSgId",
        )
        CfnOutput(
            self,
            "WikiBucketName",
            value=wiki_bucket.bucket_name,
            export_name="WikiBucketName",
        )
        CfnOutput(
            self,
            "RawBucketName",
            value=raw_bucket.bucket_name,
            export_name="WikiRawBucketName",
        )
        CfnOutput(
            self,
            "EcrRepoUri",
            value=ecr_repo.repository_uri,
            export_name="WikiEcrRepoUri",
        )
        CfnOutput(
            self,
            "AgentCoreRoleArn",
            value=agentcore_role.role_arn,
            export_name="WikiAgentCoreRoleArn",
        )

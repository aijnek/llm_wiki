from aws_cdk import (
    CfnOutput,
    Stack,
    aws_bedrockagentcore as bedrockagentcore,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class WikiRuntimeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        ecr_repo: ecr.IRepository,
        execution_role: iam.IRole,
        vpc: ec2.IVpc,
        runtime_sg: ec2.ISecurityGroup,
        wiki_bucket: s3.IBucket,
        raw_bucket: s3.IBucket,
        wiki_access_point_arn: str,
        raw_access_point_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        runtime = bedrockagentcore.CfnRuntime(
            self,
            "AgentCoreRuntime",
            agent_runtime_name="ai_agents_wiki_runtime",
            role_arn=execution_role.role_arn,
            agent_runtime_artifact=bedrockagentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=bedrockagentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=ecr_repo.repository_uri_for_tag("latest"),
                )
            ),
            network_configuration=bedrockagentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="VPC",
                network_mode_config=bedrockagentcore.CfnRuntime.VpcConfigProperty(
                    security_groups=[runtime_sg.security_group_id],
                    subnets=[s.subnet_id for s in vpc.private_subnets],
                ),
            ),
            # S3 Files BYO: wiki/ と raw/ を /mnt/wiki, /mnt/raw にマウント
            filesystem_configurations=[
                bedrockagentcore.CfnRuntime.FilesystemConfigurationProperty(
                    s3_files_access_point=bedrockagentcore.CfnRuntime.S3FilesAccessPointConfigurationProperty(
                        access_point_arn=wiki_access_point_arn,
                        mount_path="/mnt/wiki",
                    )
                ),
                bedrockagentcore.CfnRuntime.FilesystemConfigurationProperty(
                    s3_files_access_point=bedrockagentcore.CfnRuntime.S3FilesAccessPointConfigurationProperty(
                        access_point_arn=raw_access_point_arn,
                        mount_path="/mnt/raw",
                    )
                ),
            ],
            environment_variables={
                "WIKI_BUCKET": wiki_bucket.bucket_name,
                "RAW_BUCKET": raw_bucket.bucket_name,
                "WIKI_ROOT": "/mnt",
            },
            description="AI Agents Wiki - Bedrock AgentCore Runtime",
        )

        CfnOutput(
            self,
            "AgentCoreRuntimeArn",
            value=runtime.attr_agent_runtime_arn,
            export_name="WikiAgentCoreRuntimeArn",
        )
        CfnOutput(
            self,
            "AgentCoreRuntimeId",
            value=runtime.attr_agent_runtime_id,
            export_name="WikiAgentCoreRuntimeId",
        )

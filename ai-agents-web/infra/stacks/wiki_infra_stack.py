from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3files as s3files,
)
from constructs import Construct


class WikiInfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------ #
        # VPC
        # Private subnets + NAT Gateway（AgentCore Runtime の Anthropic API outbound 用）
        # + S3 Gateway Endpoint（S3 API / S3 Files NFS 同期を無料ルートに載せる）
        # ------------------------------------------------------------------ #
        self.vpc = vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        vpc.add_gateway_endpoint(
            "S3GatewayEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # AgentCore Runtime 用セキュリティグループ
        self.runtime_sg = runtime_sg = ec2.SecurityGroup(
            self,
            "RuntimeSg",
            vpc=vpc,
            description="Bedrock AgentCore Runtime - AI Agents Wiki",
            allow_all_outbound=True,
        )

        # S3 Files マウントターゲット用セキュリティグループ
        # NFS (TCP 2049) を RuntimeSg からのみ許可する
        s3files_sg = ec2.SecurityGroup(
            self,
            "S3FilesSg",
            vpc=vpc,
            description="S3 Files mount targets - AI Agents Wiki",
            allow_all_outbound=False,
        )
        s3files_sg.add_ingress_rule(
            peer=runtime_sg,
            connection=ec2.Port.tcp(2049),
            description="NFS from AgentCore Runtime",
        )

        # ------------------------------------------------------------------ #
        # S3 バケット（versioning 必須 — S3 Files がバージョン管理を使う）
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
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.PUT],
                allowed_origins=["*"],
                allowed_headers=["Content-Type"],
                max_age=3000,
            )],
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
        # S3 Files BYO — IAM ロール
        # elasticfilesystem.amazonaws.com が S3 バケットと EventBridge を操作するために使う
        # S3 Files は内部で S3 ↔ ファイルシステムの同期に EventBridge ルールを作成する
        # ------------------------------------------------------------------ #
        s3files_role = iam.Role(
            self,
            "S3FilesRole",
            assumed_by=iam.ServicePrincipal("elasticfilesystem.amazonaws.com"),
            description="S3 Files sync role for AI Agents Wiki",
        )
        for bucket in [wiki_bucket, raw_bucket]:
            s3files_role.add_to_policy(iam.PolicyStatement(
                actions=["s3:ListBucket*"],
                resources=[bucket.bucket_arn],
            ))
            s3files_role.add_to_policy(iam.PolicyStatement(
                actions=[
                    "s3:AbortMultipartUpload",
                    "s3:DeleteObject",
                    "s3:GetObject*",
                    "s3:List*",
                    "s3:PutObject*",
                ],
                resources=[bucket.arn_for_objects("*")],
            ))
        # S3 Files が "DO-NOT-DELETE-S3-Files-*" プレフィックスの EventBridge ルールを管理する
        s3files_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "events:DeleteRule",
                "events:DisableRule",
                "events:EnableRule",
                "events:PutRule",
                "events:PutTargets",
                "events:RemoveTargets",
            ],
            resources=[
                f"arn:{self.partition}:events:{self.region}:{self.account}:rule/DO-NOT-DELETE-S3-Files-*"
            ],
        ))

        # ------------------------------------------------------------------ #
        # S3 Files ファイルシステム + マウントターゲット + アクセスポイント
        # wiki バケット用
        # ------------------------------------------------------------------ #
        wiki_fs = s3files.CfnFileSystem(
            self,
            "WikiFileSystem",
            bucket=wiki_bucket.bucket_arn,
            role_arn=s3files_role.role_arn,
            accept_bucket_warning=True,
        )

        for i, subnet in enumerate(vpc.private_subnets):
            s3files.CfnMountTarget(
                self,
                f"WikiMountTarget{i}",
                file_system_id=wiki_fs.attr_file_system_id,
                subnet_id=subnet.subnet_id,
                security_groups=[s3files_sg.security_group_id],
            )

        wiki_ap = s3files.CfnAccessPoint(
            self,
            "WikiAccessPoint",
            file_system_id=wiki_fs.attr_file_system_id,
        )
        self.wiki_access_point_arn = wiki_ap.attr_access_point_arn

        # ------------------------------------------------------------------ #
        # S3 Files ファイルシステム + マウントターゲット + アクセスポイント
        # raw バケット用
        # ------------------------------------------------------------------ #
        raw_fs = s3files.CfnFileSystem(
            self,
            "RawFileSystem",
            bucket=raw_bucket.bucket_arn,
            role_arn=s3files_role.role_arn,
            accept_bucket_warning=True,
        )

        for i, subnet in enumerate(vpc.private_subnets):
            s3files.CfnMountTarget(
                self,
                f"RawMountTarget{i}",
                file_system_id=raw_fs.attr_file_system_id,
                subnet_id=subnet.subnet_id,
                security_groups=[s3files_sg.security_group_id],
            )

        raw_ap = s3files.CfnAccessPoint(
            self,
            "RawAccessPoint",
            file_system_id=raw_fs.attr_file_system_id,
        )
        self.raw_access_point_arn = raw_ap.attr_access_point_arn

        # ------------------------------------------------------------------ #
        # IAM ロール（AgentCore Runtime が引き受ける）
        # ------------------------------------------------------------------ #
        self.agentcore_role = agentcore_role = iam.Role(
            self,
            "AgentCoreRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Execution role for AI Agents Wiki - Bedrock AgentCore Runtime",
        )
        wiki_bucket.grant_read_write(agentcore_role)
        raw_bucket.grant_read_write(agentcore_role)
        ecr_repo.grant_pull(agentcore_role)

        # S3 Files マウントに必要な権限
        # AgentCore Runtime が S3 Files ファイルシステムをマウントする際に使用する
        agentcore_role.add_to_policy(iam.PolicyStatement(
            actions=["s3files:*"],
            resources=["*"],
        ))

        # SSM Parameter Store から ANTHROPIC_API_KEY を読み取る権限
        agentcore_role.add_to_policy(iam.PolicyStatement(
            actions=["ssm:GetParameter"],
            resources=[
                f"arn:{self.partition}:ssm:{self.region}:{self.account}:parameter/ai-agents-wiki/*"
            ],
        ))

        # ------------------------------------------------------------------ #
        # Outputs
        # ------------------------------------------------------------------ #
        CfnOutput(self, "VpcId", value=vpc.vpc_id, export_name="WikiVpcId")
        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join(s.subnet_id for s in vpc.private_subnets),
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
        CfnOutput(
            self,
            "WikiAccessPointArn",
            value=wiki_ap.attr_access_point_arn,
            export_name="WikiAccessPointArn",
        )
        CfnOutput(
            self,
            "RawAccessPointArn",
            value=raw_ap.attr_access_point_arn,
            export_name="WikiRawAccessPointArn",
        )

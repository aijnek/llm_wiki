import os

import aws_cdk as cdk

from stacks.wiki_infra_stack import WikiInfraStack
from stacks.wiki_runtime_stack import WikiRuntimeStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ap-northeast-1"),
)

infra = WikiInfraStack(app, "WikiInfraStack", env=env)

WikiRuntimeStack(
    app,
    "WikiRuntimeStack",
    ecr_repo=infra.ecr_repo,
    execution_role=infra.agentcore_role,
    vpc=infra.vpc,
    runtime_sg=infra.runtime_sg,
    wiki_bucket=infra.wiki_bucket,
    raw_bucket=infra.raw_bucket,
    env=env,
)

app.synth()

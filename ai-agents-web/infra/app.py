import os

import aws_cdk as cdk

from stacks.wiki_infra_stack import WikiInfraStack

app = cdk.App()

WikiInfraStack(
    app,
    "WikiInfraStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

app.synth()

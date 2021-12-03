#!/usr/bin/env python3
import os

import aws_cdk as cdk

from matchmeta.matchmeta_stack import MatchmetaStack

app = cdk.App()

MatchmetaStack(
    app, 'MatchmetaStack',
    env = cdk.Environment(
        account = os.getenv('CDK_DEFAULT_ACCOUNT'),
        region = 'us-west-2'
    ),
    synthesizer = cdk.DefaultStackSynthesizer(
        qualifier = '4n6ir'
    )
)

cdk.Tags.of(app).add('matchmeta','matchmeta')

app.synth()

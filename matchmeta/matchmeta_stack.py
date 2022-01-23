from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb as _dynamodb,
    aws_events as _events,
    aws_events_targets as _targets,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_logs as _logs,
    aws_s3 as _s3,
    aws_s3_deployment as _deployment,
    aws_s3_notifications as _notifications,
    aws_ssm as _ssm,
)

from constructs import Construct

class MatchmetaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

################################################################################

        qualifier = '4n6ir'                         # <-- Enter CDK Qualifier
        unused_valid_ami = 'ami-8f6815bf'           # <-- US-WEST-2 (Oregon)

################################################################################

        account = Stack.of(self).account
        region = Stack.of(self).region

### DATABASE ###

        table = _dynamodb.Table(
            self, 'table',
            partition_key = {'name': 'pk', 'type': _dynamodb.AttributeType.STRING},
            sort_key = {'name': 'sk', 'type': _dynamodb.AttributeType.STRING},
            billing_mode = _dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy = RemovalPolicy.DESTROY,
            point_in_time_recovery = True
        )
        
        tablessm = _ssm.StringParameter(
            self, 'tablessm',
            description = 'AMI Pipeline DynamoDB Table',
            parameter_name = '/matchmeta/dynamodb/table',
            string_value = table.table_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

### PARAMETERS ###

        amiid = _ssm.StringParameter(
            self, 'amiid',
            description = 'AMI Pipeline Image Id',
            parameter_name = '/matchmeta/ssm/ami',
            string_value = unused_valid_ami,
            tier = _ssm.ParameterTier.STANDARD,
            data_type = _ssm.ParameterDataType.AWS_EC2_IMAGE
        )
        
        ec2type = _ssm.StringParameter(
            self, 'ec2type',
            description = 'AMI Pipeline Instance Type',
            parameter_name = '/matchmeta/ssm/ec2type',
            string_value = 'EMPTY',
            tier = _ssm.ParameterTier.STANDARD,
        )

        archtype = _ssm.StringParameter(
            self, 'archtype',
            description = 'AMI Pipeline Architecture Type',
            parameter_name = '/matchmeta/ssm/arch',
            string_value = 'EMPTY',
            tier = _ssm.ParameterTier.STANDARD,
        )

        deployarn = _ssm.StringParameter(
            self, 'deployarn',
            description = 'AMI Pipeline Deploy Arn',
            parameter_name = '/matchmeta/deploy/arn',
            string_value = 'arn:aws:iam::'+account+':role/cdk-'+qualifier+'-cfn-exec-role-'+account+'-'+region,
            tier = _ssm.ParameterTier.STANDARD,
        )

        stackname = _ssm.StringParameter(
            self, 'stackname',
            description = 'AMI Pipeline Stack Name',
            parameter_name = '/matchmeta/deploy/stack',
            string_value = 'EMPTY',
            tier = _ssm.ParameterTier.STANDARD,
        )

        status = _ssm.StringParameter(
            self, 'status',
            description = 'AMI Pipeline AMI Status',
            parameter_name = '/matchmeta/ami/status',
            string_value = 'EMPTY',
            tier = _ssm.ParameterTier.STANDARD,
        )

### S3 BUCKETS ###

        dwarf = _s3.Bucket(
            self, 'dwarf', versioned = True,
            encryption = _s3.BucketEncryption.S3_MANAGED,
            block_public_access = _s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy = RemovalPolicy.DESTROY
        )

        dwarfssm = _ssm.StringParameter(
            self, 'dwarfssm',
            description = 'AMI Pipeline Dwarf Bucket',
            parameter_name = '/matchmeta/bucket/dwarf',
            string_value = dwarf.bucket_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        raw = _s3.Bucket(
            self, 'raw', versioned = True,
            encryption = _s3.BucketEncryption.S3_MANAGED,
            block_public_access = _s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy = RemovalPolicy.DESTROY
        )

        rawssm = _ssm.StringParameter(
            self, 'rawssm',
            description = 'AMI Pipeline Raw Bucket',
            parameter_name = '/matchmeta/bucket/raw',
            string_value = raw.bucket_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        template = _s3.Bucket(
            self, 'template', versioned = True,
            encryption = _s3.BucketEncryption.S3_MANAGED,
            block_public_access = _s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy = RemovalPolicy.DESTROY
        )

        templatessm = _ssm.StringParameter(
            self, 'templatessm',
            description = 'AMI Pipeline Template Bucket',
            parameter_name = '/matchmeta/bucket/template',
            string_value = template.bucket_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        copyfiles = _deployment.BucketDeployment(
            self, 'copyfiles',
            sources = [_deployment.Source.asset('template')],
            destination_bucket = template,
            prune = False
        )

        upload = _s3.Bucket(
            self, 'upload', versioned = True,
            encryption = _s3.BucketEncryption.S3_MANAGED,
            block_public_access = _s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy = RemovalPolicy.DESTROY
        )

        uploadssm = _ssm.StringParameter(
            self, 'uploadssm',
            description = 'AMI Pipeline Upload Bucket',
            parameter_name = '/matchmeta/bucket/upload',
            string_value = upload.bucket_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

### IAM ROLE ###

        role = _iam.Role(
            self, 'role', 
            assumed_by = _iam.ServicePrincipal(
                'lambda.amazonaws.com'
            )
        )
        
        role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSLambdaBasicExecutionRole'
            )
        )
        
        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    'cloudformation:CreateStack',
                    'cloudformation:DescribeStacks',
                    'cloudformation:DeleteStack',
                    'dynamodb:PutItem',
                    'dynamodb:Query',
                    'dynamodb:UpdateItem',
                    'ec2:DescribeImages',
                    'iam:PassRole',
                    's3:GetObject',
                    's3:PutObject',
                    'ssm:GetParameter',
                    'ssm:PutParameter',
                ],
                resources = ['*']
            )
        )

### AMI LAMBDA ###

        amicompute = _lambda.Function(
            self, 'amicompute',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('amilist'),
            handler = 'amilist.handler',
            timeout = Duration.seconds(900),
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name,
            ),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 512
        )

        amilogs = _logs.LogGroup(
            self, 'amilogs',
            log_group_name = '/aws/lambda/'+amicompute.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        amimonitor = _ssm.StringParameter(
            self, 'amimonitor',
            description = 'AMI Pipeline List Monitor',
            parameter_name = '/matchmeta/monitor/ami',
            string_value = '/aws/lambda/'+amicompute.function_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        amievent = _events.Rule(
            self, 'amievent',
            schedule=_events.Schedule.cron(
                minute='0',
                hour='*',
                month='*',
                week_day='*',
                year='*'
            )
        )
        amievent.add_target(_targets.LambdaFunction(amicompute))

### AMI LAUNCH ###

        amilaunch = _lambda.Function(
            self, 'amilaunch',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('amilaunch'),
            handler = 'amilaunch.handler',
            timeout = Duration.seconds(900),
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name,
                AMI_ID = amiid.parameter_name,
                INSTANCE_TYPE = ec2type.parameter_name,
                ARCH_TYPE = archtype.parameter_name,
                DEPLOY_ARN = deployarn.parameter_name,
                STACK_NAME = stackname.parameter_name,
                TEMPLATE = template.url_for_object('template.cfn.yaml'),
                VALIDTEST = unused_valid_ami
            ),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 512
        )
        
        launchlogs = _logs.LogGroup(
            self, 'launchlogs',
            log_group_name = '/aws/lambda/'+amilaunch.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )
        
        launchmonitor = _ssm.StringParameter(
            self, 'launchmonitor',
            description = 'AMI Pipeline Launch Monitor',
            parameter_name = '/matchmeta/monitor/launch',
            string_value = '/aws/lambda/'+amilaunch.function_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        launchevent = _events.Rule(
            self, 'launchevent',
            schedule=_events.Schedule.cron(
                minute='*/15',
                hour='*',
                month='*',
                week_day='*',
                year='*'
            )
        )
        launchevent.add_target(_targets.LambdaFunction(amilaunch))

### ZIP DWARF ###

        zipdwarf = _lambda.Function(
            self, 'zipdwarf',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('zipdwarf'),
            handler = 'zipdwarf.handler',
            timeout = Duration.seconds(900),
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name,
                AMI_ID = amiid.parameter_name,
                DWARF_S3 = dwarf.bucket_name,
                UPLOAD_S3 = upload.bucket_name,
            ),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 512
        )

        zipdwarflogs = _logs.LogGroup(
            self, 'zipdwarflogs',
            log_group_name = '/aws/lambda/'+zipdwarf.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        zipdwarfmonitor = _ssm.StringParameter(
            self, 'zipdwarfmonitor',
            description = 'AMI Pipeline Zip Dwarf Monitor',
            parameter_name = '/matchmeta/monitor/dwarf',
            string_value = '/aws/lambda/'+zipdwarf.function_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        notification_zipdwarf = _notifications.LambdaDestination(zipdwarf)
        dwarf.add_event_notification(_s3.EventType.OBJECT_CREATED, notification_zipdwarf)

### ZIP RAW ###

        zipraw = _lambda.Function(
            self, 'zipraw',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('zipraw'),
            handler = 'zipraw.handler',
            timeout = Duration.seconds(900),
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name,
                AMI_ID = amiid.parameter_name,
                RAW_S3 = raw.bucket_name,
                UPLOAD_S3 = upload.bucket_name,
                INSTANCE_TYPE = ec2type.parameter_name,
                ARCH_TYPE = archtype.parameter_name,
                DEPLOY_ARN = deployarn.parameter_name,
                STACK_NAME = stackname.parameter_name,
                STATUS_SSM = status.parameter_name,
                VALIDTEST = unused_valid_ami
            ),
            architecture = _lambda.Architecture.ARM_64,
            memory_size = 512
        )

        ziprawlogs = _logs.LogGroup(
            self, 'ziprawlogs',
            log_group_name = '/aws/lambda/'+zipraw.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        ziprawmonitor = _ssm.StringParameter(
            self, 'ziprawmonitor',
            description = 'AMI Pipeline Zip Raw Monitor',
            parameter_name = '/matchmeta/monitor/raw',
            string_value = '/aws/lambda/'+zipraw.function_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        notification_zipraw = _notifications.LambdaDestination(zipraw)
        raw.add_event_notification(_s3.EventType.OBJECT_CREATED, notification_zipraw)

###

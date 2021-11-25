import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

    parameter = boto3.client('ssm')
    
    ami_response = parameter.get_parameter(
        Name = os.environ['AMI_ID']
    )
    ami_value = ami_response['Parameter']['Value']
    
    type_response = parameter.get_parameter(
        Name = os.environ['INSTANCE_TYPE']
    )
    type_value = ami_response['Parameter']['Value']
                
    deploy_response = parameter.get_parameter(
        Name = os.environ['DEPLOY_ARN']
    )
    deploy_value = ami_response['Parameter']['Value']
    
    status_response = parameter.get_parameter(
        Name = os.environ['STATUS_SSM']
    )
    status_value = ami_response['Parameter']['Value']
    
    if ami_value == 'EMPTY':
    
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    
        response = table.query(
            KeyConditionExpression = Key('pk').eq('AMAZON#')
        )
        responsedata = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression = Key('pk').eq('AMAZON#'),
                ExclusiveStartKey = response['LastEvaluatedKey']
            )
            responsedata.update(response['Items'])
    
        for item in responsedata:
            if item['running'] == 'ON':
                if item['architecture'] == 'x86_64':
                    ec2type = 't3a.nano'
                elif item['architecture'] == 'arm64':
                    ec2type = 't4g.nano'
                
                response = parameter.put_parameter(
                    Name = os.environ['AMI_ID'],
                    Description = 'AMI Pipeline Image Id',
                    Value = item['imageid'],
                    Overwrite = True
                )

                response = parameter.put_parameter(
                    Name = os.environ['INSTANCE_TYPE'],
                    Description = 'AMI Pipeline Instance Type',
                    Value = ec2type,
                    Overwrite = True
                )

                response = parameter.put_parameter(
                    Name = os.environ['ARCH_TYPE'],
                    Description = 'AMI Pipeline Instance Type',
                    Value = item['architecture'],
                    Overwrite = True
                )


    #            client = boto3.client('cloudformation')
    #            response = client.create_stack(
    #                StackName='RunmetaV2Stack',
    #                TemplateURL=os.environ['S3_BUCKET_BINARY'],
    #                Capabilities=['CAPABILITY_IAM'],
    #                RoleARN=deploy_value
    #            )

                break
    
    else:
        print('RUNNING')
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Launch Amazon Linux AMI')
    }
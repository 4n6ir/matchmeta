import boto3
import json
import logging
import os
import uuid
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

    cfn_client = boto3.client('cloudformation')
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    
    parameter = boto3.client('ssm')
    
    ami_response = parameter.get_parameter(
        Name = os.environ['AMI_ID']
    )
    ami_value = ami_response['Parameter']['Value']
    
    type_response = parameter.get_parameter(
        Name = os.environ['INSTANCE_TYPE']
    )
    type_value = type_response['Parameter']['Value']
                
    deploy_response = parameter.get_parameter(
        Name = os.environ['DEPLOY_ARN']
    )
    deploy_value = deploy_response['Parameter']['Value']
    
    status_response = parameter.get_parameter(
        Name = os.environ['STATUS_SSM']
    )
    status_value = status_response['Parameter']['Value']
    
    if ami_value == 'EMPTY':
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

                uid = uuid.uuid1()
                
                response = cfn_client.create_stack(
                    StackName = 'runmeta-'+str(uid),
                    TemplateURL = os.environ['TEMPLATE'],
                    Capabilities = ['CAPABILITY_IAM'],
                    RoleARN = deploy_value
                )

                response = parameter.put_parameter(
                    Name = os.environ['STACK_NAME'],
                    Value = 'runmeta-'+str(uid),
                    Type = 'String',
                    Overwrite = True
                )

                break
    
    else:
        stack_response = parameter.get_parameter(
            Name = os.environ['STACK_NAME']
        )
        stack_value = status_response['Parameter']['Value']
        
        response = cfn_client.describe_stacks()
    
        for stack in response['Stacks']:
            if 'ROLLBACK_COMPLETE' in stack['StackStatus']:
                logger.info('ERROR: '+str(stack))
                print(' ')
                print(stack['StackName'])
                
                
                #if stack['StackName'] == stack_value:
                #    print('**MADE IT**')
                #    print(ami_value)
                #    updated = table.update_item(
                #        Key = {
                #            'pk': 'AMAZON#',
                #            'sk': 'AMAZON#'+ami_value
                #        },
                #        UpdateExpression = 'set running = :r',
                #        ExpressionAttributeValues = {
                #            ':r': 'ERROR',
                #        },
                #        ReturnValues = 'UPDATED_NEW'
                #    )
                
                # Delete Stack
                # Update 3 SSM to EMPTY

    return {
        'statusCode': 200,
        'body': json.dumps('Launch Amazon Linux AMI')
    }
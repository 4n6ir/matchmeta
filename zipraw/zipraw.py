import boto3
import json
import logging
import os
import zipfile
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    
    objectname = event['Records'][0]['s3']['object']['key']

    parameter = boto3.client('ssm')
    
    ami_response = parameter.get_parameter(
        Name = os.environ['AMI_ID']
    )
    ami_value = ami_response['Parameter']['Value']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    response = table.query(KeyConditionExpression=Key('pk').eq('AMAZON#'))
    responsedata = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.query(
            KeyConditionExpression=Key('pk').eq('AMAZON#'),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        responsedata.update(response['Items'])

    for item in responsedata:
        if item['imageid'] == ami_value:
            name = item['name']
            parse = item['creation'].split('T')
            out = parse[0].split('-') 
            year = out[0]
            month = out[1]
            day = out[2]
            
    s3 = boto3.client('s3')
    s3.download_file(os.environ['RAW_S3'], objectname, '/tmp/'+objectname)

    with zipfile.ZipFile('/tmp/'+name+'.txt.zip', 'w', compression=zipfile.ZIP_LZMA) as zipf:
        zipf.write('/tmp/'+objectname,name+'.txt')

    s3.upload_file('/tmp/'+name+'.txt.zip',os.environ['UPLOAD_S3'],year+'/'+month+'/'+day+'/'+name+'/'+name+'.txt.zip')

    stack_response = parameter.get_parameter(
        Name = os.environ['STACK_NAME']
    )
    stack_value = stack_response['Parameter']['Value']

    deploy_response = parameter.get_parameter(
        Name = os.environ['DEPLOY_ARN']
    )
    deploy_value = deploy_response['Parameter']['Value']
    
    cfn_client = boto3.client('cloudformation')
        
    response = cfn_client.describe_stacks()
    
    for stack in response['Stacks']:

        if stack['StackName'] == stack_value:
            logger.info('SUCCESS: '+str(stack))
                    
            updated = table.update_item(
                Key = {
                    'pk': 'AMAZON#',
                    'sk': 'AMAZON#'+ami_value
                },
                UpdateExpression = 'set running = :r',
                ExpressionAttributeValues = {
                    ':r': 'OFF',
                },
                ReturnValues = 'UPDATED_NEW'
            )
                    
            response = cfn_client.delete_stack(
                StackName = stack_value,
                RoleARN = deploy_value
            )

            response = parameter.put_parameter(
                Name = os.environ['AMI_ID'],
                Description = 'AMI Pipeline Image Id',
                Value = 'EMPTY',
                Overwrite = True
            )

            response = parameter.put_parameter(
                Name = os.environ['INSTANCE_TYPE'],
                Description = 'AMI Pipeline Instance Type',
                Value = 'EMPTY',
                Overwrite = True
            )

            response = parameter.put_parameter(
                Name = os.environ['ARCH_TYPE'],
                Description = 'AMI Pipeline Instance Type',
                Value = 'EMPTY',
                Overwrite = True
            )

    return {
        'statusCode': 200,
        'body': json.dumps('Compress Raw MatchMeta.Info')
    }
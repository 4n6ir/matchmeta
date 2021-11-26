import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    
    instance = boto3.client('ec2')
    
    response = instance.describe_images(
        Filters = [
            {
                'Name': 'architecture',
                'Values': ['x86_64','arm64']    
            }
        ],
        Owners = ['amazon']
    )
    
    status = 'EMPTY'

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    for item in response['Images']:
        if item['PlatformDetails'] == 'Linux/UNIX':
            if item['ImageLocation'].startswith('amazon/amzn'):     ### AMI Starts
                if item['ImageLocation'].endswith('-gp2'):          ### AMI Ends
                    exists = table.query(KeyConditionExpression=Key('pk').eq('AMAZON#') & Key('sk').eq('AMAZON#'+item['ImageId']))
                    if len(exists['Items']) == 0 and item['Public'] is True and item['State'] == 'available':
                        status = 'NEW'
                        table.put_item(
                            Item= {
                                'pk': 'AMAZON#',
                                'sk': 'AMAZON#'+item['ImageId'],
                                'name': item['Name'],
                                'description': item['Description'],
                                'creation': item['CreationDate'],
                                'imageid': item['ImageId'],
                                'architecture': item['Architecture'],
                                'running': 'ON'
                            }
                        )
                        client = boto3.client('ssm')
                        client.put_parameter(
                            Name = os.environ['STATUS_SSM'],
                            Value = status,
                            Type = 'String',
                            Overwrite = True
                        )

    return {
        'statusCode': 200,
        'body': json.dumps('List Amazon Linux AMIs')
    }
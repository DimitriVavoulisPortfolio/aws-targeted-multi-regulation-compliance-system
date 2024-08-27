import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Get the S3 bucket and key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        logger.info(f"Processing file {key} from bucket {bucket}")
        
        # Read the file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        
        # Parse the JSON content
        regulation_data = json.loads(file_content)
        
        # Get the DynamoDB table name from environment variables
        table_name = os.environ.get('DYNAMODB_TABLE')
        if not table_name:
            raise ValueError("DYNAMODB_TABLE environment variable is not set")
        
        table = dynamodb.Table(table_name)
        logger.info(f"Using DynamoDB table: {table_name}")
        
        # Insert each rule into DynamoDB
        for rule in regulation_data['rules']:
            item = {
                'RuleId': rule['ruleId'],
                'Regulation': regulation_data['regulation'],
                'ResourceType': rule['resourceType'],
                'Description': rule['description'],
                'ComplianceCheck': json.dumps(rule['complianceCheck']),
                'RemediationAction': rule['remediationAction']
            }
            table.put_item(Item=item)
            logger.info(f"Inserted rule {rule['ruleId']} into DynamoDB")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed {len(regulation_data["rules"])} rules')
        }
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise
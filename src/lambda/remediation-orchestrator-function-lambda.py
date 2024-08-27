import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')
sns = boto3.client('sns')

MAX_RETRIES = 3
BATCH_SIZE = 25  # Number of items to process in each batch

def lambda_handler(event, context):
    try:
        compliance_table = dynamodb.Table(os.environ['COMPLIANCE_RESULTS_TABLE'])
        state_machine_arn = os.environ['REMEDIATION_STATE_MACHINE_ARN']
        sns_topic_arn = os.environ['SNS_TOPIC_ARN']

        total_processed = 0
        total_remediation_started = 0
        last_evaluated_key = None

        while True:
            scan_kwargs = {
                'FilterExpression': Attr('ComplianceType').eq('NON_COMPLIANT'),
                'Limit': BATCH_SIZE
            }
            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = last_evaluated_key

            response = compliance_table.scan(**scan_kwargs)
            non_compliant_items = response.get('Items', [])

            for item in non_compliant_items:
                total_processed += 1
                if start_remediation(item, state_machine_arn):
                    total_remediation_started += 1

            last_evaluated_key = response.get('LastEvaluatedKey')
            if not last_evaluated_key:
                break

        logger.info(f"Processed {total_processed} non-compliant items. Started remediation for {total_remediation_started}.")
        
        if total_processed > 0:
            send_summary_notification(sns_topic_arn, total_processed, total_remediation_started)

        return {
            'statusCode': 200,
            'body': json.dumps(f'Processed {total_processed} items, initiated remediation for {total_remediation_started}')
        }
    except Exception as e:
        logger.error(f"Error in Remediation Orchestrator: {str(e)}")
        send_error_notification(sns_topic_arn, str(e))
        raise

def start_remediation(item, state_machine_arn):
    for attempt in range(MAX_RETRIES):
        try:
            stepfunctions.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps({
                    'ruleId': item['RuleId'],
                    'resourceType': item['ResourceType'],
                    'resourceIds': item['NonCompliantResources'],
                    'regulation': item['Regulation']
                })
            )
            logger.info(f"Started remediation for {item['ResourceType']} {item['NonCompliantResources']}")
            return True
        except ClientError as e:
            logger.warning(f"Attempt {attempt + 1} failed to start remediation for {item['ResourceType']} {item['NonCompliantResources']}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to start remediation after {MAX_RETRIES} attempts for {item['ResourceType']} {item['NonCompliantResources']}")
                return False
    return False

def send_summary_notification(topic_arn, total_processed, total_remediated):
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject="Compliance Remediation Summary",
            Message=f"Processed {total_processed} non-compliant items. Initiated remediation for {total_remediated}."
        )
    except ClientError as e:
        logger.error(f"Failed to send summary notification: {str(e)}")

def send_error_notification(topic_arn, error_message):
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject="Compliance Remediation Error",
            Message=f"An error occurred in the Remediation Orchestrator: {error_message}"
        )
    except ClientError as e:
        logger.error(f"Failed to send error notification: {str(e)}")
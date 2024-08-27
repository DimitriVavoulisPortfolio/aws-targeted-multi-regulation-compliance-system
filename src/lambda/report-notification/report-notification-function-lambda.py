import boto3
import json
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client('sns')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Extract the bucket name and object key from the S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        logger.info(f"Processing new report: {key} in bucket {bucket}")

        # Get metadata about the report
        metadata = s3.head_object(Bucket=bucket, Key=key)
        file_size = metadata['ContentLength']
        last_modified = metadata['LastModified']

        # Construct the S3 console URL (not public, requires AWS console access)
        s3_console_url = f"https://s3.console.aws.amazon.com/s3/object/{bucket}?prefix={key}"

        # Prepare the message
        message = f"""A new compliance report is available:

File: {key}
Size: {file_size / 1024:.2f} KB
Generated: {last_modified}

You can access this report in the AWS S3 Console:
{s3_console_url}

For any questions or concerns about this report, please contact the compliance team.
"""

        # Send the notification
        response = sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=message,
            Subject="New Compliance Report Available"
        )

        logger.info(f"Notification sent successfully for report: {key}")
        return {
            'statusCode': 200,
            'body': json.dumps('Notification sent successfully')
        }
    except ClientError as e:
        logger.error(f"Error sending notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error sending notification')
        }
    except KeyError as e:
        logger.error(f"Error processing event, missing key: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid event structure')
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Unexpected error occurred')
        }

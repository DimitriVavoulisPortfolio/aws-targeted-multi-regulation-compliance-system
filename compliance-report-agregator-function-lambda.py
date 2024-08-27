import boto3
import json
import os
import logging
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
    try:
        source_table = dynamodb.Table(os.environ['COMPLIANCE_RESULTS_TABLE'])
        report_table = dynamodb.Table(os.environ['COMPLIANCE_REPORT_TABLE'])

        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)

        results = query_with_pagination(source_table, start_time, end_time)

        aggregated_data = aggregate_results(results)

        report_id = f"daily_report_{end_time.strftime('%Y%m%d')}"
        store_report(report_table, report_id, end_time, aggregated_data)

        publish_metrics(aggregated_data)

        logger.info(f"Successfully generated report {report_id}")
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully generated report {report_id}')
        }
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise

def query_with_pagination(table, start_time, end_time):
    results = []
    last_evaluated_key = None
    while True:
        if last_evaluated_key:
            response = table.query(
                IndexName='timestamp-index',
                KeyConditionExpression=Key('timestamp').between(start_time.isoformat(), end_time.isoformat()),
                ExclusiveStartKey=last_evaluated_key
            )
        else:
            response = table.query(
                IndexName='timestamp-index',
                KeyConditionExpression=Key('timestamp').between(start_time.isoformat(), end_time.isoformat())
            )
        
        results.extend(response['Items'])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        if not last_evaluated_key:
            break
    
    return results

def aggregate_results(results):
    aggregated_data = {
        'total_resources_scanned': len(results),
        'compliant_resources': 0,
        'non_compliant_resources': 0,
        'compliance_by_regulation': {},
        'compliance_by_resource_type': {}
    }

    for item in results:
        update_aggregation(aggregated_data, item)

    return aggregated_data

def update_aggregation(aggregated_data, item):
    if item['ComplianceType'] == 'COMPLIANT':
        aggregated_data['compliant_resources'] += 1
    else:
        aggregated_data['non_compliant_resources'] += 1

    regulation = item['Regulation']
    resource_type = item['ResourceType']

    update_category_aggregation(aggregated_data['compliance_by_regulation'], regulation, item['ComplianceType'])
    update_category_aggregation(aggregated_data['compliance_by_resource_type'], resource_type, item['ComplianceType'])

def update_category_aggregation(category_dict, key, compliance_type):
    if key not in category_dict:
        category_dict[key] = {'compliant': 0, 'non_compliant': 0}
    if compliance_type == 'COMPLIANT':
        category_dict[key]['compliant'] += 1
    else:
        category_dict[key]['non_compliant'] += 1

def store_report(table, report_id, timestamp, data):
    try:
        table.put_item(
            Item={
                'report_id': report_id,
                'timestamp': timestamp.isoformat(),
                'data': json.dumps(data)
            }
        )
    except ClientError as e:
        logger.error(f"Error storing report: {str(e)}")
        raise

def publish_metrics(data):
    try:
        cloudwatch.put_metric_data(
            Namespace='ComplianceReports',
            MetricData=[
                {
                    'MetricName': 'TotalResourcesScanned',
                    'Value': data['total_resources_scanned'],
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'ComplianceRate',
                    'Value': (data['compliant_resources'] / data['total_resources_scanned']) * 100 if data['total_resources_scanned'] > 0 else 0,
                    'Unit': 'Percent'
                }
            ]
        )
    except ClientError as e:
        logger.error(f"Error publishing CloudWatch metrics: {str(e)}")
        # Don't raise here, as this is not critical for report generation
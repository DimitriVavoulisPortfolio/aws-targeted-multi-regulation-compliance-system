import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
config = boto3.client('config')
ec2 = boto3.client('ec2')
rds = boto3.client('rds')
s3 = boto3.client('s3')
cloudtrail = boto3.client('cloudtrail')
kms = boto3.client('kms')
iam = boto3.client('iam')
elb = boto3.client('elbv2')

def lambda_handler(event, context):
    try:
        # Get all rules from DynamoDB
        rules_table = dynamodb.Table('regulation-dynamo-compliance-rules')
        response = rules_table.scan()
        rules = response['Items']
        
        compliance_results = []
        
        for rule in rules:
            result = check_compliance(rule)
            compliance_results.append(result)
        
        # TODO: Store compliance results
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Scanned {len(compliance_results)} rules across multiple regulations')
        }
    except Exception as e:
        logger.error(f"Error in resource scanner: {str(e)}")
        raise

def check_compliance(rule):
    resource_type = rule['ResourceType']
    compliance_check = json.loads(rule['ComplianceCheck'])
    
    if compliance_check['type'] == 'AWSConfig':
        return check_aws_config(rule)
    elif compliance_check['type'] == 'CustomCheck':
        return check_custom(rule)
    else:
        logger.warning(f"Unknown compliance check type: {compliance_check['type']}")
        return None

def check_aws_config(rule):
    config_rule_name = json.loads(rule['ComplianceCheck'])['configRuleName']
    response = config.describe_compliance_by_config_rule(
        ConfigRuleNames=[config_rule_name]
    )
    compliance_type = response['ComplianceByConfigRules'][0]['Compliance']['ComplianceType']
    non_compliant_resources = []
    if compliance_type == 'NON_COMPLIANT':
        non_compliant_resources = get_non_compliant_resources(config_rule_name)
    
    return {
        'RuleId': rule['RuleId'],
        'Regulation': rule['Regulation'],
        'ResourceType': rule['ResourceType'],
        'ComplianceType': compliance_type,
        'NonCompliantResources': non_compliant_resources
    }

def check_custom(rule):
    check_function = json.loads(rule['ComplianceCheck'])['checkFunction']
    check_functions = {
        'checkEC2PublicAccess': check_ec2_public_access,
        'checkRDSEncryption': check_rds_encryption,
        'checkS3BucketEncryption': check_s3_bucket_encryption,
        'checkCloudTrailEnabled': check_cloudtrail_enabled,
        'checkKMSKeyRotation': check_kms_key_rotation,
        'checkIAMPasswordPolicy': check_iam_password_policy,
        'checkVPCFlowLogs': check_vpc_flow_logs,
        'checkELBHttpsOnly': check_elb_https_only
    }
    if check_function in check_functions:
        return check_functions[check_function](rule)
    else:
        logger.warning(f"Custom check not implemented: {check_function}")
        return None

def check_ec2_public_access(rule):
    instances = ec2.describe_instances()
    non_compliant_instances = []

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            for interface in instance['NetworkInterfaces']:
                if interface.get('Association', {}).get('PublicIp'):
                    non_compliant_instances.append(instance['InstanceId'])
                    break

    return create_result(rule, non_compliant_instances)

def check_rds_encryption(rule):
    rds_instances = rds.describe_db_instances()
    non_compliant_instances = [
        instance['DBInstanceIdentifier']
        for instance in rds_instances['DBInstances']
        if not instance['StorageEncrypted']
    ]
    return create_result(rule, non_compliant_instances)

def check_s3_bucket_encryption(rule):
    buckets = s3.list_buckets()
    non_compliant_buckets = []
    for bucket in buckets['Buckets']:
        try:
            encryption = s3.get_bucket_encryption(Bucket=bucket['Name'])
        except s3.exceptions.ClientError:
            non_compliant_buckets.append(bucket['Name'])
    return create_result(rule, non_compliant_buckets)

def check_cloudtrail_enabled(rule):
    trails = cloudtrail.describe_trails()
    if not trails['trailList']:
        return create_result(rule, ['No CloudTrail configured'])
    return create_result(rule, [])

def check_kms_key_rotation(rule):
    keys = kms.list_keys()
    non_compliant_keys = []
    for key in keys['Keys']:
        try:
            rotation_status = kms.get_key_rotation_status(KeyId=key['KeyId'])
            if not rotation_status['KeyRotationEnabled']:
                non_compliant_keys.append(key['KeyId'])
        except kms.exceptions.ClientError:
            # Skip keys that we don't have permission to check
            pass
    return create_result(rule, non_compliant_keys)

def check_iam_password_policy(rule):
    try:
        policy = iam.get_account_password_policy()
        # Check if policy meets your specific requirements
        # This is a simple check, adjust as needed
        if policy['PasswordPolicy']['MinimumPasswordLength'] < 14:
            return create_result(rule, ['IAM password policy'])
    except iam.exceptions.NoSuchEntityException:
        return create_result(rule, ['No IAM password policy set'])
    return create_result(rule, [])

def check_vpc_flow_logs(rule):
    vpcs = ec2.describe_vpcs()
    non_compliant_vpcs = []
    for vpc in vpcs['Vpcs']:
        flow_logs = ec2.describe_flow_logs(
            Filter=[{'Name': 'resource-id', 'Values': [vpc['VpcId']]}]
        )
        if not flow_logs['FlowLogs']:
            non_compliant_vpcs.append(vpc['VpcId'])
    return create_result(rule, non_compliant_vpcs)

def check_elb_https_only(rule):
    load_balancers = elb.describe_load_balancers()
    non_compliant_elbs = []
    for lb in load_balancers['LoadBalancers']:
        listeners = elb.describe_listeners(LoadBalancerArn=lb['LoadBalancerArn'])
        for listener in listeners['Listeners']:
            if listener['Protocol'] != 'HTTPS':
                non_compliant_elbs.append(lb['LoadBalancerName'])
                break
    return create_result(rule, non_compliant_elbs)

def create_result(rule, non_compliant_resources):
    return {
        'RuleId': rule['RuleId'],
        'Regulation': rule['Regulation'],
        'ResourceType': rule['ResourceType'],
        'ComplianceType': 'NON_COMPLIANT' if non_compliant_resources else 'COMPLIANT',
        'NonCompliantResources': non_compliant_resources
    }

def get_non_compliant_resources(config_rule_name):
    response = config.get_compliance_details_by_config_rule(
        ConfigRuleName=config_rule_name,
        ComplianceTypes=['NON_COMPLIANT']
    )
    return [eval_result['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceId'] 
            for eval_result in response['EvaluationResults']]

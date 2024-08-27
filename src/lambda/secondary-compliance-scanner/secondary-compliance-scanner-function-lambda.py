import boto3
import json
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS service clients
dynamodb = boto3.resource('dynamodb')
ec2 = boto3.client('ec2')
redshift = boto3.client('redshift')
config = boto3.client('config')
ssm = boto3.client('ssm')
guardduty = boto3.client('guardduty')
shield = boto3.client('shield')
wafv2 = boto3.client('wafv2')
macie = boto3.client('macie2')
secrets_manager = boto3.client('secretsmanager')
inspector = boto3.client('inspector2')

def lambda_handler(event, context):
    try:
        # Get relevant rules from DynamoDB
        rules_table = dynamodb.Table('regulation-dynamo-compliance-rules')
        response = rules_table.scan()
        rules = response['Items']
        
        compliance_results = []
        
        for rule in rules:
            result = check_compliance(rule)
            if result:
                compliance_results.append(result)
        
        # TODO: Store compliance results in a separate DynamoDB table
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Scanned {len(compliance_results)} additional rules')
        }
    except Exception as e:
        logger.error(f"Error in secondary resource scanner: {str(e)}")
        raise

def check_compliance(rule):
    resource_type = rule['ResourceType']
    check_functions = {
        'AWS::EBS::Volume': check_ebs_encryption,
        'AWS::Redshift::Cluster': check_redshift_encryption,
        'AWS::Config::ConfigRule': check_config_rules,
        'AWS::SSM::Parameter': check_ssm_parameters,
        'AWS::GuardDuty::Detector': check_guardduty_enabled,
        'AWS::Shield::Protection': check_shield_protection,
        'AWS::WAFv2::WebACL': check_waf_rules,
        'AWS::Macie::Session': check_macie_enabled,
        'AWS::SecretsManager::Secret': check_secrets_rotation,
        'AWS::Inspector::AssessmentTemplate': check_inspector_findings
    }
    
    if resource_type in check_functions:
        return check_functions[resource_type](rule)
    else:
        logger.warning(f"Check not implemented for resource type: {resource_type}")
        return None

def check_ebs_encryption(rule):
    try:
        volumes = ec2.describe_volumes()
        non_compliant_volumes = [
            vol['VolumeId'] for vol in volumes['Volumes']
            if not vol['Encrypted']
        ]
        return create_result(rule, non_compliant_volumes)
    except ClientError as e:
        logger.error(f"Error checking EBS encryption: {str(e)}")
        return None

def check_redshift_encryption(rule):
    try:
        clusters = redshift.describe_clusters()
        non_compliant_clusters = [
            cluster['ClusterIdentifier'] for cluster in clusters['Clusters']
            if not cluster['Encrypted']
        ]
        return create_result(rule, non_compliant_clusters)
    except ClientError as e:
        logger.error(f"Error checking Redshift encryption: {str(e)}")
        return None

def check_config_rules(rule):
    try:
        config_rules = config.describe_config_rules()
        non_compliant_rules = [
            rule['ConfigRuleName'] for rule in config_rules['ConfigRules']
            if rule['ConfigRuleState'] != 'ACTIVE'
        ]
        return create_result(rule, non_compliant_rules)
    except ClientError as e:
        logger.error(f"Error checking Config rules: {str(e)}")
        return None

def check_ssm_parameters(rule):
    try:
        parameters = ssm.describe_parameters()
        non_compliant_params = [
            param['Name'] for param in parameters['Parameters']
            if 'Type' in param and not param['Type'].startswith('SecureString')
        ]
        return create_result(rule, non_compliant_params)
    except ClientError as e:
        logger.error(f"Error checking SSM parameters: {str(e)}")
        return None

def check_guardduty_enabled(rule):
    try:
        detectors = guardduty.list_detectors()
        if not detectors['DetectorIds']:
            return create_result(rule, ['GuardDuty not enabled'])
        return create_result(rule, [])
    except ClientError as e:
        logger.error(f"Error checking GuardDuty: {str(e)}")
        return None

def check_shield_protection(rule):
    try:
        subscription = shield.describe_subscription()
        if not subscription['Subscription']['ActiveStatus']:
            return create_result(rule, ['Shield Advanced not active'])
        return create_result(rule, [])
    except ClientError as e:
        logger.error(f"Error checking Shield protection: {str(e)}")
        return None

def check_waf_rules(rule):
    try:
        web_acls = wafv2.list_web_acls(Scope='REGIONAL')
        if not web_acls['WebACLs']:
            return create_result(rule, ['No WAF Web ACLs configured'])
        return create_result(rule, [])
    except ClientError as e:
        logger.error(f"Error checking WAF rules: {str(e)}")
        return None

def check_macie_enabled(rule):
    try:
        macie_status = macie.get_macie_session()
        if macie_status['status'] != 'ENABLED':
            return create_result(rule, ['Macie not enabled'])
        return create_result(rule, [])
    except ClientError as e:
        logger.error(f"Error checking Macie status: {str(e)}")
        return None

def check_secrets_rotation(rule):
    try:
        secrets = secrets_manager.list_secrets()
        non_compliant_secrets = [
            secret['Name'] for secret in secrets['SecretList']
            if 'RotationEnabled' not in secret or not secret['RotationEnabled']
        ]
        return create_result(rule, non_compliant_secrets)
    except ClientError as e:
        logger.error(f"Error checking Secrets Manager rotation: {str(e)}")
        return None

def check_inspector_findings(rule):
    try:
        findings = inspector.list_findings()
        if findings['findings']:
            return create_result(rule, ['Active Inspector findings exist'])
        return create_result(rule, [])
    except ClientError as e:
        logger.error(f"Error checking Inspector findings: {str(e)}")
        return None

def create_result(rule, non_compliant_resources):
    return {
        'RuleId': rule['RuleId'],
        'Regulation': rule['Regulation'],
        'ResourceType': rule['ResourceType'],
        'ComplianceType': 'NON_COMPLIANT' if non_compliant_resources else 'COMPLIANT',
        'NonCompliantResources': non_compliant_resources
    }

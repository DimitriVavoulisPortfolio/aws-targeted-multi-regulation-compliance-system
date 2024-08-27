# Targeted Multi-Regulation Compliance System Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Components](#components)
   - [Compliance Scanner Lambda](#compliance-scanner-lambda)
   - [Remediation Orchestrator](#remediation-orchestrator)
   - [DynamoDB Tables](#dynamodb-tables)
   - [S3 Buckets](#s3-buckets)
   - [EventBridge Rules](#eventbridge-rules)
   - [CloudWatch Alarms](#cloudwatch-alarms)
   - [SNS Topics](#sns-topics)
   - [KMS Keys](#kms-keys)
   - [IAM Roles](#iam-roles)
4. [Setup and Deployment](#setup-and-deployment)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Adding New Regulations](#adding-new-regulations)
8. [Creating Custom Regulations](#creating-custom-regulations)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [FAQ](#faq)

## Introduction

The Targeted Multi-Regulation Compliance System is a comprehensive solution for automating compliance checks and remediation across multiple regulatory frameworks. It is designed to work with pre-tagged AWS resources, providing real-time analysis of compliance status and automated remediation actions.

## System Architecture

The system uses a serverless architecture built on AWS services. Here's an overview of how the components interact:

1. EventBridge triggers the Compliance Scanner Lambda on a scheduled basis.
2. The Lambda function scans pre-tagged AWS resources for compliance issues.
3. Results are stored in DynamoDB tables.
4. Non-compliant resources trigger a Step Functions workflow for remediation.
5. Remediation actions are executed by dedicated Lambda functions.
6. CloudWatch monitors the system and triggers alarms when necessary.
7. SNS sends notifications about compliance issues and system alerts.
8. All sensitive data is encrypted using KMS keys.

## Components

### Compliance Scanner Lambda

This is the core component of the system. It performs the following tasks:
- Scans pre-tagged AWS resources
- Checks compliance against defined rules
- Stores results in DynamoDB
- Triggers remediation workflows for non-compliant resources

Configuration: The Lambda function's behavior can be adjusted through environment variables defined in the CloudFormation template.

### Remediation Orchestrator

Implemented as a Step Functions workflow, this component:
- Receives information about non-compliant resources
- Determines the appropriate remediation action
- Executes the remediation Lambda function
- Updates the compliance status after remediation

Configuration: The workflow definition is in the CloudFormation template. Customize it to add new remediation steps or alter the flow.

### DynamoDB Tables

The system uses several DynamoDB tables:
- `ComplianceRules`: Stores the compliance rules for each regulation
- `ComplianceResults`: Stores the results of compliance scans
- `RemediationStatus`: Tracks the status of remediation actions

Schema details for each table are defined in the CloudFormation template.

### S3 Buckets

The system uses S3 buckets for:
- Storing compliance reports
- Keeping regulation JSON files

Bucket names and configurations are defined in the CloudFormation template.

### EventBridge Rules

An EventBridge rule triggers the compliance scan on a scheduled basis. You can modify the schedule in the CloudFormation template.

### CloudWatch Alarms

CloudWatch alarms monitor:
- Lambda function errors
- DynamoDB throttling
- Overall compliance rate

Alarm configurations are in the CloudFormation template. Adjust thresholds as needed.

### SNS Topics

SNS topics are used for various notifications:
- Compliance issues
- System alerts
- Remediation status updates

Topic ARNs are outputs of the CloudFormation stack. Subscribe to these topics to receive notifications.

### KMS Keys

KMS keys are used to encrypt:
- Data in DynamoDB tables
- S3 bucket contents
- SNS messages

Key policies are defined in the CloudFormation template.

### IAM Roles

IAM roles follow the principle of least privilege. Key roles include:
- ComplianceScannerRole
- RemediationLambdaRole
- StepFunctionsRole

Role definitions and policies are in the CloudFormation template.

## Setup and Deployment

1. Clone the repository
2. Create an S3 bucket for CloudFormation templates
3. Upload templates to the S3 bucket
4. Deploy the master stack using CloudFormation

Detailed steps are in the README.md file.

## Configuration

1. Regulation rules are defined in JSON files in the `regulations` folder.
2. Lambda function configurations can be adjusted in the CloudFormation template.
3. Compliance check schedules can be modified in the EventBridge rule definition.

## Usage

After deployment:
1. Tag your AWS resources with the appropriate regulation tags.
2. The system will automatically start scanning these resources based on the configured schedule.
3. View compliance results in the ComplianceResults DynamoDB table.
4. Check the SNS topics for notifications about compliance issues.

## Adding New Regulations

1. Create a new JSON file in the `regulations` folder.
2. Update the RegulationParserLambda to handle the new regulation type.
3. Add custom compliance checks to the ComplianceScannerLambda if needed.
4. Update reporting components to include the new regulation.

## Creating Custom Regulations

Creating custom regulations allows you to tailor the compliance system to your organization's specific needs. Here's a detailed guide on how to create and implement custom regulations:

1. **Define the Regulation Structure**:
   Create a new JSON file in the `regulations` folder with the following structure:

   ```json
   {
     "regulation": "CUSTOM_REG_NAME",
     "version": "1.0",
     "lastUpdated": "YYYY-MM-DD",
     "rules": [
       {
         "ruleId": "CUSTOM-1",
         "description": "Description of the rule",
         "resourceType": "AWS::Service::Resource",
         "complianceCheck": {
           "type": "CustomCheck",
           "checkFunction": "checkCustomCompliance"
         },
         "remediationAction": "CustomRemediation"
       }
     ]
   }
   ```

2. **Implement Custom Checks**:
   In the ComplianceScannerLambda, add a new function to perform your custom check:

   ```python
   def check_custom_compliance(resource, rule):
       # Implement your custom compliance check logic here
       # Return True if compliant, False if non-compliant
       pass
   ```

3. **Update the Compliance Scanner**:
   Modify the main scanning function to include your custom check:

   ```python
   def scan_resource(resource, rule):
       if rule['complianceCheck']['type'] == 'CustomCheck':
           if rule['complianceCheck']['checkFunction'] == 'checkCustomCompliance':
               return check_custom_compliance(resource, rule)
       # ... existing checks ...
   ```

4. **Implement Custom Remediation**:
   Create a new Lambda function for custom remediation:

   ```python
   def custom_remediation(resource_id, rule):
       # Implement your custom remediation logic here
       pass
   ```

5. **Update the Remediation Orchestrator**:
   Modify the Step Functions workflow to include your custom remediation:

   ```json
   {
     "CustomRemediation": {
       "Type": "Task",
       "Resource": "arn:aws:lambda:function:custom-remediation-function",
       "Next": "UpdateComplianceStatus"
     }
   }
   ```

6. **Update IAM Roles**:
   Ensure that the ComplianceScannerRole and RemediationLambdaRole have the necessary permissions to perform your custom checks and remediations.

7. **Test Your Custom Regulation**:
   Use the local development setup to test your custom regulation before deploying to production.

Remember to thoroughly document your custom regulations, including the rationale behind each rule and the expected behavior of custom checks and remediations.

## Troubleshooting

Common issues and their solutions:
1. Lambda function timeouts: Increase the function timeout in the CloudFormation template.
2. DynamoDB throttling: Increase the provisioned capacity for the affected table.
3. Failed remediations: Check the Step Functions execution history for error details.

## Best Practices

1. Regularly review and update compliance rules.
2. Monitor CloudWatch alarms and adjust thresholds as needed.
3. Periodically review IAM roles and tighten permissions if possible.
4. Keep the AWS CLI and SAM CLI updated for local development.

## FAQ

Q: How often does the system scan resources?
A: The system uses an EventBridge (CloudWatch Events) rule to schedule scans. By default, this is set to run daily, but the exact time can be configured in the CloudFormation template. Check the `EventBridge Rules` section of the template for the current schedule.

Q: Can I modify the scanning schedule?
A: Yes, you can adjust the EventBridge rule in the CloudFormation template. Look for the `ComplianceScanSchedule` resource and modify the `ScheduleExpression` property. For example, to run at 2 AM UTC daily:
```yaml
ComplianceScanSchedule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: "cron(0 2 * * ? *)"
    # ... other properties ...
```

Q: Can I add custom compliance rules?
A: Yes, by adding new rules to the regulation JSON files and updating the ComplianceScannerLambda. See the "Creating Custom Regulations" section for detailed instructions.

Q: How are remediation actions customized?
A: By modifying the Step Functions workflow and creating new remediation Lambda functions. This process is outlined in the "Creating Custom Regulations" section.

For more questions, please open an issue on the GitHub repository.


# Deployment Guide for Multi-Regulation Compliance System

This guide provides detailed instructions for deploying the Multi-Regulation Compliance System. Follow these steps in order to ensure a smooth deployment process.

## Prerequisites

Before beginning the deployment, ensure you have:

1. An AWS account with appropriate permissions
2. AWS CLI installed and configured
3. AWS CloudFormation knowledge
4. Git installed (for cloning the repository)

## Deployment Steps

### Stage 1: Core Infrastructure

1. **Deploy the S3 bucket for storing regulation files**
   - Navigate to the CloudFormation console
   - Create a new stack
   - Upload the template: `regulation-files-bucket.yaml`
   - Follow the prompts to create the stack

2. **Deploy the DynamoDB table for compliance rules**
   - Create a new CloudFormation stack
   - Upload the template: `regulation-files-dynamodb.yaml`
   - Complete the stack creation process

3. **Create the KMS key for encryption**
   - Create another CloudFormation stack
   - Use the template: `kms-key-report-bucket`
   - Finish the stack creation

### Stage 2: Compliance Scanning

4. **Create the IAM role for the Regulation Parser Lambda**
   - Go to the IAM console
   - Create a new role
   - Attach the policy from: `iam-policy-regulation-parser-function.json`

5. **Deploy the Regulation Parser Lambda function**
   - Navigate to the Lambda console
   - Create a new function
   - Upload the code from: `regulation-parser-function-lambda.py`
   - Assign the IAM role created in step 4

6. **Create the IAM role for the Compliance Scanner Lambda**
   - In the IAM console, create another role
   - Use the policy from: `iam-policy-primary-compliance-scanner-function.json`

7. **Deploy the Compliance Scanner Lambda function**
   - Create a new Lambda function
   - Use the code from: `primary-compliance-scanner-function-lambda.py`
   - Assign the IAM role from step 6

8. **Create the IAM role for the Secondary Compliance Scanner Lambda**
   - Create another IAM role
   - Attach the policy from: `iam-policy-secondary-compliance-scanner-function.json`

9. **Deploy the Secondary Compliance Scanner Lambda function**
   - Create another Lambda function
   - Upload the code from: `secondary-compliance-scanner-function-lambda.py`
   - Assign the IAM role from step 8

### Stage 3: Remediation

10. **Create the IAM role for the Remediation Orchestrator Lambda**
    - In the IAM console, create a new role
    - Use the policy from: `iam-policy-remediation-orchestrator-function.json`

11. **Deploy the Remediation Orchestrator Lambda function**
    - Create a new Lambda function
    - Upload the code from: `remediation-orchestrator-function-lambda.py`
    - Assign the IAM role from step 10

12. **Deploy the Step Functions state machine for remediation**
    - Go to the CloudFormation console
    - Create a new stack
    - Use the template: `remediation-workflow-state-machine.yaml`
    - Complete the stack creation process

### Stage 4: Reporting

13. **Deploy the DynamoDB table for storing compliance reports**
    - Create a new CloudFormation stack
    - Upload the template: `compliance-report-dynamodb.yaml`
    - Follow the prompts to create the stack

14. **Deploy the S3 bucket for storing generated reports**
    - Create another CloudFormation stack
    - Use the template: `compliance-report-bucket`
    - Complete the stack creation

15. **Create the IAM role for the Compliance Report Aggregator Lambda**
    - In the IAM console, create a new role
    - Attach the policy from: `iam-policy-compliance-report-agregator-function.json`

16. **Deploy the Compliance Report Aggregator Lambda function**
    - Create a new Lambda function
    - Upload the code from: `compliance-report-agregator-function-lambda.json`
    - Assign the IAM role from step 15

17. **Create the IAM role for the PDF Report Generator Lambda**
    - Create another IAM role
    - Use the policy from: `iam-policy-pdf-compliance-report-generation-function.json`

18. **Deploy the PDF Report Generator Lambda function**
    - Create a new Lambda function
    - Use the code from: `pdf-compliance-report-generation-function-lambda.py`
    - Assign the IAM role from step 17

### Stage 5: Notifications and Monitoring

19. **Deploy the SNS topic for compliance alerts**
    - Create a new CloudFormation stack
    - Upload the template: `compliance-reporting-sns-topics.yaml`
    - Complete the stack creation process

20. **Create the IAM role for the Report Notification Lambda**
    - In the IAM console, create a new role
    - Attach the policy from: `iam-policy-report-notification-function.json`

21. **Deploy the Report Notification Lambda function**
    - Create a new Lambda function
    - Upload the code from: `report-notification-function-lambda.py`
    - Assign the IAM role from step 20

22. **Deploy CloudWatch alarms for monitoring**
    - Create a new CloudFormation stack
    - Use the template: `compliance-reporting-cloudwatch-alarms.yaml`
    - Follow the prompts to create the stack

### Stage 6: Scheduling

23. **Deploy the EventBridge rule for daily compliance scans**
    - Create a new CloudFormation stack
    - Upload the template: `daily-report-eventbridge-rule.yaml`
    - Complete the stack creation process

24. **Deploy the EventBridge rule for report generation**
    - Create another CloudFormation stack
    - Use the template: `report-generation-scheduler.yaml`
    - Finish the stack creation

## Final Steps

25. **Upload regulation JSON files**
    - Navigate to the S3 console
    - Find the bucket created in step 1
    - Upload your regulation JSON files to this bucket

26. **Verify all components**
    - Check each deployed resource in its respective AWS console
    - Ensure all components are correctly configured and have the necessary permissions

27. **Run a test compliance scan**
    - Manually trigger the Compliance Scanner Lambda function
    - Check the results in the ComplianceResults DynamoDB table
    - Verify that the remediation workflow is triggered for any non-compliant resources

## Post-Deployment Checklist

- [ ] All CloudFormation stacks are in a "CREATE_COMPLETE" state
- [ ] All Lambda functions are deployed and have the correct IAM roles
- [ ] Step Functions state machine is created and linked to the correct Lambda functions
- [ ] DynamoDB tables are created and have the correct schemas
- [ ] S3 buckets are created with the proper permissions and encryption settings
- [ ] SNS topics are created and subscribed to the correct endpoints
- [ ] CloudWatch alarms are set up and in an "OK" state
- [ ] EventBridge rules are created and targeting the correct resources
- [ ] Regulation JSON files are uploaded to the correct S3 bucket
- [ ] A test compliance scan has been run successfully

## Troubleshooting

If you encounter issues during deployment:

1. Check CloudFormation events for any failed steps
2. Verify IAM roles have the necessary permissions
3. Check Lambda function logs in CloudWatch for any errors
4. Ensure all resource names and ARNs are correctly referenced across your components

## Maintenance

- Regularly review and update IAM policies to maintain least privilege
- Keep Lambda function code up to date with the latest best practices
- Periodically review CloudWatch logs and metrics to ensure system health

For detailed information on each component and its configuration options, refer to the main documentation. If you encounter any issues not covered in this guide, please consult the project's issue tracker or reach out to the maintainers for support.

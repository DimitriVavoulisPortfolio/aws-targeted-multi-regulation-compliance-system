# Targeted Multi-Regulation Compliance System

Author: Dimitri Vavoulis

## Project Overview

The Targeted Multi-Regulation Compliance System is an advanced, cloud-based solution designed to automate and streamline compliance checks across multiple regulatory frameworks. This system demonstrates expertise in cloud architecture, security, and regulatory compliance, showcasing the ability to create a flexible, scalable, and highly secure compliance management platform.

The system is built entirely on AWS services, leveraging infrastructure-as-code principles through AWS CloudFormation for repeatable and consistent deployments. It's designed to meet the stringent requirements of various industries including, but not limited to, healthcare, finance, education, and government sectors.

This project is intended to be deployed in your own AWS account. There is no live demo as the system requires specific AWS resources and configurations.

## Features

- Automated daily compliance checks using pre-tagged AWS resources
- Support for multiple regulatory frameworks (e.g., HIPAA, PCI DSS, SOX, GDPR, CCPA)
- Real-time analysis of compliance status across various AWS services
- User-defined compliance rules using JSON configuration files
- Automated remediation actions for non-compliant resources
- Comprehensive reporting and alerting system
- Secure data storage with encryption at rest and in transit
- Scalable and cost-effective serverless architecture

## Supported Regulations

This system supports compliance checks and remediation for the following regulations:

1. **HIPAA** (Health Insurance Portability and Accountability Act): Protects sensitive patient health information.
2. **PCI DSS** (Payment Card Industry Data Security Standard): Ensures secure handling of credit card information.
3. **SOX** (Sarbanes-Oxley Act): Protects against fraudulent financial practices in public companies.
4. **GDPR** (General Data Protection Regulation): Strengthens data protection for EU residents.
5. **CCPA** (California Consumer Privacy Act): Enhances privacy rights for California residents.
6. **FERPA** (Family Educational Rights and Privacy Act): Protects the privacy of student education records.
7. **GLBA** (Gramm-Leach-Bliley Act): Requires financial institutions to explain information-sharing practices and protect sensitive data.
8. **FISMA** (Federal Information Security Management Act): Protects government information and operations.
9. **NIST 800-53**: Provides security control guidelines for federal information systems.
10. **ISO 27001**: Specifies requirements for information security management systems.

Each regulation is implemented with specific rules and compliance checks tailored to its requirements. Users can enable or disable checks for each regulation based on their specific compliance needs.

## Architecture

```mermaid
graph TD
    A[EventBridge] -->|Trigger daily| B[Compliance Scanner Lambda]
    B -->|Scan resources| C[AWS Resources]
    B -->|Store results| D[DynamoDB]
    B -->|Trigger remediation| E[Step Functions]
    E -->|Execute| F[Remediation Lambda]
    G[S3] -->|Store| H[Compliance Reports]
    I[CloudWatch] -->|Monitor & Alert| J[SNS]
    K[KMS] -->|Encrypt| D
    K -->|Encrypt| G
    L[IAM] -->|Access Control| B
    L -->|Access Control| E
    L -->|Access Control| F
    M[CloudTrail] -->|Audit| N[Logs]
```

## Technical Stack

- **Infrastructure as Code**: AWS CloudFormation
- **Compute**: AWS Lambda
- **Workflow Management**: AWS Step Functions
- **Database**: AWS DynamoDB
- **Storage**: AWS S3
- **Messaging & Notifications**: AWS SNS
- **Monitoring & Logging**: AWS CloudWatch, AWS CloudTrail
- **Security**: AWS KMS, AWS IAM
- **Scheduling**: AWS EventBridge

## Key Components

1. **Compliance Scanner Lambda**: Core component that scans pre-tagged AWS resources for compliance.
2. **Remediation Orchestrator**: AWS Step Functions workflow to manage remediation actions.
3. **DynamoDB Tables**: Store compliance rules, scan results, and remediation status.
4. **S3 Buckets**: Store compliance reports and regulation JSON files.
5. **EventBridge Rules**: Schedule daily compliance scans and report generation.
6. **CloudWatch Alarms**: Monitor compliance rates and system health.
7. **SNS Topics**: Manage notifications for compliance issues and system alerts.
8. **KMS Keys**: Encrypt sensitive data at rest and in transit.
9. **IAM Roles**: Manage fine-grained access control across all components.

## Deployment

For deployment instructions, please refer to the Deployment Guide.

## Adding New Regulations

To add support for a new regulation:

1. Create a new JSON file in the `regulations` folder, following the existing format.
2. Update the `RegulationParserLambda` to handle the new regulation type.
3. Add any necessary custom compliance checks to the `ComplianceScannerLambda`.
4. Update the reporting components to include the new regulation in summaries.

## Future Enhancements

- Integration with AWS Config for continuous compliance monitoring
- Machine learning-based predictive compliance analysis
- Support for custom, user-defined compliance rules
- Integration with popular ticketing systems for managing remediation tasks
- Mobile application for on-the-go compliance monitoring

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Dimitri Vavoulis - dimitrivavoulis3@gmail.com

Project Link: [https://github.com/dimitrivavoulisportfolio/targeted-multi-regulation-compliance-system](https://github.com/dimitrivavoulisportfolio/targeted-multi-regulation-compliance-system)

import boto3
import json
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from botocore.exceptions import ClientError
import io
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Fetch the latest compliance data
        compliance_data = get_latest_compliance_data()
        
        # Generate the PDF
        pdf_buffer = generate_pdf_report(compliance_data)
        
        # Save the PDF to S3
        report_date = datetime.now().strftime("%Y%m%d")
        filename = f"compliance_report_{report_date}.pdf"
        s3.put_object(
            Bucket=os.environ['REPORT_BUCKET'],
            Key=filename,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf',
            ServerSideEncryption='AES256'
        )
        
        logger.info(f"Report generated and saved as {filename}")
        return {
            'statusCode': 200,
            'body': json.dumps(f'Report generated and saved as {filename}')
        }
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise

def get_latest_compliance_data():
    try:
        table = dynamodb.Table(os.environ['COMPLIANCE_REPORT_TABLE'])
        response = table.query(
            IndexName='TimestampIndex',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('timestamp').lte(datetime.now().isoformat()),
            ScanIndexForward=False,
            Limit=1
        )
        if not response['Items']:
            raise ValueError("No compliance data found")
        return json.loads(response['Items'][0]['data'])
    except ClientError as e:
        logger.error(f"Error fetching compliance data: {str(e)}")
        raise

def generate_pdf_report(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=1))
    
    # Title
    elements.append(Paragraph("Compliance Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Date
    elements.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Summary
    elements.append(Paragraph("Executive Summary", styles['Heading2']))
    summary_text = f"This report provides an overview of our compliance status as of {datetime.now().strftime('%Y-%m-%d')}. "
    summary_text += f"Out of {data['total_resources_scanned']} resources scanned, {data['compliant_resources']} are compliant "
    summary_text += f"and {data['non_compliant_resources']} are non-compliant with our security policies."
    elements.append(Paragraph(summary_text, styles['Justify']))
    elements.append(Spacer(1, 12))
    
    # Summary Table
    summary_data = [
        ["Metric", "Count"],
        ["Total Resources", data['total_resources_scanned']],
        ["Compliant Resources", data['compliant_resources']],
        ["Non-Compliant Resources", data['non_compliant_resources']]
    ]
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 12))
    
    # Compliance by Regulation
    elements.append(Paragraph("Compliance by Regulation", styles['Heading2']))
    reg_data = [["Regulation", "Compliant", "Non-Compliant", "Compliance Rate"]]
    for reg, values in data['compliance_by_regulation'].items():
        total = values['compliant'] + values['non_compliant']
        rate = (values['compliant'] / total) * 100 if total > 0 else 0
        reg_data.append([reg, values['compliant'], values['non_compliant'], f"{rate:.2f}%"])
    reg_table = Table(reg_data)
    reg_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(reg_table)
    
    # Generate the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

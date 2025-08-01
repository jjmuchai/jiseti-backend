# utils/emailer.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_status_email(to_email, subject, message):
    """
    Send email notification using SendGrid
    
    Args:
        to_email (str): Recipient's email address
        subject (str): Email subject
        message (str): Email body content
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        from_email = os.getenv('FROM_EMAIL', 'noreply@jiseti.go.ke')
        
        if not sendgrid_api_key:
            logger.error("SENDGRID_API_KEY environment variable not set")
            return False
        
        # Create the email message
        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=format_email_html(message)
        )
        
        # Send the email
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(mail)
        
        logger.info(f"Email sent successfully to {to_email}. Status code: {response.status_code}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {str(e)}")
        return False

def send_sms_notification(phone_number, message):
    """
    Send SMS notification using Twilio
    
    Args:
        phone_number (str): Recipient's phone number
        message (str): SMS message content
    
    Returns:
        bool: True if SMS sent successfully, False otherwise
    """
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, from_number]):
            logger.error("Twilio credentials not properly configured")
            return False
        
        client = Client(account_sid, auth_token)
        
        # Ensure phone number has country code
        if not phone_number.startswith('+'):
            # Assume Kenya country code if not provided
            phone_number = '+254' + phone_number.lstrip('0')
        
        # Send SMS
        message_instance = client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
        
        logger.info(f"SMS sent successfully to {phone_number}. Message SID: {message_instance.sid}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending SMS to {phone_number}: {str(e)}")
        return False

def format_email_html(message):
    """
    Format plain text message into HTML for better email presentation
    
    Args:
        message (str): Plain text message
    
    Returns:
        str: HTML formatted email content
    """
    # Convert line breaks to HTML breaks
    html_message = message.replace('\n', '<br>')
    
    # Create a nicely formatted HTML email template
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jiseti Notification</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, hsl(163, 100%, 19%) 0%, hsl(163, 80%, 35%) 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 20px;
            }}
            .content {{
                padding: 20px 0;
                font-size: 16px;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 14px;
                border-top: 1px solid #eee;
                margin-top: 30px;
            }}
            .button {{
                display: inline-block;
                background: hsl(163, 100%, 19%);
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">🛡️ Jiseti Platform</h2>
                <p style="margin: 5px 0 0 0;">Fighting Corruption Together</p>
            </div>
            
            <div class="content">
                {html_message}
            </div>
            
            <div class="footer">
                <p>This is an automated message from Jiseti Platform.</p>
                <p>© 2025 Jiseti. Building a corruption-free Africa.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template

def send_welcome_email(to_email, user_name):
    """
    Send welcome email to new users
    
    Args:
        to_email (str): New user's email address
        user_name (str): New user's name
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "Welcome to Jiseti - Fight Corruption Together! 🛡️"
    message = f"""Hello {user_name},

Welcome to Jiseti! 🎉

Thank you for joining our mission to build a corruption-free Africa. You are now part of a community dedicated to transparency and accountability.

With your Jiseti account, you can:
✅ Report corruption incidents (Red-flags)
✅ Request government intervention 
✅ Track your reports in real-time
✅ Support other citizens' reports
✅ Add evidence with photos and videos

Getting Started:
1. Create your first report from your dashboard
2. Add location details and evidence
3. Track progress as authorities respond
4. Receive email and SMS updates

Together, we can make a difference!

Best regards,
The Jiseti Team

P.S. Your voice matters in building a better Africa."""

    return send_status_email(to_email, subject, message)

def send_record_created_email(to_email, user_name, record_title):
    """
    Send confirmation email when a user creates a new record
    
    Args:
        to_email (str): User's email address
        user_name (str): User's name
        record_title (str): Title of the created record
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "Report Submitted Successfully - Jiseti"
    message = f"""Hello {user_name},

Your report has been submitted successfully! ✅

📋 Report Details:
Title: "{record_title}"
Status: Draft
Submitted: Just now

What happens next?
• Your report is currently in "Draft" status
• You can edit or add more details while it's in draft
• Once ready, it will be reviewed by our admin team
• You'll receive email and SMS updates on any status changes

Need to make changes?
Visit your dashboard to edit your report before it goes under investigation.

Thank you for helping build a more transparent Africa!

Best regards,
The Jiseti Admin Team"""

    return send_status_email(to_email, subject, message)

def send_anonymous_report_confirmation(email, tracking_token, record_title):
    """
    Send confirmation for anonymous reports
    
    Args:
        email (str): Optional email for tracking
        tracking_token (str): Tracking token for the report
        record_title (str): Title of the report
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not email:
        return True  # No email provided for anonymous report
    
    subject = "Anonymous Report Submitted - Jiseti"
    message = f"""Your anonymous report has been submitted successfully!

📋 Report Details:
Title: "{record_title}"
Tracking Token: {tracking_token}
Status: Under Investigation
Submitted: Just now

Your report is now under investigation by our admin team. Since this is an anonymous report, we cannot send you automatic updates, but you can check the status using your tracking token.

IMPORTANT: Save your tracking token to check status later!

Thank you for helping fight corruption in Africa!

Best regards,
The Jiseti Team"""

    return send_status_email(email, subject, message)

def send_status_change_notification(user_email, user_name, record_title, old_status, new_status, reason=None, resolution_notes=None, phone_number=None):
    """
    Send comprehensive status change notification via email and SMS
    
    Args:
        user_email (str): User's email
        user_name (str): User's name
        record_title (str): Record title
        old_status (str): Previous status
        new_status (str): New status
        reason (str): Reason for change (optional)
        resolution_notes (str): Resolution details (optional)
        phone_number (str): User's phone for SMS (optional)
    
    Returns:
        dict: Status of email and SMS delivery
    """
    # Prepare email message
    status_messages = {
        'under-investigation': '🔍 Your report is now being actively investigated by our team.',
        'resolved': '✅ Great news! Your report has been resolved.',
        'rejected': '❌ Your report has been reviewed and rejected.'
    }
    
    status_message = status_messages.get(new_status, f'Your report status has changed to {new_status}.')
    
    email_subject = f"Status Update: {record_title}"
    email_body = f"""Hello {user_name},

{status_message}

📋 Report Details:
Title: "{record_title}"
Previous Status: {old_status.upper()}
New Status: {new_status.upper()}

{f'Reason for Change: {reason}' if reason else ''}

{f'Resolution Details: {resolution_notes}' if resolution_notes else ''}

You can view your full report details in your Jiseti dashboard.

Thank you for using Jiseti!

Best regards,
The Jiseti Admin Team"""

    # Send email
    email_sent = send_status_email(user_email, email_subject, email_body)
    
    # Send SMS if phone number provided
    sms_sent = False
    if phone_number:
        sms_message = f"Jiseti Update: Your report '{record_title}' is now {new_status.upper()}. {reason if reason else ''} Check email for details."
        sms_sent = send_sms_notification(phone_number, sms_message)
    
    return {
        'email_sent': email_sent,
        'sms_sent': sms_sent,
        'phone_provided': bool(phone_number)
    }

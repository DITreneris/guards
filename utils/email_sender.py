import os
import logging
import smtplib
import secrets
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, app=None):
        self.app = app
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', 587))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.sender_email = os.environ.get('SENDER_EMAIL', 'noreply@guardsnrobbers.com')
        self.sender_name = os.environ.get('SENDER_NAME', 'Guards & Robbers')
        self.base_url = os.environ.get('BASE_URL', 'https://guardsnrobbers.com')
        
        # Setup Jinja2 environment for email templates
        self.env = Environment(
            loader=FileSystemLoader('templates/email_templates'),
            autoescape=True
        )
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        # Setup any app-specific configuration
        if app.config.get('SMTP_SERVER'):
            self.smtp_server = app.config['SMTP_SERVER']
        if app.config.get('SMTP_PORT'):
            self.smtp_port = int(app.config['SMTP_PORT'])
        if app.config.get('SMTP_USERNAME'):
            self.smtp_username = app.config['SMTP_USERNAME']
        if app.config.get('SMTP_PASSWORD'):
            self.smtp_password = app.config['SMTP_PASSWORD']
        if app.config.get('SENDER_EMAIL'):
            self.sender_email = app.config['SENDER_EMAIL']
        if app.config.get('SENDER_NAME'):
            self.sender_name = app.config['SENDER_NAME']
        if app.config.get('BASE_URL'):
            self.base_url = app.config['BASE_URL']
    
    def _create_message(self, to_email, subject, html_content, to_name=None):
        """Create a multipart email message"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        
        if to_name:
            msg['To'] = f"{to_name} <{to_email}>"
        else:
            msg['To'] = to_email
            
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        return msg
    
    def send_email(self, to_email, subject, html_content, to_name=None):
        """Send an email using SMTP"""
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        msg = self._create_message(to_email, subject, html_content, to_name)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def generate_confirmation_token(self, email):
        """Generate a unique token for email confirmation"""
        # Create a random token
        token = secrets.token_urlsafe(32)
        # Add timestamp to prevent token reuse
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # Create a hash that includes the email
        data = f"{email}:{token}:{timestamp}"
        
        # Create a hash that can be used to validate the token
        h = hashlib.sha256()
        h.update(data.encode('utf-8'))
        
        return f"{h.hexdigest()}:{timestamp}"
    
    def send_welcome_email(self, to_email, to_name, company_name):
        """Send welcome email to new subscribers with confirmation link"""
        try:
            # Generate confirmation token
            token = self.generate_confirmation_token(to_email)
            
            # Create confirmation link
            confirmation_link = f"{self.base_url}/confirm-subscription?email={to_email}&token={token}"
            unsubscribe_link = f"{self.base_url}/unsubscribe?email={to_email}&token={token}"
            
            # Load template
            template = self.env.get_template('welcome_email.html')
            
            # Render template with context
            html_content = template.render(
                name=to_name,
                confirmation_link=confirmation_link,
                unsubscribe_link=unsubscribe_link
            )
            
            # Send email
            subject = "Welcome to Guards & Robbers Newsletter - Please Confirm Subscription"
            return self.send_email(to_email, subject, html_content, to_name)
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
    
    def send_newsletter(self, to_email, to_name, template_name, context):
        """Send newsletter to subscriber"""
        try:
            # Generate unsubscribe token
            token = self.generate_confirmation_token(to_email)
            
            # Create unsubscribe link
            unsubscribe_link = f"{self.base_url}/unsubscribe?email={to_email}&token={token}"
            
            # Add unsubscribe link to context
            context['unsubscribe_link'] = unsubscribe_link
            
            # Load template
            template = self.env.get_template(template_name)
            
            # Render template with context
            html_content = template.render(**context)
            
            # Send email
            subject = context.get('newsletter_title', 'Guards & Robbers Newsletter')
            return self.send_email(to_email, subject, html_content, to_name)
            
        except Exception as e:
            logger.error(f"Failed to send newsletter: {e}")
            return False

# Instantiate a default email sender
email_sender = EmailSender()

# Helper functions for common email tasks
def send_welcome_email(to_email, to_name, company_name):
    """Send welcome email to new subscriber"""
    return email_sender.send_welcome_email(to_email, to_name, company_name)

def send_newsletter(to_email, to_name, template_name, context):
    """Send newsletter to subscriber"""
    return email_sender.send_newsletter(to_email, to_name, template_name, context) 
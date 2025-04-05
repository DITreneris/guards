import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Set environment variables
os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
os.environ['SMTP_PORT'] = '587'
os.environ['SMTP_USERNAME'] = 'guardsbot66@gmail.com'
os.environ['SMTP_PASSWORD'] = 'tygh ospm rshu mzet'

def test_email_sending():
    # Email configuration
    sender_email = "info@guardsandrobbers.com"
    receiver_email = "guardsbot66@gmail.com"
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = f"Email System Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # Add body
    body = """
    This is a test email to verify:
    1. Email sending from info@guardsandrobbers.com
    2. Email forwarding to guardsbot66@gmail.com
    3. SMTP configuration
    4. DNS records (MX, SPF, DKIM)

    If you receive this email, the basic email infrastructure is working correctly.
    """
    message.attach(MIMEText(body, "plain"))

    try:
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Send email
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("✅ Test email sent successfully!")
        
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        return False

if __name__ == "__main__":
    test_email_sending() 
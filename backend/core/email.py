import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
from typing import List, Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.host = settings.EMAIL_HOST
        self.port = settings.EMAIL_PORT
        self.user = settings.EMAIL_USER
        # Gmail App Passwords are often copied with spaces (e.g. "abcd efgh ijkl mnop").
        # SMTP auth expects the raw value, so normalize it here.
        self.password = (settings.EMAIL_PASSWORD or "").replace(" ", "")
        # If EMAIL_FROM isn't set or is left as the default, fall back to the SMTP user.
        self.sender = settings.EMAIL_FROM or (self.user or "noreply@homeguard.local")
        self.enabled = settings.EMAIL_ENABLED

    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send an email to a recipient
        """
        if not self.enabled or not self.user or not self.password:
            logger.warning("Email service is disabled or not configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = to_email

            # Attach plain text body
            msg.attach(MIMEText(body, "plain"))

            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            # Connect to SMTP server
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.sender, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            print(f"✅ Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False

    def send_alert_email(self, to_email: str, alert_data: dict) -> bool:
        """
        Send a formatted security alert email
        """
        subject = f"🚨 HomeGuard Alert: {alert_data.get('reason', 'Security Alert')}"
        
        # Plain text version
        body = f"""
        HOMEGUARD SECURITY ALERT
        
        Severity: {alert_data.get('severity', 'UNKNOWN').upper()}
        Reason: {alert_data.get('reason')}
        Device: {alert_data.get('device_name') or alert_data.get('device_ip')}
        Time: {alert_data.get('timestamp')}
        
        Please check your dashboard for more details.
        """
        
        # HTML version
        severity_color = {
            "critical": "#ef4444",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#3b82f6"
        }.get(alert_data.get('severity', 'medium').lower(), "#6b7280")
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                <div style="background-color: {severity_color}; padding: 20px; text-align: center; color: white;">
                    <h1 style="margin: 0;">Security Alert</h1>
                </div>
                <div style="padding: 24px;">
                    <h2 style="margin-top: 0; color: #1f2937;">{alert_data.get('reason')}</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">Severity:</td>
                            <td style="padding: 8px 0; font-weight: bold; text-transform: uppercase; color: {severity_color};">{alert_data.get('severity')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">Device:</td>
                            <td style="padding: 8px 0; font-weight: bold;">{alert_data.get('device_name') or alert_data.get('device_ip')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6b7280;">Time:</td>
                            <td style="padding: 8px 0;">{alert_data.get('timestamp')}</td>
                        </tr>
                    </table>
                    <div style="margin-top: 24px; text-align: center;">
                        <a href="{settings.FRONTEND_URL}" style="display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View Dashboard</a>
                    </div>
                </div>
                <div style="background-color: #f9fafb; padding: 16px; text-align: center; font-size: 12px; color: #6b7280;">
                    &copy; HomeGuard Security System
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)

email_service = EmailService()


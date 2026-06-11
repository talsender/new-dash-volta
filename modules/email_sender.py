# modules/email_sender.py
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass
from typing import Optional


@dataclass
class SendResult:
    success: bool
    error: Optional[str] = None


def send_email(smtp_config: dict, smtp_password: str, to: list,
               subject: str, html_body: str,
               attachment_path: Optional[str] = None) -> SendResult:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_config['from_email']
    msg['To'] = ', '.join(to)
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    if attachment_path:
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        f'attachment; filename="{os.path.basename(attachment_path)}"')
        msg.attach(part)
    try:
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as srv:
            srv.starttls()
            srv.login(smtp_config['username'], smtp_password)
            srv.sendmail(smtp_config['from_email'], to, msg.as_string())
        return SendResult(success=True)
    except Exception as e:
        return SendResult(success=False, error=str(e))

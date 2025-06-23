
from pathlib import Path
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
from loguru import logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_PATH = Path("/secrets/token.json")
CREDS_PATH = Path("/secrets/credentials.json")

def get_gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with TOKEN_PATH.open("w") as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_pdf_via_email(pdf_path: Path, to_email: str, subject: str = "CSV Summary PDF"):
    logger.info(f"📧 Preparing to send email with attachment: {pdf_path}")
    service = get_gmail_service()
    message = MIMEMultipart()
    message['to'] = to_email
    message['subject'] = subject
    message.attach(MIMEText("Attached is your processed CSV summary."))
    with pdf_path.open("rb") as f:
        part = MIMEApplication(f.read(), Name=pdf_path.name)
        part['Content-Disposition'] = f'attachment; filename="{pdf_path.name}"'
        message.attach(part)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
    logger.success(f"✅ Email sent: {result.get('id')}")

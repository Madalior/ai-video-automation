"""
Gmail Verification Tools
Handles Gmail API integration for email verification, account creation, and automation
"""

import os
import base64
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import re

class GmailVerificationTool:
    """
    Gmail API tool for email verification and automation
    """
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, credentials_path='credentials.json'):
        self.credentials_path = credentials_path
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Token file stores user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail authenticated successfully!")
    
    def send_verification_email(self, to_email, verification_code):
        """Send verification email with code"""
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = 'AI Video Studio - Email Verification'
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 30px; border-radius: 10px;">
                <h1 style="color: #8a5aff;">AI Video Studio</h1>
                <h2>Email Verification</h2>
                <p>Your verification code is:</p>
                <div style="background: white; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #8a5aff; letter-spacing: 5px; font-size: 36px;">{verification_code}</h1>
                </div>
                <p>This code will expire in 10 minutes.</p>
                <p style="color: #666; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        
        message.attach(MIMEText(body, 'html'))
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {'raw': raw}
        
        try:
            sent = self.service.users().messages().send(
                userId='me', body=send_message).execute()
            print(f"✅ Verification email sent to {to_email}")
            return sent
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return None
    
    def check_inbox_for_verification(self, sender_filter=None, subject_filter=None, timeout=300):
        """
        Monitor inbox for verification emails
        Returns: verification code if found
        """
        print(f"👁️ Monitoring inbox for verification email...")
        start_time = time.time()
        
        query = []
        if sender_filter:
            query.append(f"from:{sender_filter}")
        if subject_filter:
            query.append(f"subject:{subject_filter}")
        query.append("is:unread")
        
        query_string = " ".join(query)
        
        while time.time() - start_time < timeout:
            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query_string,
                    maxResults=1
                ).execute()
                
                messages = results.get('messages', [])
                
                if messages:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=messages[0]['id'],
                        format='full'
                    ).execute()
                    
                    # Extract verification code
                    code = self.extract_verification_code(msg)
                    
                    if code:
                        # Mark as read
                        self.service.users().messages().modify(
                            userId='me',
                            id=messages[0]['id'],
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        
                        print(f"✅ Verification code found: {code}")
                        return code
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error checking inbox: {e}")
                time.sleep(5)
        
        print("⏱️ Timeout: No verification email found")
        return None
    
    def extract_verification_code(self, message):
        """Extract verification code from email message"""
        # Get message body
        if 'payload' in message:
            parts = message['payload'].get('parts', [])
            
            if not parts:
                # Single part message
                body_data = message['payload']['body'].get('data', '')
            else:
                # Multi-part message
                for part in parts:
                    if part['mimeType'] == 'text/plain' or part['mimeType'] == 'text/html':
                        body_data = part['body'].get('data', '')
                        break
            
            # Decode body
            if body_data:
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                
                # Common verification code patterns
                patterns = [
                    r'(?:code|verification code|otp)[\s:]+([A-Z0-9]{4,8})',  # CODE: ABC123
                    r'([A-Z0-9]{6})',  # 6-digit code
                    r'(\d{4,8})',  # Numeric code
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, body, re.IGNORECASE)
                    if match:
                        return match.group(1)
        
        return None
    
    def create_filter_for_verification(self, sender_email):
        """Create Gmail filter to automatically label verification emails"""
        filter_criteria = {
            'criteria': {
                'from': sender_email,
                'hasAttachment': False
            },
            'action': {
                'addLabelIds': ['CATEGORY_UPDATES'],
                'removeLabelIds': ['INBOX']
            }
        }
        
        try:
            result = self.service.users().settings().filters().create(
                userId='me',
                body=filter_criteria
            ).execute()
            print(f"✅ Filter created for {sender_email}")
            return result
        except Exception as e:
            print(f"Error creating filter: {e}")
            return None
    
    def get_recent_emails(self, max_results=10, query=""):
        """Get recent emails from inbox"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = message['payload']['headers']
                email_data = {
                    'id': msg['id'],
                    'from': next((h['value'] for h in headers if h['name'] == 'From'), ''),
                    'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), ''),
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), '')
                }
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error getting emails: {e}")
            return []
    
    def delete_old_verification_emails(self, days=7):
        """Delete verification emails older than specified days"""
        import datetime
        
        # Calculate date string
        date = datetime.datetime.now() - datetime.timedelta(days=days)
        date_str = date.strftime('%Y/%m/%d')
        
        query = f'subject:(verification OR verify OR code) before:{date_str}'
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            for msg in messages:
                self.service.users().messages().delete(
                    userId='me',
                    id=msg['id']
                ).execute()
            
            print(f"✅ Deleted {len(messages)} old verification emails")
            return len(messages)
            
        except Exception as e:
            print(f"Error deleting emails: {e}")
            return 0


# Usage Examples
if __name__ == "__main__":
    # Initialize Gmail tool
    gmail = GmailVerificationTool()
    
    # Example 1: Send verification email
    gmail.send_verification_email(
        to_email="user@example.com",
        verification_code="ABC123"
    )
    
    # Example 2: Monitor inbox for verification from specific sender
    code = gmail.check_inbox_for_verification(
        sender_filter="noreply@dreamina.com",
        subject_filter="verification",
        timeout=300  # 5 minutes
    )
    
    if code:
        print(f"Received code: {code}")
    
    # Example 3: Get recent emails
    emails = gmail.get_recent_emails(max_results=5)
    for email in emails:
        print(f"From: {email['from']}, Subject: {email['subject']}")
    
    # Example 4: Clean up old verification emails
    gmail.delete_old_verification_emails(days=7)

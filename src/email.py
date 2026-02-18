#!/usr/bin/env python3
"""
Gmail Email Client
Simple class for sending and receiving emails using Gmail SMTP/IMAP
"""

import smtplib
import imaplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional


class GmailClient:
    def __init__(self, email_address: str, app_password: str):
        """
        Initialize Gmail client
        
        Args:
            email_address: Your Gmail address
            app_password: Gmail App Password (not your regular password)
                         Generate at: https://myaccount.google.com/apppasswords
        """
        self.email_address = email_address
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        
        print(f"📧 Gmail Client initialized for: {self.email_address}")

    def send_email(self, to_email: str, subject: str, body: str, 
                   attachments: Optional[List[str]] = None, 
                   is_html: bool = False) -> bool:
        """
        Send an email via Gmail SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            attachments: List of file paths to attach (optional)
            is_html: Whether the body is HTML formatted
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            print(f"📤 Sending email to: {to_email}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
                    else:
                        print(f"⚠️  Attachment not found: {file_path}")
            
            # Connect to server and send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable encryption
            server.login(self.email_address, self.app_password)
            
            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add file attachment to email message"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            print(f"📎 Added attachment: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to add attachment {file_path}: {e}")

    def check_emails(self, mailbox: str = "INBOX", limit: int = 10, 
                     unread_only: bool = True) -> List[Dict]:
        """
        Check for received emails
        
        Args:
            mailbox: Gmail folder to check (default: "INBOX")
            limit: Maximum number of emails to retrieve
            unread_only: Only retrieve unread emails
            
        Returns:
            List[Dict]: List of email dictionaries with keys:
                       'subject', 'from', 'date', 'body', 'uid'
        """
        emails = []
        
        try:
            print(f"📥 Checking {mailbox} for emails...")
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.app_password)
            mail.select(mailbox)
            
            # Search for emails
            search_criteria = "UNSEEN" if unread_only else "ALL"
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                print(f"❌ Failed to search emails: {status}")
                return emails
            
            # Get message IDs
            message_ids = messages[0].split()
            
            if not message_ids:
                print("📭 No emails found")
                mail.close()
                mail.logout()
                return emails
            
            # Get recent emails (limit)
            recent_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
            
            print(f"🔍 Processing {len(recent_ids)} emails...")
            
            for msg_id in recent_ids:
                try:
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                        
                    # Parse email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract email info
                    email_info = {
                        'uid': msg_id.decode(),
                        'subject': email_message.get('Subject', 'No Subject'),
                        'from': email_message.get('From', 'Unknown Sender'),
                        'date': email_message.get('Date', 'No Date'),
                        'body': self._get_email_body(email_message)
                    }
                    
                    emails.append(email_info)
                    
                except Exception as e:
                    print(f"❌ Error processing email {msg_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
            print(f"✅ Retrieved {len(emails)} emails")
            return emails
            
        except Exception as e:
            print(f"❌ Failed to check emails: {e}")
            return emails

    def _get_email_body(self, email_message) -> str:
        """Extract body content from email message"""
        body = ""
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Skip attachments
                    if "attachment" not in content_disposition:
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                        elif content_type == "text/html" and not body:
                            body = part.get_payload(decode=True).decode()
            else:
                body = email_message.get_payload(decode=True).decode()
                
        except Exception as e:
            print(f"❌ Error extracting email body: {e}")
            body = "Could not extract email body"
            
        return body

    def mark_as_read(self, uid: str, mailbox: str = "INBOX") -> bool:
        """
        Mark an email as read
        
        Args:
            uid: Email UID from check_emails()
            mailbox: Mailbox containing the email
            
        Returns:
            bool: True if marked successfully, False otherwise
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.app_password)
            mail.select(mailbox)
            
            mail.store(uid, '+FLAGS', '\\Seen')
            
            mail.close()
            mail.logout()
            
            print(f"✅ Marked email {uid} as read")
            return True
            
        except Exception as e:
            print(f"❌ Failed to mark email as read: {e}")
            return False

    def get_unread_count(self, mailbox: str = "INBOX") -> int:
        """
        Get count of unread emails
        
        Args:
            mailbox: Mailbox to check
            
        Returns:
            int: Number of unread emails
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.app_password)
            mail.select(mailbox)
            
            status, messages = mail.search(None, "UNSEEN")
            
            if status == 'OK':
                count = len(messages[0].split()) if messages[0] else 0
            else:
                count = 0
                
            mail.close()
            mail.logout()
            
            print(f"📊 Unread emails in {mailbox}: {count}")
            return count
            
        except Exception as e:
            print(f"❌ Failed to get unread count: {e}")
            return 0


# Example usage
if __name__ == "__main__":
    # Example configuration - replace with your details
    EMAIL = "your.email@gmail.com"
    APP_PASSWORD = "your-app-password"  # Generate at https://myaccount.google.com/apppasswords
    
    # Initialize client
    gmail = GmailClient(EMAIL, APP_PASSWORD)
    
    # Send test email
    success = gmail.send_email(
        to_email="recipient@example.com",
        subject="Test Email from Python",
        body="This is a test email sent using Python!",
        is_html=False
    )
    
    if success:
        print("✅ Test email sent successfully!")
    
    # Check for new emails
    print("\n" + "="*50)
    new_emails = gmail.check_emails(limit=5, unread_only=True)
    
    for i, email_info in enumerate(new_emails, 1):
        print(f"\n📧 Email {i}:")
        print(f"  From: {email_info['from']}")
        print(f"  Subject: {email_info['subject']}")
        print(f"  Date: {email_info['date']}")
        print(f"  Body: {email_info['body'][:100]}...")  # First 100 chars
    
    # Get unread count
    unread_count = gmail.get_unread_count()
    print(f"\n📊 Total unread emails: {unread_count}")

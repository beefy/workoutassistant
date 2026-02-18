#!/usr/bin/env python3
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class GmailClient:
    def __init__(self, email_address, app_password):
        self.email = email_address
        self.password = app_password

    def send_email(self, to_email, subject, body, is_html=False):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email, self.password)
            server.sendmail(self.email, to_email, msg.as_string())
            server.quit()
            
            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Send failed: {e}")
            return False

    def check_emails(self, limit=10, unread_only=True):
        emails = []
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email, self.password)
            mail.select("INBOX")
            
            search_criteria = "UNSEEN" if unread_only else "ALL"
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK' or not messages[0]:
                mail.close()
                mail.logout()
                return emails
            
            message_ids = messages[0].split()
            recent_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
            
            for msg_id in recent_ids:
                try:
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                        
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Extract body
                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = email_message.get_payload(decode=True).decode()
                    
                    emails.append({
                        'uid': msg_id.decode(),
                        'subject': email_message.get('Subject', 'No Subject'),
                        'from': email_message.get('From', 'Unknown'),
                        'date': email_message.get('Date', 'No Date'),
                        'body': body or "Could not extract body"
                    })
                except Exception as e:
                    print(f"❌ Error processing email: {e}")
                    continue
            
            mail.close()
            mail.logout()
            print(f"✅ Retrieved {len(emails)} emails")
            
        except Exception as e:
            print(f"❌ Check emails failed: {e}")
            
        return emails

    def get_unread_count(self):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email, self.password)
            mail.select("INBOX")
            status, messages = mail.search(None, "UNSEEN")
            count = len(messages[0].split()) if status == 'OK' and messages[0] else 0
            mail.close()
            mail.logout()
            return count
        except Exception as e:
            print(f"❌ Count failed: {e}")
            return 0

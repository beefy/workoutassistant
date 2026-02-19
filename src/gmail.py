#!/usr/bin/env python3
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading
import time
from datetime import datetime
import psutil


class GmailClient:
    def __init__(self, email_address=None, app_password=None):
        if not email_address or not app_password:
            email_address = os.getenv("GMAIL_ADDRESS")
            app_password = os.getenv("GMAIL_APP_PASSWORD")

        if not email_address or not app_password:
            raise ValueError("Email address and app password are required")
        self.email = email_address
        self.password = app_password

    def send_email(self, to_email, subject, body, is_html=False):
        if not all([to_email, subject, body]):
            print("❌ Send failed: to_email, subject, and body are required")
            return False
            
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

    def schedule_email(self, to_email, subject, body, send_time, is_html=False):
        """Schedule an email to be sent at a future time"""
        if not all([to_email, subject, body, send_time]):
            print("❌ Schedule failed: to_email, subject, body, and send_time are required")
            return False
            
        try:
            # Parse send_time (expected format: "YYYY-MM-DD HH:MM")
            target_time = datetime.strptime(send_time, "%Y-%m-%d %H:%M")
            current_time = datetime.now()
            
            if target_time <= current_time:
                print("❌ Schedule failed: send_time must be in the future")
                return False
            
            delay = (target_time - current_time).total_seconds()
            
            print(f"📅 Email scheduled to send to {to_email} at {send_time}")
            
            # Start background thread to send email at scheduled time
            def delayed_send():
                time.sleep(delay)
                success = self.send_email(to_email, subject, body, is_html)
                if success:
                    print(f"📨 Scheduled email sent to {to_email}")
                else:
                    print(f"❌ Scheduled email failed to send to {to_email}")
            
            thread = threading.Thread(target=delayed_send, daemon=True)
            thread.start()
            
            return True
            
        except ValueError as e:
            print(f"❌ Schedule failed: Invalid time format. Use YYYY-MM-DD HH:MM. Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Schedule failed: {e}")
            return False

    def check_emails(self, limit=None, unread_only=True, mark_as_read=True):
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
            
            # Use unread count as default limit if not specified
            if limit is None:
                limit = len(message_ids)
            
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
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                                    break
                    else:
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                    
                    emails.append({
                        'uid': msg_id.decode(),
                        'subject': email_message.get('Subject', 'No Subject'),
                        'from': email_message.get('From', 'Unknown'),
                        'date': email_message.get('Date', 'No Date'),
                        'body': body or "Could not extract body"
                    })
                    
                    # Mark as read if requested
                    if mark_as_read and unread_only:
                        mail.store(msg_id, '+FLAGS', '\\Seen')
                        
                except Exception as e:
                    print(f"❌ Error processing email: {e}")
                    continue
            
            mail.close()
            mail.logout()
            print(f"✅ Retrieved {len(emails)} emails{' and marked as read' if mark_as_read and unread_only else ''}")
            
        except Exception as e:
            print(f"❌ Check emails failed: {e}")
            
        return emails

    def mark_as_read(self, uid):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email, self.password)
            mail.select("INBOX")
            mail.store(uid, '+FLAGS', '\\Seen')
            mail.close()
            mail.logout()
            print(f"✅ Marked email {uid} as read")
            return True
        except Exception as e:
            print(f"❌ Mark as read failed: {e}")
            return False

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


def get_system_info():
    """Get system information including date/time, CPU, memory usage"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get load averages (Unix/Linux only)
        try:
            load_avg = os.getloadavg()
            load_info = f"Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
        except:
            load_info = "Load Average: Not available"
        
        system_info = {
            "current_time": current_time,
            "cpu_usage_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 1),
            "load_average": load_info
        }
        
        formatted_info = f"""🕒 Current Time: {current_time}
💻 CPU Usage: {cpu_percent}%
🧠 Memory: {memory.percent}% used ({round(memory.used / (1024**3), 2)}GB / {round(memory.total / (1024**3), 2)}GB)
💾 Disk: {system_info['disk_percent']}% used ({system_info['disk_used_gb']}GB / {system_info['disk_total_gb']}GB)
⚡ {load_info}"""
        
        return formatted_info
        
    except Exception as e:
        return f"❌ Failed to get system info: {e}"

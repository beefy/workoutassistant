#!/usr/bin/env python3
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
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

    def send_email(self, to_email, subject, body, is_html=False, cc=None):
        if not all([to_email, subject, body]):
            print("❌ Send failed: to_email, subject, and body are required")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Handle CC addresses
            all_recipients = [to_email]
            if cc:
                if isinstance(cc, str):
                    cc_list = [cc]
                elif isinstance(cc, list):
                    cc_list = cc
                else:
                    cc_list = [str(cc)]
                
                msg['Cc'] = ', '.join(cc_list)
                all_recipients.extend(cc_list)
            
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email, self.password)
            server.sendmail(self.email, all_recipients, msg.as_string())
            server.quit()
            
            cc_info = f" (CC: {', '.join(cc_list)})" if cc else ""
            print(f"✅ Email sent to {to_email}{cc_info}")
            return True
        except Exception as e:
            print(f"❌ Send failed: {e}")
            return False

    def send_email_with_attachment(self, to_email, subject, body, file_path, is_html=False, cc=None):
        """Send an email with a file attachment
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body text
            file_path (str): Path to file to attach
            is_html (bool): Whether body is HTML format
            cc (str or list): CC recipient(s) - can be single email or list of emails
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not all([to_email, subject, body, file_path]):
            print("❌ Send failed: to_email, subject, body, and file_path are required")
            return False
        
        if not os.path.exists(file_path):
            print(f"❌ Send failed: File not found: {file_path}")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Handle CC addresses
            all_recipients = [to_email]
            if cc:
                if isinstance(cc, str):
                    cc_list = [cc]
                elif isinstance(cc, list):
                    cc_list = cc
                else:
                    cc_list = [str(cc)]
                
                msg['Cc'] = ', '.join(cc_list)
                all_recipients.extend(cc_list)
            
            # Add body text
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            # Add attachment
            filename = os.path.basename(file_path)
            
            # Guess the content type based on the file's extension
            content_type, encoding = mimetypes.guess_type(file_path)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            
            main_type, sub_type = content_type.split('/', 1)
            
            with open(file_path, 'rb') as fp:
                attachment = MIMEBase(main_type, sub_type)
                attachment.set_payload(fp.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(attachment)
            
            # Send email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email, self.password)
            server.sendmail(self.email, all_recipients, msg.as_string())
            server.quit()
            
            cc_info = f" (CC: {', '.join(cc_list)})" if cc else ""
            print(f"✅ Email with attachment sent to {to_email}{cc_info}")
            print(f"📎 Attached file: {filename} ({os.path.getsize(file_path)} bytes)")
            return True
            
        except Exception as e:
            print(f"❌ Send with attachment failed: {e}")
            return False

    def send_email_with_attachments(self, to_email, subject, body, file_paths, is_html=False, cc=None):
        """Send an email with multiple file attachments
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body text
            file_paths (list): List of file paths to attach
            is_html (bool): Whether body is HTML format
            cc (str or list): CC recipient(s) - can be single email or list of emails
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not all([to_email, subject, body, file_paths]):
            print("❌ Send failed: to_email, subject, body, and file_paths are required")
            return False
        
        # Convert single file path to list for compatibility
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        if not file_paths:
            print("❌ Send failed: At least one file path must be provided")
            return False
        
        # Check all files exist before proceeding
        missing_files = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Send failed: Files not found: {missing_files}")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Handle CC addresses
            all_recipients = [to_email]
            if cc:
                if isinstance(cc, str):
                    cc_list = [cc]
                elif isinstance(cc, list):
                    cc_list = cc
                else:
                    cc_list = [str(cc)]
                
                msg['Cc'] = ', '.join(cc_list)
                all_recipients.extend(cc_list)
            
            # Add body text
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            # Add all attachments
            total_size = 0
            attached_files = []
            
            for file_path in file_paths:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Check for reasonable size limit (25MB total for Gmail)
                if total_size > 25 * 1024 * 1024:
                    print(f"⚠️ Warning: Total attachment size ({total_size / (1024*1024):.1f}MB) exceeds Gmail limit")
                
                # Guess the content type based on the file's extension
                content_type, encoding = mimetypes.guess_type(file_path)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                
                main_type, sub_type = content_type.split('/', 1)
                
                with open(file_path, 'rb') as fp:
                    attachment = MIMEBase(main_type, sub_type)
                    attachment.set_payload(fp.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    msg.attach(attachment)
                
                attached_files.append(f"{filename} ({file_size} bytes)")
            
            # Send email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.email, self.password)
            server.sendmail(self.email, all_recipients, msg.as_string())
            server.quit()
            
            cc_info = f" (CC: {', '.join(cc_list)})" if cc else ""
            print(f"✅ Email with {len(file_paths)} attachments sent to {to_email}{cc_info}")
            print(f"📎 Attached files:")
            for file_info in attached_files:
                print(f"   • {file_info}")
            print(f"📊 Total size: {total_size / 1024:.1f} KB")
            return True
            
        except Exception as e:
            print(f"❌ Send with attachments failed: {e}")
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
                    
                    # Extract body and attachments
                    body = ""
                    attachments = []
                    
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition", ""))
                            
                            # Extract text body
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                payload = part.get_payload(decode=True)
                                if payload and not body:  # Use first text part found
                                    body = payload.decode('utf-8', errors='ignore')
                            
                            # Extract JPG/PNG attachments
                            elif "attachment" in content_disposition and content_type in ["image/jpeg", "image/jpg", "image/png"]:
                                filename = part.get_filename()
                                if filename:
                                    # Create attachments directory if it doesn't exist
                                    attachments_dir = os.path.join(os.path.dirname(__file__), '..', 'email_attachments')
                                    os.makedirs(attachments_dir, exist_ok=True)
                                    
                                    # Generate unique filename with timestamp
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    file_ext = os.path.splitext(filename)[1].lower()
                                    safe_filename = f"{timestamp}_{filename}"
                                    file_path = os.path.join(attachments_dir, safe_filename)
                                    
                                    try:
                                        # Save attachment to file
                                        with open(file_path, 'wb') as f:
                                            f.write(part.get_payload(decode=True))
                                        attachments.append(file_path)
                                        print(f"💾 Saved attachment: {safe_filename}")
                                    except Exception as attach_error:
                                        print(f"❌ Failed to save attachment {filename}: {attach_error}")
                    else:
                        # Single part message
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                    
                    emails.append({
                        'uid': msg_id.decode(),
                        'subject': email_message.get('Subject', 'No Subject'),
                        'from': email_message.get('From', 'Unknown'),
                        'cc': email_message.get('Cc', ''),
                        'date': email_message.get('Date', 'No Date'),
                        'body': body or "Could not extract body",
                        'attachments': attachments
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

    def email_to_admin(self, subject, body=None, file_path=None, file_paths=None, is_html=False):
        """Send email to admin (uses GMAIL_ADDRESS as both sender and recipient)
        
        Args:
            subject (str): Email subject
            body (str, optional): Email body. If None, uses system info
            file_path (str, optional): Single file path to attach (for compatibility)
            file_paths (list, optional): Multiple file paths to attach
            is_html (bool): Whether body is HTML format
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        admin_email = self.email  # Send to self (admin)
        
        # Use system info as default body if none provided
        if body is None:
            body = get_system_info()
        
        try:
            # Handle both single and multiple file attachments
            if file_paths or file_path:
                # Combine file_path and file_paths if both provided
                all_files = []
                if file_path:
                    all_files.append(file_path)
                if file_paths:
                    if isinstance(file_paths, list):
                        all_files.extend(file_paths)
                    else:
                        all_files.append(file_paths)
                
                success = self.send_email_with_attachments(
                    admin_email, subject, body, all_files, is_html
                )
            else:
                success = self.send_email(admin_email, subject, body, is_html)
            
            if success:
                print(f"📧 Admin notification sent: {subject}")
            return success
            
        except Exception as e:
            print(f"❌ Admin email failed: {e}")
            return False


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
        
        print("✅ System info retrieved")
        print(formatted_info)
        
        return formatted_info
        
    except Exception as e:
        return f"❌ Failed to get system info: {e}"

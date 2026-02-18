from gmail import GmailClient
import os

email_address = os.getenv("GMAIL_ADDRESS")
app_password = os.getenv("GMAIL_APP_PASSWORD")
test_email = os.getenv("TEST_EMAIL")
print(f"Sending test email from {email_address} to {test_email}")

gmail = GmailClient(email_address, app_password)

# Send email
gmail.send_email(test_email, "Test", "Hello World!")

# Check emails
new_emails = gmail.check_emails(limit=5)
for i, email_info in enumerate(new_emails, 1):
    print(f"Email {i}: {email_info['subject']} from {email_info['from']}")

# Get unread count
print(f"Unread emails: {gmail.get_unread_count()}")

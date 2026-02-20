from gmail import GmailClient
import os

test_email = os.getenv("TEST_EMAIL")

# get command line arg of file to attach
import sys
if len(sys.argv) < 2:
    print("Usage: python test_email_file.py <file_path>")
    sys.exit(1)

file_path = sys.argv[1]
if not os.path.isfile(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

client = GmailClient()
client.send_email_with_attachment(test_email, "Test Email with Attachment", "Please see the attached file.", file_path=file_path)
print(f"Sent email with attachment: {file_path}")

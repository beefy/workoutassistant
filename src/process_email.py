from gmail import GmailClient
from local_llm import LocalLLM
from approve_list import is_email_approved, add_to_approve_list
import os
from email_reply_parser import EmailReplyParser

def parse_email_body(body):
    """
    # TODO: reply history parsing??
    Parse email body to separate the most recent email from the email chain history.
    
    Args:
        body (str): The full email body including quoted replies
        
    Returns:
        dict: {
            "body": str,  # Most recent message
            "history": [   # Previous messages in reverse chronological order (oldest first)
                {
                    "sender": str,  # Sender name/email
                    "body": str     # Message content
                }
            ]
        }
    """
    if not body or not body.strip():
        return {"body": "", "history": []}
    
    try:
        # Use email-reply-parser to extract the new content
        new_content = EmailReplyParser.parse_reply(body)
        return {
            "body": new_content.strip() if new_content else "",
            "history": []  # email-reply-parser focuses on new content extraction, not history parsing
        }
    except Exception as e:
        print(f"⚠️ Email parsing failed: {e}")
        # Fallback: use entire body
        return {
            "body": body.strip(),
            "history": []
        }

def process_email():
    gmail = GmailClient()
    llm = LocalLLM()

    # Collect new emails
    new_emails = gmail.check_emails()
    for email_info in new_emails:
        sender = email_info['from'].replace("<", "").replace(">", "")
        senders_email = sender.split()[-1] if " " in sender else sender
        subject = email_info['subject']
        body = email_info['body']
        llm.attachments = email_info.get('attachments', [])  # Pass attachments
        parsed_body = parse_email_body(body)
        print(parsed_body["body"])
        exit()

        print(f"Processing email from {sender} with subject '{subject}'")

        if is_email_approved(senders_email):
            print(f"✅ {sender} is approved. Processing email...")
        elif os.getenv("APPROVED_PHRASE").lower() in body.lower():
            print(f"✅ {sender} is a friend of Nate. Adding to approve list...")
            add_to_approve_list(senders_email)
        else:
            print(f"❌ {sender} is not approved. Ignoring email.")
            continue

        if os.getenv("GMAIL_ADDRESS").replace(".", "") in senders_email.replace(".", ""):
            continue  # Skip processing emails from the bot to itself

        # Generate response using LLM
        prompt = f"{subject}\n{body}"
        response = llm.prompt(prompt)
        print(f"Generated response: {response}")
        print(f"Generated images in this session: {llm.generated_images}")

        # Send response email
        if llm.generated_images:
            print(f"📧 Sending email with attachments to {senders_email}")
            gmail.send_email_with_attachments(senders_email, f"Re: {subject}", response, llm.generated_images)
        else:
            print(f"📧 Sending email to {senders_email}")
            gmail.send_email(senders_email, f"Re: {subject}", response)

        print(f"📧 Completed processing email from {sender}: {subject}")
        llm.generated_images = []  # Clear generated images for next email
        llm.tool_call_memo = set()  # Clear tool call memo for next email
        llm.attachments = []  # Clear attachments for next email


if __name__ == "__main__":
    process_email()

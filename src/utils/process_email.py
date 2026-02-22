from clients.gmail import GmailClient
from llm.priority_queue import submit_llm_request
from utils.approve_list import is_email_approved, add_to_approve_list, remove_from_approve_list
from utils.tracking_api import status_update, system_info_update, response_time_update, login, unsubscribe_user
import datetime
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
    generated_images = []  # Track generated images for this session

    # Collect new emails
    new_emails = gmail.check_emails()
    email_received_time = datetime.datetime.now(datetime.UTC).isoformat()
    for email_info in new_emails:
        sender = email_info['from'].replace("<", "").replace(">", "")
        senders_email = sender.split()[-1] if " " in sender else sender
        subject = email_info['subject']
        body = email_info['body']
        attachments = email_info.get('attachments', [])  # Get attachments
        parsed_body = parse_email_body(body)
        body = parsed_body["body"]
        cc = email_info.get('cc', '')
        if not cc:
            cc = []

        print(f"Processing email from {sender} with subject '{subject}'")

        if is_email_approved(senders_email):
            print(f"✅ {sender} is approved. Processing email...")
        elif os.getenv("APPROVED_PHRASE").lower() in body.lower():
            print(f"✅ {sender} is a friend of Nate. Adding to approve list...")
            add_to_approve_list(senders_email)
        else:
            print(f"❌ {sender} is not approved. Ignoring email.")
            continue

        if "UNSUBSCRIBE" in body:
            print(f"📩 {sender} requested to unsubscribe. Removing from approve list...")
            
            remove_from_approve_list(senders_email)
            token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
            if token:
                unsubscribe_user(token, senders_email)

            gmail.send_email(senders_email, f"Re: {subject}", "You have been unsubscribed.")

        if os.getenv("GMAIL_ADDRESS").replace(".", "").lower() in senders_email.replace(".", "").lower():
            continue  # Skip processing emails from the bot to itself

        # Generate response using LLM Priority Queue (priority 1 for emails = high priority)
        prompt = f"{subject}\n{body}"
        
        response = submit_llm_request(
            prompt=prompt,
            attachments=attachments,
            priority=1  # High priority for emails
        )
        print(f"Email response generated: {response}")
        
        print(f"Generated response: {response}")
        
        # Note: generated_images functionality would need to be handled differently
        # since we don't have direct access to the LLM instance anymore
        # For now, assuming no image generation in emails
        
        # Send response email
        print(f"📧 Sending email to {senders_email}")
        gmail.send_email(senders_email, f"Re: {subject}", response, cc=cc)

        print(f"📧 Completed processing email from {sender}: {subject}")

        email_sent_time = datetime.datetime.now(datetime.UTC).isoformat()
        token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if token:
            status_update(token, f"Processed email")
            response_time_update(token, email_received_time, email_sent_time)

if __name__ == "__main__":
    process_email()

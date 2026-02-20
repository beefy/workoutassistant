from gmail import GmailClient
from local_llm import LocalLLM
from approve_list import is_email_approved, add_to_approve_list
import os

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

        print(f"Processing email from {sender} with subject '{subject}'")

        if is_email_approved(senders_email):
            print(f"✅ {sender} is approved. Processing email...")
        elif os.getenv("APPROVED_PHRASE").lower() in body.lower():
            print(f"✅ {sender} is a friend of Nate. Adding to approve list...")
            add_to_approve_list(senders_email)
        else:
            print(f"❌ {sender} is not approved. Ignoring email.")
            continue

        # Generate response using LLM
        prompt = f"{sender} says 'Re: {subject}:\n{body}'"
        response = llm.prompt(prompt)
        print(f"Generated response: {response}")
        print(f"Generated images in this session: {llm.generated_images}")

        # Send response email
        if llm.generated_images:
            print(f"📧 Sending email with attachments to {senders_email}")
            gmail.send_email_with_attachments(senders_email, subject, response, llm.generated_images)
        else:
            print(f"📧 Sending email to {senders_email}")
            gmail.send_email(senders_email, subject, response)

        print(f"📧 Completed processing email from {sender}: {subject}")
        llm.generated_images = []  # Clear generated images for next email


if __name__ == "__main__":
    process_email()

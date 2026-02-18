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
        prompt = f"Email from {sender} with subject '{subject}' and body:\n{body}"
        response = llm.prompt(prompt)
        print(f"Generated response: {response}")

        # Send response email
        gmail.send_email(senders_email, f"Re: {subject}", response)

        print(f"📧 Completed processing email from {sender}: {subject}")


if __name__ == "__main__":
    process_email()

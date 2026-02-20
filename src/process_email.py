from gmail import GmailClient
from local_llm import LocalLLM
from approve_list import is_email_approved, add_to_approve_list
import os

def parse_email_body(body):
    """
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
    import re
    
    if not body or not body.strip():
        return {"body": "", "history": []}
    
    # Split email into lines for processing
    lines = body.split('\n')
    
    # More robust pattern to match "On ... wrote:" lines
    # Handles: "On Fri, Feb 20, 2026 at 2:31 PM Bob <email> wrote:"
    wrote_pattern = r'^On\s+.+?\s+wrote:\s*$'
    
    current_message_lines = []
    all_sections = []
    
    # First pass: split into sections based on "On ... wrote:" pattern
    current_section = []
    current_sender = None
    
    for line in lines:
        stripped = line.strip()
        
        # Check if this is an "On ... wrote:" line
        if re.match(wrote_pattern, stripped):
            # Save previous section if it exists
            if current_section:
                all_sections.append({
                    "sender": current_sender,
                    "lines": current_section.copy()
                })
            
            # Extract sender from this line
            # Pattern: "On Date at Time Sender wrote:"
            sender_match = re.search(r'On\s+.+?\s+(.+?)\s+wrote:\s*$', stripped)
            if sender_match:
                current_sender = sender_match.group(1).strip()
            else:
                current_sender = "Unknown"
            
            current_section = []
        else:
            current_section.append(line)
    
    # Add the last section
    if current_section:
        all_sections.append({
            "sender": current_sender,
            "lines": current_section.copy()
        })
    
    # Process sections
    if not all_sections:
        # No quoted content found, entire body is new message
        return {"body": body.strip(), "history": []}
    
    # First section is the new message
    current_body = '\n'.join(all_sections[0]["lines"]).strip()
    
    # Process quoted sections
    history_messages = []
    
    for section in all_sections[1:]:
        if section["sender"]:
            # Clean quoted content by removing quote prefixes
            cleaned_lines = []
            for line in section["lines"]:
                # Remove quote prefixes (>, >>, etc.)
                cleaned_line = line
                while cleaned_line.startswith('>'):
                    cleaned_line = cleaned_line[1:].strip()
                
                # Skip empty lines and nested "On ... wrote:" lines
                if cleaned_line and not re.match(wrote_pattern, cleaned_line):
                    cleaned_lines.append(cleaned_line)
                elif not cleaned_line and cleaned_lines:  # Preserve internal empty lines
                    cleaned_lines.append("")
            
            # Join and clean the message body
            quoted_body = '\n'.join(cleaned_lines).strip()
            
            # Remove any remaining nested "On ... wrote:" content
            lines_to_keep = []
            skip_rest = False
            for line in quoted_body.split('\n'):
                if re.match(wrote_pattern, line.strip()):
                    skip_rest = True
                    break
                if not skip_rest:
                    lines_to_keep.append(line)
            
            final_body = '\n'.join(lines_to_keep).strip()
            
            if final_body:
                history_messages.append({
                    "sender": section["sender"],
                    "body": final_body
                })
    
    # Reverse history to put oldest first
    history_messages.reverse()
    
    return {
        "body": current_body,
        "history": history_messages
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

        print(parsed_body)
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

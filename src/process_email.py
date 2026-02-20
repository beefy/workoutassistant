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
    
    # Find the pattern "On ... wrote:" which indicates start of quoted content
    wrote_pattern = r'^On .+? wrote:$'
    
    current_message_lines = []
    history_messages = []
    current_section = "new"  # "new", "parsing_quote"
    current_quote_level = 0
    current_quoted_lines = []
    current_sender = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line matches the "On ... wrote:" pattern
        if re.match(wrote_pattern, line.strip()):
            # Extract sender from the "On ... wrote:" line
            # Pattern: "On Date at Time Sender <email> wrote:"
            sender_match = re.search(r'On .+? (.+?) wrote:$', line.strip())
            if sender_match:
                current_sender = sender_match.group(1).strip()
            else:
                current_sender = "Unknown"
            
            current_section = "parsing_quote"
            current_quoted_lines = []
            current_quote_level = 0
            i += 1
            continue
        
        if current_section == "new":
            # We're still in the new message part
            current_message_lines.append(line)
        
        elif current_section == "parsing_quote":
            # We're parsing quoted content
            stripped_line = line.strip()
            
            # Count quote level (>, >>, >>>)
            quote_level = 0
            temp_line = stripped_line
            while temp_line.startswith('>'):
                quote_level += 1
                temp_line = temp_line[1:].strip()
            
            # If we hit a new "On ... wrote:" pattern, save current quote and start new one
            if re.match(wrote_pattern, temp_line):
                # Save current quoted message
                if current_quoted_lines:
                    quoted_body = '\n'.join(current_quoted_lines).strip()
                    if quoted_body:
                        history_messages.append({
                            "sender": current_sender,
                            "body": quoted_body
                        })
                
                # Extract new sender
                sender_match = re.search(r'On .+? (.+?) wrote:$', temp_line)
                if sender_match:
                    current_sender = sender_match.group(1).strip()
                else:
                    current_sender = "Unknown"
                
                current_quoted_lines = []
                current_quote_level = quote_level
                i += 1
                continue
            
            # Add content to current quoted message (remove quote prefixes)
            if temp_line:  # Only add non-empty lines
                current_quoted_lines.append(temp_line)
            elif current_quoted_lines:  # Preserve empty lines within message
                current_quoted_lines.append("")
        
        i += 1
    
    # Save any remaining quoted message
    if current_section == "parsing_quote" and current_quoted_lines:
        quoted_body = '\n'.join(current_quoted_lines).strip()
        if quoted_body:
            history_messages.append({
                "sender": current_sender,
                "body": quoted_body
            })
    
    # Clean up the current message
    current_body = '\n'.join(current_message_lines).strip()
    
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

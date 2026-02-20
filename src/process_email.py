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
    
    def extract_sender_from_wrote_line(line):
        """Extract sender from 'On ... wrote:' line"""
        # Pattern: "On Date at Time Sender wrote:"
        # Extract everything between the last "at" and "wrote:"
        match = re.search(r'On\s+.+?\s+at\s+.+?\s+(.+?)\s+wrote:\s*$', line.strip())
        if match:
            return match.group(1).strip()
        
        # Fallback: extract everything between last whitespace group and "wrote:"
        match = re.search(r'On\s+.+?\s+(.+?)\s+wrote:\s*$', line.strip())
        if match:
            return match.group(1).strip()
        
        return "Unknown"
    
    def parse_recursive(text, level=0):
        """Recursively parse email content to extract individual messages"""
        messages = []
        lines = text.split('\n')
        
        current_message_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Remove quote prefixes for this level
            working_line = line
            for _ in range(level):
                if working_line.startswith('>'):
                    working_line = working_line[1:].strip()
                else:
                    break
            
            # Check if this is an "On ... wrote:" line at our current level
            if re.match(r'^On\s+.+?\s+wrote:\s*$', working_line.strip()):
                # We found a quoted section at our level
                sender = extract_sender_from_wrote_line(working_line.strip())
                
                # Collect all lines for this quoted section
                quoted_section_lines = []
                i += 1
                
                while i < len(lines):
                    next_line = lines[i]
                    
                    # Check if this line belongs to our quote level
                    quote_prefix_count = 0
                    temp_line = next_line
                    while temp_line.startswith('>'):
                        quote_prefix_count += 1
                        temp_line = temp_line[1:]
                    
                    # If we hit a new "On ... wrote:" at the same level, stop
                    if quote_prefix_count == level + 1:
                        # Remove the quote prefix
                        clean_line = next_line
                        for _ in range(level + 1):
                            if clean_line.startswith('>'):
                                clean_line = clean_line[1:]
                        clean_line = clean_line.strip() if clean_line else ""
                        
                        # Check if this is another "On ... wrote:" line
                        if re.match(r'^On\s+.+?\s+wrote:\s*$', clean_line):
                            break
                        
                        quoted_section_lines.append(next_line)
                    elif quote_prefix_count > level + 1:
                        # Deeper nesting, include it
                        quoted_section_lines.append(next_line)
                    else:
                        # We've moved back to a higher level, stop
                        break
                    
                    i += 1
                
                # Process this quoted section
                if quoted_section_lines:
                    # Clean the quoted section by removing appropriate quote prefixes
                    cleaned_lines = []
                    for qline in quoted_section_lines:
                        clean_qline = qline
                        for _ in range(level + 1):
                            if clean_qline.startswith('>'):
                                clean_qline = clean_qline[1:]
                            else:
                                break
                        clean_qline = clean_qline.strip() if clean_qline else ""
                        cleaned_lines.append(clean_qline)
                    
                    quoted_text = '\n'.join(cleaned_lines).strip()
                    
                    # Parse this quoted section recursively
                    nested_messages = parse_recursive(quoted_text, level + 1)
                    
                    # Add this message and any nested ones
                    # First, extract the direct message (before any nested quotes)
                    direct_message_lines = []
                    for clean_line in cleaned_lines:
                        if re.match(r'^On\s+.+?\s+wrote:\s*$', clean_line.strip()):
                            break
                        direct_message_lines.append(clean_line)
                    
                    direct_message = '\n'.join(direct_message_lines).strip()
                    
                    if direct_message:
                        messages.append({
                            "sender": sender,
                            "body": direct_message
                        })
                    
                    # Add nested messages
                    messages.extend(nested_messages)
                
                continue
            else:
                # This line is part of the current message
                if level == 0:
                    current_message_lines.append(line)
                else:
                    # For quoted content, we already processed it above
                    current_message_lines.append(working_line)
                i += 1
        
        return messages
    
    # Split the email into the new message and quoted content
    lines = body.split('\n')
    new_message_lines = []
    remaining_content = []
    found_quote = False
    
    for i, line in enumerate(lines):
        if not found_quote and re.match(r'^On\s+.+?\s+wrote:\s*$', line.strip()):
            found_quote = True
            remaining_content = lines[i:]
            break
        else:
            new_message_lines.append(line)
    
    # Get the new message
    current_body = '\n'.join(new_message_lines).strip()
    
    # Parse the quoted content recursively
    history_messages = []
    if remaining_content:
        remaining_text = '\n'.join(remaining_content)
        history_messages = parse_recursive(remaining_text, 0)
    
    # Reverse to get oldest first
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

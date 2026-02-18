from approve_list import is_email_approved
import os

print(is_email_approved(os.getenv("ADMIN_EMAIL")))

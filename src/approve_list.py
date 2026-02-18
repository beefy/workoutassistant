from db import SQLiteClient

def get_approve_list():
    db = SQLiteClient()
    return db.select("approve_list")

def is_email_approved(email):
    db = SQLiteClient()
    result = db.select("approve_list", where="email = ?", params=(email,))
    return len(result) > 0

def add_to_approve_list(email):
    db = SQLiteClient()
    if is_email_approved(email):
        print(f"✅ {email} is already in the approve list")
        return True

    result = db.insert("approve_list", {"email": email})
    if result:
        print(f"✅ Added {email} to approve list")
    else:
        print(f"❌ Failed to add {email} to approve list")

    return result

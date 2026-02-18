from db import SQLiteClient

def get_approve_list():
    db = SQLiteClient()
    return db.fetch_all("approve_list", order_by="added_at DESC")

def is_email_approved(email):
    db = SQLiteClient()
    result = db.fetch_all("approve_list", where="email = ?", params=(email,))
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

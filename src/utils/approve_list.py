from clients.db import SQLiteClient
import logging
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

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
        logger.info(f"✅ {email} is already in the approve list")
        return True

    result = db.insert("approve_list", {"email": email})
    if result:
        logger.info(f"✅ Added {email} to approve list")
    else:
        logger.error(f"❌ Failed to add {email} to approve list")

    return result

def remove_from_approve_list(email):
    db = SQLiteClient()
    if not is_email_approved(email):
        logger.warning(f"⚠️ {email} is not in the approve list")
        return True

    result = db.execute_query("DELETE FROM approve_list WHERE email = ?", (email,))
    if result and result[0].get("affected_rows", 0) > 0:
        logger.info(f"✅ Removed {email} from approve list")
        return True
    else:
        logger.error(f"❌ Failed to remove {email} from approve list")
        return False

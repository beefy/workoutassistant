from db import SQLiteClient
import os


def approve_list():
    # Create approve list table
    db = SQLiteClient()
    db.create_table("approve_list", """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)

    # Populate with some initial data
    initial_emails = [
        {"email": os.getenv("ADMIN_EMAIL")}
    ]

    for entry in initial_emails:
        db.insert("approve_list", entry)


if __name__ == "__main__":
    approve_list()

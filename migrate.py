# Python Scriptt to migrate from JSON to SQLite 

import json
from database import init_db, add_user

USERS_JSON = "users.json"

def migrate():
    """Read users from JSON and insert into SQLite database."""
    init_db()
    with open(USERS_JSON, "r", encoding="utf-8") as f:
        users = json.load(f)
        for user in users:
            add_user(user["id"], user["username"])
    print(f"{len(users)} users migrated successfully to SQLite.")

if __name__ == "__main__":
    migrate()

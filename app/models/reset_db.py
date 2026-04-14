"""
reset_db.py — Run this ONE TIME to wipe the old broken database
and create fresh tables with the correct column names.

Run from your project root:
    python reset_db.py

After running this, start the app normally with:
    python run.py
"""

import os

# Delete the old database file so SQLite rebuilds from scratch
db_path = os.path.join(os.path.dirname(__file__), "resume_analyzer.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Deleted old database: {db_path}")
else:
    print("ℹ️  No existing database found — nothing to delete.")

# Recreate all tables with correct schema
from app import create_app
from app.models.database import db

app = create_app("development")
with app.app_context():
    db.create_all()
    print("✅ Fresh database created with correct schema.")
    print("✅ You can now run: python run.py")

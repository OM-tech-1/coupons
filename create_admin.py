#!/usr/bin/env python3
"""
Script to create or promote a user to ADMIN role.
Usage: python3 create_admin.py
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import get_password_hash


import os

def create_admin():
    db = SessionLocal()
    
    # Check for environment variables (Non-interactive mode)
    env_phone = os.getenv("ADMIN_PHONE")
    env_password = os.getenv("ADMIN_PASSWORD")
    env_name = os.getenv("ADMIN_NAME", "Admin User")
    
    if env_phone and env_password:
        phone_number = env_phone.strip()
        password = env_password.strip()
        full_name = env_name.strip()
        print(f"🔧 Running in non-interactive mode for {phone_number}...")
    else:
        # Interactive mode
        print("🔧 Running in interactive mode (env vars not set)...")
        phone_number = input("Enter phone number (e.g. +971501234567): ").strip()
        password = None  # Will ask if needed
        full_name = None

    # Check if user exists
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if user:
        if user.role != "ADMIN":
            # Promote existing user
            user.role = "ADMIN"
            db.commit()
            print(f"✅ User {phone_number} promoted to ADMIN")
        else:
            print(f"ℹ️ User {phone_number} is already an ADMIN")
    else:
        # Create new admin user
        if not password:
             password = input("Enter password for new admin: ").strip()
        if not full_name:
             full_name = input("Enter full name: ").strip()
        
        new_user = User(
            phone_number=phone_number,
            full_name=full_name,
            second_name="",
            hashed_password=get_password_hash(password),
            role="ADMIN"
        )
        db.add(new_user)
        db.commit()
        print(f"✅ Admin user {phone_number} created successfully")
    
    db.close()


if __name__ == "__main__":
    create_admin()

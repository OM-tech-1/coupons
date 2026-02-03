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


def create_admin():
    db = SessionLocal()
    
    phone_number = input("Enter phone number (e.g. +971501234567): ").strip()
    
    # Check if user exists
    user = db.query(User).filter(User.phone_number == phone_number).first()
    
    if user:
        # Promote existing user
        user.role = "ADMIN"
        db.commit()
        print(f"✅ User {phone_number} promoted to ADMIN")
    else:
        # Create new admin user
        password = input("Enter password for new admin: ").strip()
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

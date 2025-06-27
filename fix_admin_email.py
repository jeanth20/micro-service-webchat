#!/usr/bin/env python3
"""
Fix admin user email in database
"""
from sqlalchemy.orm import Session
from database import get_db, engine
import models

def fix_admin_email():
    """Fix the admin user email to be valid"""
    db = Session(bind=engine)
    try:
        # Find admin user with invalid email
        admin_user = db.query(models.User).filter(
            models.User.username == "admin",
            models.User.email == "admin@admin.local"
        ).first()
        
        if admin_user:
            print(f"Found admin user with invalid email: {admin_user.email}")
            admin_user.email = "admin@example.com"
            db.commit()
            print(f"Updated admin email to: {admin_user.email}")
        else:
            print("No admin user with invalid email found")
            
        # Check all users with potentially invalid emails
        users = db.query(models.User).all()
        for user in users:
            if user.email and ("@admin.local" in user.email or not ("." in user.email.split("@")[1] if "@" in user.email else False)):
                print(f"Found user {user.username} with potentially invalid email: {user.email}")
                if "@admin.local" in user.email:
                    user.email = user.email.replace("@admin.local", "@example.com")
                    db.commit()
                    print(f"  Updated to: {user.email}")
                    
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_admin_email()

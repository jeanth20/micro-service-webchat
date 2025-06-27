import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
import secrets

from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBasic()

def verify_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials from environment variables"""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    is_correct_username = secrets.compare_digest(credentials.username, admin_username)
    is_correct_password = secrets.compare_digest(credentials.password, admin_password)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Dashboard endpoints
@router.get("/dashboard")
def get_admin_dashboard(
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    online_users = db.query(models.User).filter(models.User.is_online == True).count()
    total_messages = db.query(models.Message).count()
    total_groups = db.query(models.Group).count()
    total_calls = db.query(models.CallLog).count()
    
    # Recent activity
    recent_users = db.query(models.User).order_by(desc(models.User.created_at)).limit(5).all()
    recent_messages = db.query(models.Message).join(models.User, models.Message.sender_id == models.User.id).order_by(desc(models.Message.created_at)).limit(10).all()
    recent_calls = db.query(models.CallLog).order_by(desc(models.CallLog.started_at)).limit(10).all()
    
    return {
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "online_users": online_users,
            "total_messages": total_messages,
            "total_groups": total_groups,
            "total_calls": total_calls
        },
        "recent_activity": {
            "users": recent_users,
            "messages": recent_messages,
            "calls": recent_calls
        }
    }

# User Management
@router.get("/users")
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get all users with optional search"""
    query = db.query(models.User)

    if search:
        query = query.filter(
            models.User.username.contains(search) |
            models.User.email.contains(search)
        )

    users = query.offset(skip).limit(limit).all()

    # Convert to dict to avoid email validation issues
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email if user.email and "@" in user.email and "." in user.email.split("@")[1] else None,
            "avatar_url": user.avatar_url,
            "role": user.role.value,
            "is_online": user.is_online,
            "is_active": user.is_active,
            "can_create_chats": user.can_create_chats,
            "last_seen": user.last_seen,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        result.append(user_dict)

    return result

@router.post("/users", response_model=schemas.User)
def create_user_admin(
    user: schemas.UserCreate,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    # Check if username already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists (if provided)
    if user.email:
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log the action
    log_moderation_action(db, admin, "create_user", user_id=db_user.id, reason="Admin created user")
    
    return db_user

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user_admin(
    user_id: int,
    user_update: schemas.UserUpdate,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    # Log the action
    log_moderation_action(db, admin, "update_user", user_id=user_id, reason="Admin updated user")
    
    return db_user

@router.delete("/users/{user_id}")
def delete_user_admin(
    user_id: int,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log the action before deletion
    log_moderation_action(db, admin, "delete_user", user_id=user_id, reason="Admin deleted user")
    
    db.delete(db_user)
    db.commit()
    
    return {"message": "User deleted successfully"}

# Group Management
@router.get("/groups")
def get_all_groups(
    skip: int = 0,
    limit: int = 100,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get all groups with member counts"""
    groups = db.query(models.Group).offset(skip).limit(limit).all()

    # Add member count to each group
    result = []
    for group in groups:
        group_dict = {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "avatar_url": group.avatar_url,
            "created_by": group.created_by,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "member_count": db.query(models.GroupMember).filter(models.GroupMember.group_id == group.id).count(),
            "creator_username": group.creator.username if group.creator else f"User {group.created_by}"
        }
        result.append(group_dict)

    return result

@router.post("/groups", response_model=schemas.Group)
def create_group_admin(
    group: schemas.GroupCreate,
    created_by: int,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Create a new group (admin only)"""
    # Check if creator exists
    creator = db.query(models.User).filter(models.User.id == created_by).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found")

    # Create group
    db_group = models.Group(**group.dict(), created_by=created_by)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    # Add creator as admin member
    group_member = models.GroupMember(
        group_id=db_group.id,
        user_id=created_by,
        is_admin=True
    )
    db.add(group_member)
    db.commit()

    # Log the action
    log_moderation_action(db, admin, "create_group", group_id=db_group.id, reason="Admin created group")

    return db_group

@router.delete("/groups/{group_id}")
def delete_group_admin(
    group_id: int,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Delete group (admin only)"""
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Log the action before deletion
    log_moderation_action(db, admin, "delete_group", group_id=group_id, reason="Admin deleted group")

    db.delete(db_group)
    db.commit()

    return {"message": "Group deleted successfully"}

@router.get("/groups/{group_id}/members")
def get_group_members(
    group_id: int,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get group members"""
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    members = db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()

    result = []
    for member in members:
        result.append({
            "id": member.id,
            "user_id": member.user_id,
            "user": {
                "id": member.user.id,
                "username": member.user.username,
                "email": member.user.email
            },
            "is_admin": member.is_admin,
            "joined_at": member.joined_at
        })

    return result

# Chat Moderation
@router.get("/messages")
def get_messages_for_moderation(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get messages for moderation"""
    query = db.query(models.Message).join(models.User, models.Message.sender_id == models.User.id).filter(models.Message.deleted_at.is_(None))

    if user_id:
        query = query.filter(models.Message.sender_id == user_id)
    if group_id:
        query = query.filter(models.Message.group_id == group_id)

    messages = query.order_by(desc(models.Message.created_at)).offset(skip).limit(limit).all()

    # Log the snooping action
    log_moderation_action(db, admin, "view_messages",
                         user_id=user_id, group_id=group_id,
                         reason="Admin viewed messages for moderation")

    # Format messages with sender info
    result = []
    for message in messages:
        message_dict = {
            "id": message.id,
            "sender_id": message.sender_id,
            "sender_username": message.sender.username,
            "receiver_id": message.receiver_id,
            "group_id": message.group_id,
            "content": message.content,
            "message_type": message.message_type.value,
            "created_at": message.created_at,
            "is_read": message.is_read,
            "is_delivered": message.is_delivered
        }

        # Add group or receiver info
        if message.group_id:
            message_dict["group_name"] = message.group.name if message.group else f"Group {message.group_id}"
        elif message.receiver_id:
            message_dict["receiver_username"] = message.receiver.username if message.receiver else f"User {message.receiver_id}"

        result.append(message_dict)

    return result

@router.delete("/messages/{message_id}")
def delete_message_admin(
    message_id: int,
    reason: Optional[str] = None,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Delete message (admin only)"""
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Soft delete
    db_message.deleted_at = datetime.utcnow()
    db.commit()

    # Log the action
    log_moderation_action(db, admin, "delete_message",
                         message_id=message_id, reason=reason or "Admin deleted message")

    return {"message": "Message deleted successfully"}

# Call Logs
@router.get("/call-logs")
def get_call_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get call logs with user information"""
    query = db.query(models.CallLog).join(models.User, models.CallLog.caller_id == models.User.id)

    if user_id:
        query = query.filter(
            (models.CallLog.caller_id == user_id) |
            (models.CallLog.receiver_id == user_id)
        )

    call_logs = query.order_by(desc(models.CallLog.started_at)).offset(skip).limit(limit).all()

    # Format call logs with user info
    result = []
    for call in call_logs:
        call_dict = {
            "id": call.id,
            "caller_id": call.caller_id,
            "caller_username": call.caller.username,
            "receiver_id": call.receiver_id,
            "receiver_username": call.receiver.username if call.receiver else None,
            "group_id": call.group_id,
            "call_status": call.call_status.value,
            "started_at": call.started_at,
            "ended_at": call.ended_at,
            "duration": call.duration
        }
        result.append(call_dict)

    return result

# Moderation Logs
@router.get("/moderation-logs", response_model=List[schemas.ChatModerationLog])
def get_moderation_logs(
    skip: int = 0,
    limit: int = 100,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get moderation logs"""
    return db.query(models.ChatModerationLog).order_by(desc(models.ChatModerationLog.created_at)).offset(skip).limit(limit).all()

# Settings Management
@router.get("/settings")
def get_admin_settings(
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Get admin settings"""
    settings = db.query(models.AdminSettings).all()
    return {setting.setting_key: setting.setting_value for setting in settings}

@router.put("/settings/{setting_key}")
def update_admin_setting(
    setting_key: str,
    setting_update: schemas.AdminSettingsUpdate,
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Update admin setting"""
    setting = db.query(models.AdminSettings).filter(models.AdminSettings.setting_key == setting_key).first()

    if not setting:
        # Create new setting
        setting = models.AdminSettings(
            setting_key=setting_key,
            setting_value=setting_update.setting_value,
            description=setting_update.description
        )
        db.add(setting)
    else:
        # Update existing setting
        setting.setting_value = setting_update.setting_value
        if setting_update.description:
            setting.description = setting_update.description

    db.commit()
    db.refresh(setting)

    return setting

def log_moderation_action(db: Session, admin_username: str, action: str, **kwargs):
    """Helper function to log moderation actions"""
    # Find admin user by username (assuming admin username is unique)
    admin_user = db.query(models.User).filter(models.User.username == admin_username).first()
    if admin_user:
        log_entry = models.ChatModerationLog(
            admin_id=admin_user.id,
            action=action,
            **kwargs
        )
        db.add(log_entry)
        db.commit()

def initialize_admin_settings(db: Session):
    """Initialize default admin settings if they don't exist"""
    default_settings = [
        ("allow_user_chats", "true", "Allow users to create direct chats"),
        ("allow_group_creation", "true", "Allow users to create groups"),
        ("max_file_size", "10485760", "Maximum file upload size in bytes (10MB)"),
        ("max_message_length", "4000", "Maximum message length in characters"),
        ("enable_message_reactions", "true", "Enable message reactions"),
        ("enable_typing_indicators", "true", "Enable typing indicators"),
        ("enable_read_receipts", "true", "Enable read receipts"),
        ("auto_delete_messages", "false", "Auto delete messages after certain period"),
        ("message_retention_days", "365", "Number of days to retain messages"),
    ]

    for key, value, description in default_settings:
        existing = db.query(models.AdminSettings).filter(models.AdminSettings.setting_key == key).first()
        if not existing:
            setting = models.AdminSettings(
                setting_key=key,
                setting_value=value,
                description=description
            )
            db.add(setting)

    db.commit()

@router.post("/initialize")
def initialize_admin_data(
    admin: str = Depends(verify_admin_credentials),
    db: Session = Depends(get_db)
):
    """Initialize admin data and settings"""
    try:
        # Initialize admin settings
        initialize_admin_settings(db)

        # Create admin user if it doesn't exist
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_user = db.query(models.User).filter(models.User.username == admin_username).first()
        if not admin_user:
            admin_user = models.User(
                username=admin_username,
                email=f"{admin_username}@example.com",  # Use a valid email format
                role=models.UserRole.ADMIN,
                is_active=True,
                can_create_chats=True
            )
            db.add(admin_user)
            db.commit()

        return {"message": "Admin data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize admin data: {str(e)}")

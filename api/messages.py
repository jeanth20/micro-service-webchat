from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime
from database import get_db
import models
import schemas

router = APIRouter()

@router.post("/", response_model=schemas.Message)
def create_message(message: schemas.MessageCreate, db: Session = Depends(get_db)):
    """Create a new message"""
    # Validate that either receiver_id or group_id is provided
    if not message.receiver_id and not message.group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either receiver_id or group_id must be provided"
        )

    # Validate that both receiver_id and group_id are not provided
    if message.receiver_id and message.group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both receiver_id and group_id"
        )

    # Check sender permissions for direct messages
    if message.receiver_id:
        sender = db.query(models.User).filter(models.User.id == message.sender_id).first()
        if sender and not sender.can_create_chats and sender.role != models.UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create direct chats"
            )

        # Check global chat creation setting
        chat_setting = db.query(models.AdminSettings).filter(
            models.AdminSettings.setting_key == "allow_user_chats"
        ).first()

        if chat_setting and chat_setting.setting_value == "false" and sender.role != models.UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Direct messaging is currently disabled by admin"
            )
    
    # Create message
    db_message = models.Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.get("/", response_model=List[schemas.Message])
def read_messages(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter messages for specific user"),
    group_id: Optional[int] = Query(None, description="Filter messages for specific group"),
    db: Session = Depends(get_db)
):
    """Get messages with optional filtering"""
    query = db.query(models.Message).filter(models.Message.deleted_at.is_(None))
    
    if group_id:
        query = query.filter(models.Message.group_id == group_id)
    elif user_id:
        # Get direct messages for the user
        query = query.filter(
            or_(
                models.Message.sender_id == user_id,
                models.Message.receiver_id == user_id
            )
        )
    
    messages = query.order_by(desc(models.Message.created_at)).offset(skip).limit(limit).all()
    return messages

@router.get("/{message_id}", response_model=schemas.Message)
def read_message(message_id: int, db: Session = Depends(get_db)):
    """Get a specific message by ID"""
    db_message = db.query(models.Message).filter(
        and_(
            models.Message.id == message_id,
            models.Message.deleted_at.is_(None)
        )
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return db_message

@router.put("/{message_id}", response_model=schemas.Message)
def update_message(message_id: int, message_update: schemas.MessageUpdate, db: Session = Depends(get_db)):
    """Update a message"""
    db_message = db.query(models.Message).filter(
        and_(
            models.Message.id == message_id,
            models.Message.deleted_at.is_(None)
        )
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Update message fields
    update_data = message_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_message, field, value)
    
    db.commit()
    db.refresh(db_message)
    return db_message

@router.delete("/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db)):
    """Soft delete a message"""
    db_message = db.query(models.Message).filter(
        and_(
            models.Message.id == message_id,
            models.Message.deleted_at.is_(None)
        )
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Soft delete by setting deleted_at timestamp
    from sqlalchemy.sql import func
    db_message.deleted_at = func.now()
    db.commit()
    
    return {"message": "Message deleted successfully"}

@router.get("/conversation/{user1_id}/{user2_id}", response_model=List[schemas.Message])
def get_conversation(
    user1_id: int,
    user2_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get conversation between two users"""
    messages = db.query(models.Message).filter(
        and_(
            models.Message.deleted_at.is_(None),
            or_(
                and_(
                    models.Message.sender_id == user1_id,
                    models.Message.receiver_id == user2_id
                ),
                and_(
                    models.Message.sender_id == user2_id,
                    models.Message.receiver_id == user1_id
                )
            )
        )
    ).order_by(models.Message.created_at).offset(skip).limit(limit).all()
    
    return messages

@router.get("/group/{group_id}", response_model=List[schemas.Message])
def get_group_messages(
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get messages for a specific group"""
    messages = db.query(models.Message).filter(
        and_(
            models.Message.group_id == group_id,
            models.Message.deleted_at.is_(None)
        )
    ).order_by(models.Message.created_at).offset(skip).limit(limit).all()
    
    return messages

@router.put("/{message_id}/read")
def mark_message_as_read(message_id: int, db: Session = Depends(get_db)):
    """Mark a message as read"""
    db_message = db.query(models.Message).filter(
        and_(
            models.Message.id == message_id,
            models.Message.deleted_at.is_(None)
        )
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db_message.is_read = True
    db.commit()
    
    return {"message": "Message marked as read"}

@router.put("/{message_id}/delivered")
def mark_message_as_delivered(message_id: int, db: Session = Depends(get_db)):
    """Mark a message as delivered"""
    db_message = db.query(models.Message).filter(
        and_(
            models.Message.id == message_id,
            models.Message.deleted_at.is_(None)
        )
    ).first()
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db_message.is_delivered = True
    db.commit()
    
    return {"message": "Message marked as delivered"}

@router.get("/unread/{user_id}")
def get_unread_count(user_id: int, db: Session = Depends(get_db)):
    """Get count of unread messages for a user"""
    unread_count = db.query(models.Message).filter(
        and_(
            models.Message.receiver_id == user_id,
            models.Message.is_read == False,
            models.Message.deleted_at.is_(None)
        )
    ).count()
    
    return {"user_id": user_id, "unread_count": unread_count}

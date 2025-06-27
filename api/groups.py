from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas

router = APIRouter()

@router.post("/", response_model=schemas.Group)
def create_group(group: schemas.GroupCreate, created_by: int, db: Session = Depends(get_db)):
    """Create a new group"""
    # Check if creator exists
    creator = db.query(models.User).filter(models.User.id == created_by).first()
    if not creator:
        raise HTTPException(status_code=404, detail="Creator user not found")

    # Check if user has permission to create groups
    if not creator.can_create_chats and creator.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create groups"
        )

    # Check global group creation setting
    group_setting = db.query(models.AdminSettings).filter(
        models.AdminSettings.setting_key == "allow_group_creation"
    ).first()

    if group_setting and group_setting.setting_value == "false" and creator.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group creation is currently disabled by admin"
        )

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

    return db_group

@router.get("/", response_model=List[schemas.Group])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of groups"""
    groups = db.query(models.Group).offset(skip).limit(limit).all()
    return groups

@router.get("/{group_id}", response_model=schemas.Group)
def read_group(group_id: int, db: Session = Depends(get_db)):
    """Get a specific group by ID"""
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group

@router.put("/{group_id}", response_model=schemas.Group)
def update_group(group_id: int, group_update: schemas.GroupUpdate, db: Session = Depends(get_db)):
    """Update a group"""
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Update group fields
    update_data = group_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group

@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """Delete a group"""
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Delete all group members first
    db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).delete()
    
    # Delete the group
    db.delete(db_group)
    db.commit()
    return {"message": "Group deleted successfully"}

@router.post("/{group_id}/members", response_model=schemas.GroupMember)
def add_group_member(group_id: int, user_id: int, is_admin: bool = False, db: Session = Depends(get_db)):
    """Add a member to a group"""
    # Check if group exists
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already a member
    existing_member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )
    
    # Add member
    group_member = models.GroupMember(
        group_id=group_id,
        user_id=user_id,
        is_admin=is_admin
    )
    db.add(group_member)
    db.commit()
    db.refresh(group_member)
    
    return group_member

@router.get("/{group_id}/members", response_model=List[schemas.GroupMember])
def get_group_members(group_id: int, db: Session = Depends(get_db)):
    """Get all members of a group"""
    # Check if group exists
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    members = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id
    ).all()
    
    return members

@router.delete("/{group_id}/members/{user_id}")
def remove_group_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    """Remove a member from a group"""
    # Check if group exists
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Find the member
    group_member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if not group_member:
        raise HTTPException(status_code=404, detail="User is not a member of this group")
    
    # Don't allow removing the group creator if they're the only admin
    if group_member.is_admin and db_group.created_by == user_id:
        admin_count = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group_id,
            models.GroupMember.is_admin == True
        ).count()
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the only admin from the group"
            )
    
    # Remove member
    db.delete(group_member)
    db.commit()
    
    return {"message": "Member removed successfully"}

@router.get("/user/{user_id}", response_model=List[schemas.Group])
def get_user_groups(user_id: int, db: Session = Depends(get_db)):
    """Get all groups that a user is a member of"""
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get groups through group memberships
    group_memberships = db.query(models.GroupMember).filter(
        models.GroupMember.user_id == user_id
    ).all()
    
    groups = []
    for membership in group_memberships:
        group = db.query(models.Group).filter(models.Group.id == membership.group_id).first()
        if group:
            groups.append(group)
    
    return groups

@router.put("/{group_id}/members/{user_id}/admin")
def toggle_admin_status(group_id: int, user_id: int, is_admin: bool, db: Session = Depends(get_db)):
    """Toggle admin status for a group member"""
    # Check if group exists
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Find the member
    group_member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()
    if not group_member:
        raise HTTPException(status_code=404, detail="User is not a member of this group")
    
    # Don't allow removing admin status from group creator if they're the only admin
    if not is_admin and group_member.is_admin and db_group.created_by == user_id:
        admin_count = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group_id,
            models.GroupMember.is_admin == True
        ).count()
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove admin status from the only admin"
            )
    
    # Update admin status
    group_member.is_admin = is_admin
    db.commit()
    
    return {"message": f"Admin status {'granted' if is_admin else 'revoked'} successfully"}

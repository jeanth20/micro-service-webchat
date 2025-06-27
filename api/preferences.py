from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/preferences", tags=["preferences"])

@router.get("/{user_id}", response_model=schemas.UserPreferences)
def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    """Get user preferences"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get or create preferences
    preferences = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = models.UserPreferences(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences

@router.put("/{user_id}", response_model=schemas.UserPreferences)
def update_user_preferences(
    user_id: int, 
    preferences_update: schemas.UserPreferencesUpdate, 
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get or create preferences
    preferences = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        # Create new preferences with provided data
        preferences_data = preferences_update.dict(exclude_unset=True)
        preferences_data['user_id'] = user_id
        preferences = models.UserPreferences(**preferences_data)
        db.add(preferences)
    else:
        # Update existing preferences
        update_data = preferences_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    return preferences

@router.post("/{user_id}", response_model=schemas.UserPreferences)
def create_user_preferences(
    user_id: int, 
    preferences: schemas.UserPreferencesCreate, 
    db: Session = Depends(get_db)
):
    """Create user preferences"""
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if preferences already exist
    existing_preferences = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == user_id
    ).first()
    
    if existing_preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User preferences already exist"
        )
    
    # Create new preferences
    db_preferences = models.UserPreferences(**preferences.dict(), user_id=user_id)
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences

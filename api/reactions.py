from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from database import get_db
import models
import schemas

router = APIRouter()

@router.post("/", response_model=schemas.Reaction)
def create_reaction(reaction: schemas.ReactionCreate, user_id: int, db: Session = Depends(get_db)):
    """Create or update a reaction to a message"""
    
    # Check if message exists
    message = db.query(models.Message).filter(models.Message.id == reaction.message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user already reacted with this emoji to this message
    existing_reaction = db.query(models.Reaction).filter(
        and_(
            models.Reaction.message_id == reaction.message_id,
            models.Reaction.user_id == user_id,
            models.Reaction.emoji == reaction.emoji
        )
    ).first()
    
    if existing_reaction:
        # Remove existing reaction (toggle off)
        db.delete(existing_reaction)
        db.commit()
        return {"message": "Reaction removed"}
    
    # Create new reaction
    db_reaction = models.Reaction(
        message_id=reaction.message_id,
        user_id=user_id,
        emoji=reaction.emoji
    )
    
    db.add(db_reaction)
    db.commit()
    db.refresh(db_reaction)
    
    return db_reaction

@router.get("/message/{message_id}", response_model=List[schemas.Reaction])
def get_message_reactions(message_id: int, db: Session = Depends(get_db)):
    """Get all reactions for a specific message"""
    reactions = db.query(models.Reaction).filter(
        models.Reaction.message_id == message_id
    ).all()
    
    return reactions

@router.delete("/{reaction_id}")
def delete_reaction(reaction_id: int, user_id: int, db: Session = Depends(get_db)):
    """Delete a specific reaction"""
    reaction = db.query(models.Reaction).filter(
        and_(
            models.Reaction.id == reaction_id,
            models.Reaction.user_id == user_id
        )
    ).first()
    
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")
    
    db.delete(reaction)
    db.commit()
    
    return {"message": "Reaction deleted"}

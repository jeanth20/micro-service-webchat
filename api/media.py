import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from PIL import Image
from database import get_db
import models
import schemas

router = APIRouter()

# Allowed file types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/mov", "video/wmv"}
ALLOWED_AUDIO_TYPES = {"audio/mp3", "audio/wav", "audio/ogg", "audio/m4a"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "text/plain", "application/msword", 
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB default
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")

def get_file_type(content_type: str) -> str:
    """Determine file type based on content type"""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    elif content_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    elif content_type in ALLOWED_DOCUMENT_TYPES:
        return "file"  # Use "file" instead of "document" to match MessageType enum
    else:
        return "file"

def is_allowed_file_type(content_type: str) -> bool:
    """Check if file type is allowed"""
    allowed_types = (ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | 
                    ALLOWED_AUDIO_TYPES | ALLOWED_DOCUMENT_TYPES)
    return content_type in allowed_types

async def save_uploaded_file(file: UploadFile, user_id: int) -> str:
    """Save uploaded file and return the file path"""
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create user-specific directory
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return file_path

def create_thumbnail(image_path: str) -> str:
    """Create thumbnail for image files"""
    try:
        with Image.open(image_path) as img:
            # Create thumbnail
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumbnail_path = image_path.replace(".", "_thumb.")
            img.save(thumbnail_path)
            return thumbnail_path
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None

@router.post("/upload", response_model=schemas.Media)
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a file"""
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Read file content to check size
    file_content = await file.read()
    file_size = len(file_content)

    # Reset file position
    await file.seek(0)

    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )

    # Check file type
    if not is_allowed_file_type(file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} is not allowed"
        )

    try:
        # Save file
        file_path = await save_uploaded_file(file, user_id)

        # Create thumbnail for images
        thumbnail_path = None
        if file.content_type in ALLOWED_IMAGE_TYPES:
            thumbnail_path = create_thumbnail(file_path)

        # Create media record
        db_media = models.Media(
            filename=os.path.basename(file_path),
            original_filename=file.filename,
            file_path=file_path,
            file_type=get_file_type(file.content_type),
            file_size=file_size,
            uploaded_by=user_id
        )

        db.add(db_media)
        db.commit()
        db.refresh(db_media)

        return db_media

    except Exception as e:
        # Clean up file if database operation fails
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/", response_model=List[schemas.Media])
def get_media_files(
    skip: int = 0,
    limit: int = 100,
    user_id: int = None,
    file_type: str = None,
    db: Session = Depends(get_db)
):
    """Get media files with optional filtering"""
    query = db.query(models.Media)
    
    if user_id:
        query = query.filter(models.Media.uploaded_by == user_id)
    
    if file_type:
        query = query.filter(models.Media.file_type == file_type)
    
    media_files = query.offset(skip).limit(limit).all()
    return media_files

@router.get("/{media_id}", response_model=schemas.Media)
def get_media_file(media_id: int, db: Session = Depends(get_db)):
    """Get a specific media file by ID"""
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=404, detail="Media file not found")
    return db_media

@router.get("/{media_id}/download")
def download_media_file(media_id: int, db: Session = Depends(get_db)):
    """Download a media file"""
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    if not os.path.exists(db_media.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=db_media.file_path,
        filename=db_media.original_filename,
        media_type='application/octet-stream'
    )

@router.get("/{media_id}/view")
def view_media_file(media_id: int, db: Session = Depends(get_db)):
    """View a media file (for images, videos, etc.)"""
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    if not os.path.exists(db_media.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Determine media type for proper browser handling
    media_type_mapping = {
        "image": "image/*",
        "video": "video/*",
        "audio": "audio/*",
        "document": "application/pdf" if db_media.file_path.endswith('.pdf') else "text/plain"
    }
    
    media_type = media_type_mapping.get(db_media.file_type, 'application/octet-stream')
    
    return FileResponse(
        path=db_media.file_path,
        media_type=media_type
    )

@router.delete("/{media_id}")
def delete_media_file(media_id: int, db: Session = Depends(get_db)):
    """Delete a media file"""
    db_media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if db_media is None:
        raise HTTPException(status_code=404, detail="Media file not found")
    
    # Delete file from disk
    try:
        if os.path.exists(db_media.file_path):
            os.remove(db_media.file_path)
        
        # Delete thumbnail if it exists
        thumbnail_path = db_media.file_path.replace(".", "_thumb.")
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            
    except Exception as e:
        print(f"Error deleting file from disk: {e}")
    
    # Delete from database
    db.delete(db_media)
    db.commit()
    
    return {"message": "Media file deleted successfully"}

@router.get("/user/{user_id}/images", response_model=List[schemas.Media])
def get_user_images(user_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Get all images uploaded by a specific user"""
    images = db.query(models.Media).filter(
        models.Media.uploaded_by == user_id,
        models.Media.file_type == "image"
    ).offset(skip).limit(limit).all()
    
    return images

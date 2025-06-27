from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import MessageType, CallStatus, ThemeMode, ColorTheme, UserRole

# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    is_online: Optional[bool] = None
    is_active: Optional[bool] = None
    can_create_chats: Optional[bool] = None

class User(UserBase):
    id: int
    role: UserRole
    is_online: bool
    is_active: bool
    can_create_chats: bool
    last_seen: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Group Schemas
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None

class Group(GroupBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Message Schemas
class MessageBase(BaseModel):
    content: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    receiver_id: Optional[int] = None
    group_id: Optional[int] = None
    reply_to_id: Optional[int] = None

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    is_read: Optional[bool] = None
    is_delivered: Optional[bool] = None

class Message(MessageBase):
    id: int
    sender_id: int
    media_id: Optional[int] = None
    is_read: bool
    is_delivered: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Media Schemas
class MediaBase(BaseModel):
    filename: str
    original_filename: str
    file_type: str
    file_size: int

class MediaCreate(MediaBase):
    file_path: str
    uploaded_by: int

class Media(MediaBase):
    id: int
    file_path: str
    uploaded_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Group Member Schemas
class GroupMemberBase(BaseModel):
    group_id: int
    user_id: int
    is_admin: bool = False

class GroupMemberCreate(GroupMemberBase):
    pass

class GroupMember(GroupMemberBase):
    id: int
    joined_at: datetime
    
    class Config:
        from_attributes = True

# Typing Indicator Schemas
class TypingIndicatorBase(BaseModel):
    group_id: Optional[int] = None
    receiver_id: Optional[int] = None
    is_typing: bool = True

class TypingIndicatorCreate(TypingIndicatorBase):
    user_id: int

class TypingIndicator(TypingIndicatorBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Call Log Schemas
class CallLogBase(BaseModel):
    receiver_id: Optional[int] = None
    group_id: Optional[int] = None
    call_status: CallStatus

class CallLogCreate(CallLogBase):
    caller_id: int

class CallLogUpdate(BaseModel):
    call_status: Optional[CallStatus] = None
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None

class CallLog(CallLogBase):
    id: int
    caller_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None
    
    class Config:
        from_attributes = True

# WebSocket Message Schemas
class WSMessage(BaseModel):
    type: str  # message, typing, call, etc.
    data: dict

class WSTypingMessage(BaseModel):
    type: str = "typing"
    user_id: int
    group_id: Optional[int] = None
    receiver_id: Optional[int] = None
    is_typing: bool

class WSChatMessage(BaseModel):
    type: str = "message"
    message: Message

class WSCallMessage(BaseModel):
    type: str = "call"
    call_log: CallLog

# Reaction Schemas
class ReactionBase(BaseModel):
    message_id: int
    emoji: str

class ReactionCreate(ReactionBase):
    pass

class Reaction(ReactionBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# User Preferences Schemas
class UserPreferencesBase(BaseModel):
    theme_mode: ThemeMode = ThemeMode.LIGHT
    color_theme: ColorTheme = ColorTheme.BLUE
    notifications_enabled: bool = True
    sound_enabled: bool = True
    auto_download_media: bool = True
    show_online_status: bool = True

class UserPreferencesCreate(UserPreferencesBase):
    pass

class UserPreferencesUpdate(BaseModel):
    theme_mode: Optional[ThemeMode] = None
    color_theme: Optional[ColorTheme] = None
    notifications_enabled: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    auto_download_media: Optional[bool] = None
    show_online_status: Optional[bool] = None

class UserPreferences(UserPreferencesBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Admin Schemas
class AdminLogin(BaseModel):
    username: str
    password: str

class AdminSettings(BaseModel):
    setting_key: str
    setting_value: str
    description: Optional[str] = None

class AdminSettingsUpdate(BaseModel):
    setting_value: str
    description: Optional[str] = None

class ChatModerationLog(BaseModel):
    id: int
    admin_id: int
    message_id: Optional[int] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    action: str
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatModerationCreate(BaseModel):
    message_id: Optional[int] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    action: str
    reason: Optional[str] = None

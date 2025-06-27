import os
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import json
from typing import List, Dict

from database import get_db, create_tables
from api import users, messages, groups, media, websocket_manager, reactions, preferences, admin
import models

load_dotenv()

# Create FastAPI app
app = FastAPI(title="WebChat API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create upload directory if it doesn't exist
upload_dir = os.getenv("UPLOAD_DIR", "static/uploads")
os.makedirs(upload_dir, exist_ok=True)

# Include API routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(reactions.router, prefix="/api/reactions", tags=["reactions"])
app.include_router(preferences.router)
app.include_router(admin.router)

# WebSocket manager
ws_manager = websocket_manager.ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    create_tables()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, user_id: int = None, username: str = None, db: Session = Depends(get_db)):
    """Serve the main chat interface"""
    # Get some sample data for the template
    users_list = db.query(models.User).limit(10).all()

    # Check if specific user is requested
    current_user = None
    if user_id:
        current_user = db.query(models.User).filter(models.User.id == user_id).first()
    elif username:
        current_user = db.query(models.User).filter(models.User.username == username).first()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "users": users_list,
        "current_user": current_user
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Serve the admin panel interface with authentication"""
    # Check for basic auth header
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Admin Login Required</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
                    .login-box { max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
                    .error { color: red; margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="login-box">
                    <h2>Admin Access Required</h2>
                    <p>Please enter admin credentials to access the admin panel.</p>
                    <button onclick="promptLogin()">Login</button>
                    <script>
                        function promptLogin() {
                            const username = prompt("Admin Username:");
                            const password = prompt("Admin Password:");
                            if (username && password) {
                                const credentials = btoa(username + ':' + password);
                                fetch('/admin', {
                                    headers: { 'Authorization': 'Basic ' + credentials }
                                }).then(response => {
                                    if (response.ok) {
                                        // Store credentials for future requests
                                        sessionStorage.setItem('adminAuth', credentials);
                                        location.reload();
                                    } else {
                                        alert('Invalid credentials');
                                    }
                                });
                            }
                        }

                        // Check if we have stored credentials
                        const storedAuth = sessionStorage.getItem('adminAuth');
                        if (storedAuth) {
                            fetch('/admin', {
                                headers: { 'Authorization': 'Basic ' + storedAuth }
                            }).then(response => {
                                if (response.ok) {
                                    location.reload();
                                }
                            });
                        }
                    </script>
                </div>
            </body>
            </html>
            """,
            status_code=401,
            headers={"WWW-Authenticate": "Basic realm='Admin Panel'"}
        )

    # Verify credentials
    import base64
    import secrets
    try:
        encoded_credentials = auth_header.split(" ")[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

        is_correct_username = secrets.compare_digest(username, admin_username)
        is_correct_password = secrets.compare_digest(password, admin_password)

        if not (is_correct_username and is_correct_password):
            raise ValueError("Invalid credentials")

    except (ValueError, IndexError):
        return HTMLResponse(
            content="<h1>401 Unauthorized</h1><p>Invalid admin credentials</p>",
            status_code=401,
            headers={"WWW-Authenticate": "Basic realm='Admin Panel'"}
        )

    return templates.TemplateResponse("admin.html", {
        "request": request
    })

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time communication"""
    print(f"WebSocket connection attempt for user {user_id}")

    await ws_manager.connect(websocket, user_id)
    print(f"WebSocket connected for user {user_id}")

    # Update user online status
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.is_online = True
        db.commit()
        print(f"User {user.username} is now online")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WebSocket data from user {user_id}: {data}")

            try:
                message_data = json.loads(data)

                # Handle different message types
                if message_data.get("type") == "message":
                    print(f"Handling chat message from user {user_id}")
                    await handle_chat_message(message_data, user_id, db)
                elif message_data.get("type") == "typing":
                    await handle_typing_indicator(message_data, user_id, db)
                elif message_data.get("type") == "call":
                    await handle_call_message(message_data, user_id, db)
                elif message_data.get("type") == "webrtc-signal":
                    await handle_webrtc_signal(message_data, user_id, db)
                elif message_data.get("type") == "reaction":
                    await handle_reaction(message_data, user_id, db)
                else:
                    print(f"Unknown message type: {message_data.get('type')}")

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")
        ws_manager.disconnect(user_id)
        # Update user offline status
        if user:
            user.is_online = False
            db.commit()
            print(f"User {user.username} is now offline")
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(user_id)
        if user:
            user.is_online = False
            db.commit()

async def handle_chat_message(message_data: dict, sender_id: int, db: Session):
    """Handle incoming chat messages"""
    try:
        print(f"Processing chat message from user {sender_id}: {message_data}")

        # Create message in database
        message = models.Message(
            sender_id=sender_id,
            receiver_id=message_data.get("receiver_id"),
            group_id=message_data.get("group_id"),
            content=message_data.get("content"),
            message_type=models.MessageType(message_data.get("message_type", "text")),
            media_id=message_data.get("media_id")
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        print(f"Message saved to database with ID: {message.id}")

        # Prepare message data for broadcasting
        message_payload = {
            "type": "message",
            "message": {
                "id": message.id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "group_id": message.group_id,
                "content": message.content,
                "message_type": message.message_type.value,
                "media_id": message.media_id,
                "created_at": message.created_at.isoformat(),
                "is_read": message.is_read,
                "is_delivered": message.is_delivered
            }
        }

        print(f"Broadcasting message payload: {message_payload}")

        # Broadcast message to relevant users
        if message.group_id:
            print(f"Broadcasting to group {message.group_id}")
            # Group message - send to all group members
            group_members = db.query(models.GroupMember).filter(
                models.GroupMember.group_id == message.group_id
            ).all()

            print(f"Found {len(group_members)} group members")

            # Send to all members
            for member in group_members:
                print(f"Sending to group member: {member.user_id}")
                await ws_manager.send_personal_message(
                    json.dumps(message_payload),
                    member.user_id
                )
        else:
            print(f"Broadcasting direct message from {sender_id} to {message.receiver_id}")
            # Direct message - send to receiver
            if message.receiver_id:
                print(f"Sending to receiver: {message.receiver_id}")
                success = await ws_manager.send_personal_message(
                    json.dumps(message_payload),
                    message.receiver_id
                )
                print(f"Message sent to receiver: {success}")

                # Send confirmation to sender
                print(f"Sending confirmation to sender: {sender_id}")
                success = await ws_manager.send_personal_message(
                    json.dumps(message_payload),
                    sender_id
                )
                print(f"Confirmation sent to sender: {success}")

    except Exception as e:
        print(f"Error handling chat message: {e}")
        import traceback
        traceback.print_exc()

        # Send error message back to sender
        error_payload = {
            "type": "error",
            "message": "Failed to send message",
            "error": str(e)
        }
        await ws_manager.send_personal_message(
            json.dumps(error_payload),
            sender_id
        )

async def handle_typing_indicator(message_data: dict, user_id: int, db: Session):
    """Handle typing indicators"""
    try:
        # Broadcast typing indicator
        if message_data.get("group_id"):
            # Group typing
            group_members = db.query(models.GroupMember).filter(
                models.GroupMember.group_id == message_data["group_id"]
            ).all()
            for member in group_members:
                if member.user_id != user_id:
                    await ws_manager.send_personal_message(json.dumps({
                        "type": "typing",
                        "user_id": user_id,
                        "group_id": message_data["group_id"],
                        "is_typing": message_data.get("is_typing", True)
                    }), member.user_id)
        elif message_data.get("receiver_id"):
            # Direct message typing
            await ws_manager.send_personal_message(json.dumps({
                "type": "typing",
                "user_id": user_id,
                "receiver_id": message_data["receiver_id"],
                "is_typing": message_data.get("is_typing", True)
            }), message_data["receiver_id"])
            
    except Exception as e:
        print(f"Error handling typing indicator: {e}")

async def handle_call_message(message_data: dict, caller_id: int, db: Session):
    """Handle call-related messages"""
    try:
        print(f"Handling call message: {message_data}")

        call_status = message_data.get("call_status")
        call_type = message_data.get("call_type", "audio")
        call_id = message_data.get("call_id")
        receiver_id = message_data.get("receiver_id")

        # Create call log entry for new requests
        if call_status == "request":
            call_log = models.CallLog(
                caller_id=caller_id,
                receiver_id=receiver_id,
                group_id=message_data.get("group_id"),
                call_status=models.CallStatus(call_status)
            )
            db.add(call_log)
            db.commit()
            db.refresh(call_log)

            # Broadcast call request with all necessary data
            call_payload = {
                "type": "call",
                "call_status": call_status,
                "call_type": call_type,
                "call_id": call_id,
                "caller_id": caller_id,
                "receiver_id": receiver_id,
                "call_log": {
                    "id": call_log.id,
                    "caller_id": call_log.caller_id,
                    "receiver_id": call_log.receiver_id,
                    "call_status": call_log.call_status.value,
                    "started_at": call_log.started_at.isoformat()
                }
            }

            print(f"Sending call request payload: {call_payload}")

            if receiver_id:
                await ws_manager.send_personal_message(json.dumps(call_payload), receiver_id)

        else:
            # Handle call responses (accept, decline, end, etc.)
            call_payload = {
                "type": "call",
                "call_status": call_status,
                "call_type": call_type,
                "call_id": call_id,
                "caller_id": caller_id,
                "receiver_id": receiver_id
            }

            print(f"Sending call response payload: {call_payload}")

            # Send to the other party
            if call_status in ["accept", "decline"]:
                # This is a response, so send back to the original caller
                if receiver_id:
                    await ws_manager.send_personal_message(json.dumps(call_payload), receiver_id)
            elif call_status == "end":
                # Send end message to receiver
                if receiver_id:
                    await ws_manager.send_personal_message(json.dumps(call_payload), receiver_id)

    except Exception as e:
        print(f"Error handling call message: {e}")
        import traceback
        traceback.print_exc()

async def handle_webrtc_signal(message_data: dict, sender_id: int, db: Session):
    """Handle WebRTC signaling messages (ICE candidates, SDP offers/answers)"""
    try:
        print(f"Handling WebRTC signal from user {sender_id}: {message_data}")

        call_id = message_data.get("call_id")
        signal = message_data.get("signal")
        receiver_id = message_data.get("receiver_id")

        if not call_id or not signal:
            print("Missing call_id or signal in WebRTC message")
            return

        # Forward the signaling message to the other peer
        signal_payload = {
            "type": "webrtc-signal",
            "call_id": call_id,
            "signal": signal,
            "sender_id": sender_id
        }

        print(f"Forwarding WebRTC signal to receiver {receiver_id}: {signal_payload}")

        if receiver_id:
            await ws_manager.send_personal_message(
                json.dumps(signal_payload),
                receiver_id
            )
        else:
            print("No receiver_id specified for WebRTC signal")

    except Exception as e:
        print(f"Error handling WebRTC signal: {e}")
        import traceback
        traceback.print_exc()

async def handle_reaction(message_data: dict, user_id: int, db: Session):
    """Handle reaction messages"""
    try:
        print(f"Handling reaction from user {user_id}: {message_data}")

        emoji = message_data.get("emoji")
        target_message_id = message_data.get("target_message_id")

        if not emoji or not target_message_id:
            print("Missing emoji or target_message_id in reaction")
            return

        # Check if message exists
        target_message = db.query(models.Message).filter(models.Message.id == target_message_id).first()
        if not target_message:
            print(f"Target message {target_message_id} not found")
            return

        # Check if user already reacted with this emoji
        existing_reaction = db.query(models.Reaction).filter(
            models.Reaction.message_id == target_message_id,
            models.Reaction.user_id == user_id,
            models.Reaction.emoji == emoji
        ).first()

        if existing_reaction:
            # Remove existing reaction (toggle off)
            db.delete(existing_reaction)
            db.commit()
            action = "removed"
        else:
            # Create new reaction
            new_reaction = models.Reaction(
                message_id=target_message_id,
                user_id=user_id,
                emoji=emoji
            )
            db.add(new_reaction)
            db.commit()
            db.refresh(new_reaction)
            action = "added"

        # Get all reactions for this message
        reactions = db.query(models.Reaction).filter(
            models.Reaction.message_id == target_message_id
        ).all()

        # Group reactions by emoji
        reaction_summary = {}
        for reaction in reactions:
            if reaction.emoji not in reaction_summary:
                reaction_summary[reaction.emoji] = []
            reaction_summary[reaction.emoji].append({
                "user_id": reaction.user_id,
                "created_at": reaction.created_at.isoformat()
            })

        # Broadcast reaction update to relevant users
        reaction_payload = {
            "type": "reaction_update",
            "message_id": target_message_id,
            "reactions": reaction_summary,
            "action": action,
            "user_id": user_id,
            "emoji": emoji
        }

        print(f"Broadcasting reaction update: {reaction_payload}")

        # Send to message participants
        if target_message.group_id:
            # Group message - send to all group members
            group_members = db.query(models.GroupMember).filter(
                models.GroupMember.group_id == target_message.group_id
            ).all()

            for member in group_members:
                await ws_manager.send_personal_message(
                    json.dumps(reaction_payload),
                    member.user_id
                )
        else:
            # Direct message - send to both sender and receiver
            await ws_manager.send_personal_message(
                json.dumps(reaction_payload),
                target_message.sender_id
            )
            if target_message.receiver_id:
                await ws_manager.send_personal_message(
                    json.dumps(reaction_payload),
                    target_message.receiver_id
                )

    except Exception as e:
        print(f"Error handling reaction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )

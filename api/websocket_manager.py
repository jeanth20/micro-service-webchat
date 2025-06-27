from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a WebSocket connection and store it"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
    def disconnect(self, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
    async def send_personal_message(self, message: str, user_id: int):
        """Send a message to a specific user"""
        print(f"Attempting to send message to user {user_id}")
        print(f"Active connections: {list(self.active_connections.keys())}")

        if user_id in self.active_connections:
            try:
                print(f"Sending message to user {user_id}: {message}")
                await self.active_connections[user_id].send_text(message)
                print(f"Message sent successfully to user {user_id}")
                return True
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                # Remove disconnected connection
                self.disconnect(user_id)
                return False
        else:
            print(f"User {user_id} not connected")
            return False
                
    async def broadcast(self, message: str):
        """Broadcast a message to all connected users"""
        disconnected_users = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
                
        # Clean up disconnected connections
        for user_id in disconnected_users:
            self.disconnect(user_id)
            
    async def send_to_group(self, message: str, user_ids: List[int]):
        """Send a message to a list of users"""
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)
            
    def get_connected_users(self) -> List[int]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
        
    def is_user_connected(self, user_id: int) -> bool:
        """Check if a user is currently connected"""
        return user_id in self.active_connections

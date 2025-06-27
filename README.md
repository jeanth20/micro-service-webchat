# WebChat - Standalone Real-time Messaging Application

A modern, standalone webchat application built with FastAPI, PostgreSQL, and WebSockets. This application can be easily integrated into any project as a microservice.

## Features

### Core Features
- **Real-time messaging** with WebSocket support and SSE fallback
- **User-to-user chat** and **group chat** functionality
- **File sharing** (images, documents, audio, video)
- **Typing indicators** and **read receipts**
- **Online status** tracking
- **Message history** with soft delete functionality
- **Dark/Light theme** support with multiple color themes

### Media Support
- Image sharing with thumbnail generation
- File uploads (documents, audio, video)
- Media gallery in chat details
- Secure file storage and retrieval

### Advanced Features
- **Call functionality** (audio/video call requests)
- **Search** conversations and users
- **Responsive design** for mobile and desktop
- **Notification system** for new messages
- **Microservice architecture** ready

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Jinja2 templates, Vanilla JavaScript
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Real-time**: WebSockets with SSE fallback
- **File Storage**: Local filesystem with configurable upload directory
- **Migrations**: Alembic for database schema management

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js (optional, for development)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd webchat
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb webchat_db
   
   # Copy environment file
   cp .env.example .env
   
   # Edit .env file with your database credentials
   # DATABASE_URL=postgresql://username:password@localhost:5432/webchat_db
   ```

5. **Initialize database**
   ```bash
   # Initialize Alembic (if not already done)
   alembic init alembic
   
   # Create initial migration
   alembic revision --autogenerate -m "Initial migration"
   
   # Apply migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/webchat_db

# Application Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=0.0.0.0
PORT=8000

# File Upload Configuration
UPLOAD_DIR=static/uploads
MAX_FILE_SIZE=10485760  # 10MB in bytes

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Database Configuration

The application uses PostgreSQL as the primary database. Make sure to:

1. Create a PostgreSQL database
2. Update the `DATABASE_URL` in your `.env` file
3. Run migrations to create the required tables

## API Documentation

Once the application is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key API Endpoints

#### Users
- `POST /api/users/` - Create a new user
- `GET /api/users/` - Get list of users
- `GET /api/users/{user_id}` - Get user by ID
- `PUT /api/users/{user_id}` - Update user
- `PUT /api/users/{user_id}/online-status` - Update online status

#### Messages
- `POST /api/messages/` - Send a message
- `GET /api/messages/` - Get messages (with filtering)
- `GET /api/messages/conversation/{user1_id}/{user2_id}` - Get conversation
- `GET /api/messages/group/{group_id}` - Get group messages
- `PUT /api/messages/{message_id}/read` - Mark as read

#### Groups
- `POST /api/groups/` - Create a group
- `GET /api/groups/` - Get groups
- `POST /api/groups/{group_id}/members` - Add member
- `GET /api/groups/{group_id}/members` - Get members

#### Media
- `POST /api/media/upload` - Upload file
- `GET /api/media/{media_id}/download` - Download file
- `GET /api/media/{media_id}/view` - View file

## WebSocket API

Connect to WebSocket at `/ws/{user_id}` for real-time features:

### Message Types

#### Send Message
```json
{
  "type": "message",
  "content": "Hello world!",
  "message_type": "text",
  "receiver_id": 123,  // For direct messages
  "group_id": 456      // For group messages
}
```

#### Typing Indicator
```json
{
  "type": "typing",
  "is_typing": true,
  "receiver_id": 123,  // For direct messages
  "group_id": 456      // For group messages
}
```

#### Call Request
```json
{
  "type": "call",
  "call_status": "request",
  "receiver_id": 123,  // For direct calls
  "group_id": 456      // For group calls
}
```

## Usage

### Getting Started

1. **Create a User**: When you first visit the application, you'll be prompted to enter a username
2. **Start Chatting**: Click the "+" button to start a new conversation
3. **Send Messages**: Type in the message input and press Enter or click the send button
4. **Upload Files**: Click the attachment or image buttons to share files
5. **Group Chats**: Create groups and add multiple users for group conversations

### Features Guide

#### Themes
- Click the moon/sun icon to toggle dark/light mode
- Use the color dots in the detail panel to change theme colors

#### File Sharing
- Drag and drop files or use the upload buttons
- Supported formats: images, documents, audio, video
- Files are automatically organized and thumbnails generated for images

#### Search
- Use the search bar to find conversations
- Search works on usernames and message content

## Deployment

### Docker Deployment (Recommended)

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Database**: Use a managed PostgreSQL service
2. **File Storage**: Consider using cloud storage (AWS S3, etc.)
3. **Load Balancing**: Use nginx or similar for load balancing
4. **SSL**: Enable HTTPS for secure WebSocket connections
5. **Monitoring**: Add logging and monitoring solutions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team.

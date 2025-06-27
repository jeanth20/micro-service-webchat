I want to create a webchat that is standalone that can be added to any of my future projects.

I want to use fastapi, jinja templates, and a postgresql database
I have an example of a chat app that I want to use as a starting point this is in the example folder

I want to use the same database as my other projects so I want to use the same database connection as my other projects we can just alter the connection string in the .env file


we dont need a login or register page for this app we just need the frontend to make a request to the api for the user store the user in the frontend and then use that user to send messages and receive messages from the api and then display them on the frontend and send them to the api

I want the chat to be realtime so we can use websockets for this but I also want to use Server-Sent Events (SSE) as a backup if the websockets dont work 

Can we save all the messages and users data like photos ect in the database so that we can retrieve them later?

can we also have a soft delete for the messages so we dont ever delete the messages but we can hide them from the user

we will need to keep in mind that this will be a micro service so it will need to be able to connect with another projecct and only work with the connected project 

we will need the following functionallity for the chat:
user to user chat 
group chat
send messages
receive messages
display messages
send images
send files
send audio
send video
send location
send contact
send sticker
send gif
send emoji
send reaction
send typing indicator
send read receipt
send delivered receipt
send call request
send call response
send call end
send call reject
send call cancel
send call busy
send call hangup
send call answer
send call decline
send call accept
send call ignore


Here’s a detailed project outline and roadmap for your standalone webchat application:

---

### **Project Outline**

#### **1. Technology Stack**
- **Backend**: FastAPI
- **Frontend**: Jinja templates
- **Database**: PostgreSQL
- **Realtime Communication**: WebSockets (primary) and Server-Sent Events (SSE) (fallback)

#### **2. Features**
- **Core Features**:
  - User-to-user chat
  - Group chat
  - Send and receive messages
  - Display messages
  - Soft delete for messages
  - Save messages and user data (photos, etc.) in the database

- **Media and Interaction**:
  - Send images, files, audio, video, location, contact, stickers, GIFs, emojis
  - Send reactions, typing indicators, read receipts, and delivered receipts

- **Call Functionality**:
  - Call request, response, end, reject, cancel, busy, hangup, answer, decline, accept, ignore

#### **3. Database Design**
- **Tables**:
  - `users`: Store user information
  - `messages`: Store messages with soft delete functionality
  - `media`: Store media files (images, videos, etc.)
  - `groups`: Store group chat information
  - `group_members`: Store group membership details

#### **4. Example Folder**
- Use the example folder as a reference for UI/UX and functionality.

#### **5. Environment Configuration**
- Use a `.env` file to manage the database connection string and other environment variables.

---

### **Roadmap**

#### **Phase 1: Project Setup**
1. Initialize a FastAPI project.
2. Set up PostgreSQL database connection.
3. Configure `.env` file for environment variables.
4. Create the project structure:
   - Backend: API endpoints, WebSocket handlers, database models, and schemas.
   - Frontend: Jinja templates and static assets (CSS, JS, media).

#### **Phase 2: Database Design**
1. Define database models for `users`, `messages`, `media`, `groups`, and `group_members`.
2. Implement migrations using a tool like Alembic.

#### **Phase 3: Backend Development**
1. **API Endpoints**:
   - Create endpoints for sending, receiving, and retrieving messages.
   - Implement WebSocket and SSE handlers for real-time communication.
2. **Soft Delete**:
   - Add a `deleted` flag to the `messages` table for soft delete functionality.
3. **Media Handling**:
   - Implement file upload and storage for images, videos, and other media.

#### **Phase 4: Frontend Development**
1. Design Jinja templates for the chat interface.
2. Implement JavaScript for WebSocket and SSE communication.
3. Add support for sending and displaying media, reactions, and typing indicators.

#### **Phase 5: Testing**
1. Test WebSocket and SSE fallback functionality.
2. Test database queries and soft delete functionality.
3. Test media upload and retrieval.

#### **Phase 6: Deployment**
1. Deploy the application using a web server like Uvicorn or Gunicorn.
2. Set up a CI/CD pipeline for automated testing and deployment.

#### **Phase 7: Enhancements**
1. Add support for advanced features like call functionality.
2. Optimize database queries for performance.
3. Improve UI/UX based on user feedback.

---

This roadmap provides a clear path to building your standalone webchat application. Let me know if you'd like help with any specific phase!
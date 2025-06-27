# WebChat Multi-User Testing Guide

## 🎯 Quick Start

### 1. Start the Application
```bash
python main.py
```

### 2. Create Test Users
```bash
python create_test_users.py
```

### 3. Start Multi-User Testing
Open multiple browser windows with different users:

- **Window 1**: `http://localhost:8000/?user_id=1` (alice)
- **Window 2**: `http://localhost:8000/?user_id=2` (bob)  
- **Window 3**: `http://localhost:8000/?user_id=3` (charlie)

## 🔧 User Selection Methods

### Method 1: URL Parameters (Recommended for Testing)

**By User ID:**
```
http://localhost:8000/?user_id=1
http://localhost:8000/?user_id=2
http://localhost:8000/?user_id=3
```

**By Username:**
```
http://localhost:8000/?username=alice
http://localhost:8000/?username=bob
http://localhost:8000/?username=charlie
```

### Method 2: User Switcher Dropdown
1. Open `http://localhost:8000`
2. Use the dropdown in the top-right corner
3. Select different users to switch between them

### Method 3: Manual User Creation
1. Open `http://localhost:8000` 
2. Enter a new username when prompted
3. Start chatting

## 🧪 Testing Scenarios

### Real-Time Messaging
1. **Setup**: Open 2 browser windows with different users
2. **Test**: Send messages from one window
3. **Verify**: Messages appear instantly in the other window
4. **Check**: Typing indicators work properly

### File Sharing
1. **Setup**: Have a conversation open between two users
2. **Test**: Upload images, documents, or other files
3. **Verify**: Files appear in both windows with proper previews
4. **Check**: Download functionality works

### Group Chat
1. **Setup**: Create a group with multiple users
2. **Test**: Send messages in the group
3. **Verify**: All group members receive messages
4. **Check**: Group member list displays correctly

### Call Functionality
1. **Setup**: Open direct conversation between two users
2. **Test**: Click audio or video call button
3. **Verify**: Call request appears in other window
4. **Check**: Accept/decline buttons work

### User Status
1. **Setup**: Multiple users online
2. **Test**: Close one browser window
3. **Verify**: User shows as offline in other windows
4. **Check**: Last seen time updates

## 🔍 Advanced Testing

### Browser Console Testing
Open browser developer tools and test WebSocket connections:

```javascript
// Check WebSocket connection
console.log(window.chatApp.websocket.readyState);

// Send test message
window.chatApp.websocket.send(JSON.stringify({
    type: 'message',
    content: 'Test message',
    message_type: 'text',
    receiver_id: 2
}));
```

### API Testing with curl
Test the REST API directly:

```bash
# Create user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser"}'

# Send message
curl -X POST http://localhost:8000/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello", "receiver_id": 2, "message_type": "text"}'

# Upload file
curl -X POST http://localhost:8000/api/media/upload \
  -F "file=@test.jpg" \
  -F "user_id=1"
```

## 🐛 Troubleshooting

### Common Issues

**Messages not appearing in real-time:**
- Check browser console for WebSocket errors
- Verify both users are connected
- Try refreshing the page

**File uploads failing:**
- Check file size (max 10MB by default)
- Verify file type is allowed
- Check server logs for errors

**Users not showing online:**
- Ensure WebSocket connection is established
- Check if user switched properly
- Verify database connection

### Debug Mode
Enable debug logging by setting in `.env`:
```
DEBUG=True
```

### Browser Developer Tools
1. Open F12 Developer Tools
2. Go to Network tab
3. Filter by "WS" to see WebSocket traffic
4. Check Console for JavaScript errors

## 📊 Performance Testing

### Load Testing
Test with multiple users simultaneously:

1. Open 5+ browser windows with different users
2. Send messages rapidly between users
3. Upload files simultaneously
4. Monitor server performance

### Memory Testing
1. Keep application running for extended periods
2. Send hundreds of messages
3. Upload multiple files
4. Check for memory leaks

## 🎯 Test Checklist

### Basic Functionality
- [ ] User creation works
- [ ] User switching works
- [ ] Messages send and receive
- [ ] File uploads work
- [ ] Group chats function
- [ ] Call requests work

### Real-Time Features
- [ ] Messages appear instantly
- [ ] Typing indicators work
- [ ] Online status updates
- [ ] Notifications display
- [ ] WebSocket reconnection works

### UI/UX
- [ ] Theme switching works
- [ ] Responsive design functions
- [ ] Search functionality works
- [ ] Conversation list updates
- [ ] Error messages display

### Edge Cases
- [ ] Network disconnection handling
- [ ] Large file uploads
- [ ] Special characters in messages
- [ ] Empty messages handling
- [ ] Concurrent user actions

## 🚀 Production Testing

### Multi-Device Testing
1. Test on different devices (desktop, mobile, tablet)
2. Test on different browsers (Chrome, Firefox, Safari, Edge)
3. Test on different operating systems

### Network Conditions
1. Test on slow networks
2. Test with intermittent connectivity
3. Test WebSocket fallback to SSE

### Security Testing
1. Test file upload restrictions
2. Test message content filtering
3. Test user authentication (if implemented)

## 📝 Reporting Issues

When reporting issues, include:
1. Browser and version
2. Steps to reproduce
3. Expected vs actual behavior
4. Console errors (if any)
5. Network conditions
6. User IDs involved

## 🎉 Success Criteria

Your WebChat is working correctly if:
- ✅ Multiple users can chat in real-time
- ✅ Files upload and display properly
- ✅ Group chats work with multiple participants
- ✅ Call functionality initiates properly
- ✅ Users can switch between accounts seamlessly
- ✅ No console errors during normal operation
- ✅ WebSocket connections remain stable

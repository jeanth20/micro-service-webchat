// WebChat Application JavaScript
class WebChatApp {
    constructor() {
        this.currentUser = null;
        this.currentConversation = null;
        this.websocket = null;
        this.conversations = new Map();
        this.users = new Map();
        this.isConnected = false;
        this.typingTimeout = null;
        this.callManager = null;

        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupTheme();

        // Check URL parameters for user selection
        const urlParams = new URLSearchParams(window.location.search);
        const userIdParam = urlParams.get('user_id');
        const usernameParam = urlParams.get('username');

        if (userIdParam) {
            await this.loadUserById(parseInt(userIdParam));
        } else if (usernameParam) {
            await this.loadUserByUsername(usernameParam);
        } else {
            // Check if user exists in localStorage
            const savedUser = localStorage.getItem('webchat_user');
            if (savedUser) {
                this.currentUser = JSON.parse(savedUser);
                this.updateUserProfile();
                await this.loadConversations();
                this.connectWebSocket();
            } else {
                this.showUserSetupModal();
            }
        }

        // Initialize call manager
        if (window.WebRTCCallManager) {
            this.callManager = new window.WebRTCCallManager(this);
        }
    }

    setupEventListeners() {
        // User switcher
        const userSelect = document.getElementById('user-select');
        if (userSelect) {
            userSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.switchUser(parseInt(e.target.value));
                }
            });
        }

        // Theme toggle
        document.getElementById('theme-toggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // Settings button
        document.getElementById('settings-btn').addEventListener('click', () => {
            this.showSettingsModal();
        });

        // New chat button
        document.getElementById('new-chat-btn').addEventListener('click', () => {
            this.showNewChatModal();
        });

        // Message input
        const messageInput = document.getElementById('message-input');
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            } else {
                this.sendTypingIndicator(true);
            }
        });

        messageInput.addEventListener('input', () => {
            this.sendTypingIndicator(true);
        });

        messageInput.addEventListener('blur', () => {
            this.sendTypingIndicator(false);
        });

        // Send button
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendMessage();
        });

        // File upload buttons
        document.getElementById('file-upload-btn').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });

        document.getElementById('image-upload-btn').addEventListener('click', () => {
            document.getElementById('image-input').click();
        });

        // File input handlers
        document.getElementById('file-input').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        document.getElementById('image-input').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        // Location sharing button
        const locationBtn = document.getElementById('location-btn');
        if (locationBtn) {
            locationBtn.addEventListener('click', () => {
                this.shareLocation();
            });
        }

        // Emoji picker button
        const emojiBtn = document.getElementById('emoji-btn');
        if (emojiBtn) {
            emojiBtn.addEventListener('click', () => {
                this.toggleEmojiPicker();
            });
        }

        // User setup modal
        document.getElementById('create-user-btn').addEventListener('click', () => {
            this.createUser();
        });

        document.getElementById('username-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.createUser();
            }
        });

        // New chat modal
        document.getElementById('close-new-chat').addEventListener('click', () => {
            this.hideNewChatModal();
        });

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Search functionality
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.searchConversations(e.target.value);
        });

        document.getElementById('search-users').addEventListener('input', (e) => {
            this.searchUsers(e.target.value);
        });

        // Call buttons
        document.getElementById('audio-call-btn').addEventListener('click', () => {
            this.initiateCall('audio');
        });

        document.getElementById('video-call-btn').addEventListener('click', () => {
            this.initiateCall('video');
        });

        document.getElementById('video-call-detail-btn').addEventListener('click', () => {
            this.initiateCall('video');
        });

        // Settings modal
        document.getElementById('close-settings').addEventListener('click', () => {
            this.hideSettingsModal();
        });

        document.getElementById('save-settings-btn').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('cancel-settings-btn').addEventListener('click', () => {
            this.hideSettingsModal();
        });

        // Profile picture change
        document.getElementById('change-avatar-btn').addEventListener('click', () => {
            document.getElementById('avatar-input').click();
        });

        document.getElementById('avatar-input').addEventListener('change', (e) => {
            this.handleAvatarUpload(e.target.files[0]);
        });

        // Color theme selection in settings
        document.querySelectorAll('.color-option').forEach(color => {
            color.addEventListener('click', (e) => {
                this.selectColorTheme(e.target.dataset.color);
            });
        });

        // Theme mode selection
        document.getElementById('theme-mode').addEventListener('change', (e) => {
            this.setThemeMode(e.target.value);
        });

        // Close modals when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }

    setupTheme() {
        const savedTheme = localStorage.getItem('webchat_theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
            // Update color selection in settings if available
            setTimeout(() => {
                const colorOption = document.querySelector(`.color-option[data-color="${savedTheme}"]`);
                if (colorOption) {
                    document.querySelectorAll('.color-option').forEach(c => c.classList.remove('selected'));
                    colorOption.classList.add('selected');
                }
            }, 100);
        }

        const isDarkMode = localStorage.getItem('webchat_dark_mode') === 'true';
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
        }
    }

    toggleTheme() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('webchat_dark_mode', isDarkMode);
    }

    changeTheme(color) {
        // Update color options in settings modal if they exist
        const colorOptions = document.querySelectorAll('.color-option');
        if (colorOptions.length > 0) {
            colorOptions.forEach(c => c.classList.remove('selected'));
            const selectedOption = document.querySelector(`.color-option[data-color="${color}"]`);
            if (selectedOption) {
                selectedOption.classList.add('selected');
            }
        }

        // Update legacy color elements if they exist (for backward compatibility)
        const legacyColors = document.querySelectorAll('.color');
        if (legacyColors.length > 0) {
            legacyColors.forEach(c => c.classList.remove('selected'));
            const legacySelected = document.querySelector(`.color.${color}`);
            if (legacySelected) {
                legacySelected.classList.add('selected');
            }
        }

        document.documentElement.setAttribute('data-theme', color);
        localStorage.setItem('webchat_theme', color);
    }

    showUserSetupModal() {
        document.getElementById('user-setup-modal').style.display = 'block';
        document.getElementById('username-input').focus();
    }

    hideUserSetupModal() {
        document.getElementById('user-setup-modal').style.display = 'none';
    }

    showNewChatModal() {
        document.getElementById('new-chat-modal').style.display = 'block';
        this.loadUsersForChat();
    }

    hideNewChatModal() {
        document.getElementById('new-chat-modal').style.display = 'none';
    }

    async showSettingsModal() {
        document.getElementById('settings-modal').style.display = 'block';
        await this.loadUserPreferences();
    }

    hideSettingsModal() {
        document.getElementById('settings-modal').style.display = 'none';
    }

    async loadUserPreferences() {
        if (!this.currentUser) return;

        try {
            const response = await fetch(`/api/preferences/${this.currentUser.id}`);
            if (response.ok) {
                const preferences = await response.json();
                this.populateSettingsForm(preferences);
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    }

    populateSettingsForm(preferences) {
        try {
            // Set avatar
            const avatarElement = document.getElementById('settings-avatar');
            if (avatarElement) {
                avatarElement.src = this.currentUser.avatar_url || '/static/images/default-avatar.png';
            }

            // Set theme mode
            const themeModeElement = document.getElementById('theme-mode');
            if (themeModeElement) {
                themeModeElement.value = preferences.theme_mode || 'light';
            }

            // Set color theme
            document.querySelectorAll('.color-option').forEach(option => {
                option.classList.remove('selected');
            });
            const selectedColor = document.querySelector(`.color-option[data-color="${preferences.color_theme || 'blue'}"]`);
            if (selectedColor) {
                selectedColor.classList.add('selected');
            }

            // Set toggles
            const notificationsElement = document.getElementById('notifications-enabled');
            if (notificationsElement) {
                notificationsElement.checked = preferences.notifications_enabled !== false;
            }

            const soundElement = document.getElementById('sound-enabled');
            if (soundElement) {
                soundElement.checked = preferences.sound_enabled !== false;
            }

            const onlineStatusElement = document.getElementById('show-online-status');
            if (onlineStatusElement) {
                onlineStatusElement.checked = preferences.show_online_status !== false;
            }

            const autoDownloadElement = document.getElementById('auto-download-media');
            if (autoDownloadElement) {
                autoDownloadElement.checked = preferences.auto_download_media !== false;
            }

            console.log('Settings form populated with preferences:', preferences);
        } catch (error) {
            console.error('Error populating settings form:', error);
        }
    }

    selectColorTheme(color) {
        document.querySelectorAll('.color-option').forEach(option => {
            option.classList.remove('selected');
        });
        document.querySelector(`.color-option[data-color="${color}"]`).classList.add('selected');
    }

    setThemeMode(mode) {
        if (mode === 'dark') {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }

    async handleAvatarUpload(file) {
        if (!file || !this.currentUser) return;

        console.log('Uploading avatar for user:', this.currentUser.id);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', this.currentUser.id.toString());

        try {
            const response = await fetch('/api/media/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const media = await response.json();
                const avatarUrl = `/api/media/${media.id}/view`;

                // Update user avatar
                await this.updateUserAvatar(avatarUrl);

                // Update UI
                document.getElementById('settings-avatar').src = avatarUrl;
                document.getElementById('current-user-avatar').src = avatarUrl;

                this.showNotification('Profile picture updated successfully!', 'success');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }
        } catch (error) {
            console.error('Error uploading avatar:', error);
            this.showNotification('Failed to upload avatar: ' + error.message, 'error');
        }
    }

    async updateUserAvatar(avatarUrl) {
        try {
            const response = await fetch(`/api/users/${this.currentUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    avatar_url: avatarUrl
                })
            });

            if (response.ok) {
                this.currentUser.avatar_url = avatarUrl;
                localStorage.setItem('webchat_user', JSON.stringify(this.currentUser));
            }
        } catch (error) {
            console.error('Error updating user avatar:', error);
        }
    }

    async saveSettings() {
        if (!this.currentUser) {
            this.showNotification('No user selected', 'error');
            return;
        }

        try {
            const selectedColor = document.querySelector('.color-option.selected');
            const themeMode = document.getElementById('theme-mode');
            const notificationsEnabled = document.getElementById('notifications-enabled');
            const soundEnabled = document.getElementById('sound-enabled');
            const showOnlineStatus = document.getElementById('show-online-status');
            const autoDownloadMedia = document.getElementById('auto-download-media');

            // Validate that all elements exist
            if (!themeMode || !notificationsEnabled || !soundEnabled || !showOnlineStatus || !autoDownloadMedia) {
                throw new Error('Settings form elements not found');
            }

            const preferences = {
                theme_mode: themeMode.value,
                color_theme: selectedColor ? selectedColor.dataset.color : 'blue',
                notifications_enabled: notificationsEnabled.checked,
                sound_enabled: soundEnabled.checked,
                show_online_status: showOnlineStatus.checked,
                auto_download_media: autoDownloadMedia.checked
            };

            console.log('Saving preferences:', preferences);

            const response = await fetch(`/api/preferences/${this.currentUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(preferences)
            });

            if (response.ok) {
                const savedPreferences = await response.json();
                console.log('Preferences saved:', savedPreferences);

                // Apply theme changes
                this.setThemeMode(preferences.theme_mode);
                this.changeTheme(preferences.color_theme);

                // Save to localStorage
                localStorage.setItem('webchat_dark_mode', preferences.theme_mode === 'dark');
                localStorage.setItem('webchat_theme', preferences.color_theme);

                this.hideSettingsModal();
                this.showNotification('Settings saved successfully!', 'success');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showNotification('Failed to save settings: ' + error.message, 'error');
        }
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    async createUser() {
        const username = document.getElementById('username-input').value.trim();
        if (!username) {
            alert('Please enter a username');
            return;
        }

        try {
            const response = await fetch('/api/users/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    avatar_url: '/static/images/default-avatar.png'
                })
            });

            if (response.ok) {
                this.currentUser = await response.json();
                localStorage.setItem('webchat_user', JSON.stringify(this.currentUser));
                this.hideUserSetupModal();
                this.updateUserProfile();
                await this.loadConversations();
                this.connectWebSocket();
            } else {
                const error = await response.json();
                alert(error.detail || 'Error creating user');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            alert('Error creating user');
        }
    }

    updateUserProfile() {
        if (this.currentUser) {
            document.getElementById('current-user-avatar').src = this.currentUser.avatar_url || '/static/images/default-avatar.png';

            // Update user selector
            const userSelect = document.getElementById('user-select');
            if (userSelect) {
                userSelect.value = this.currentUser.id;
            }

            // Update page title
            document.title = `WebChat - ${this.currentUser.username}`;
        }
    }

    async loadUserById(userId) {
        try {
            const response = await fetch(`/api/users/${userId}`);
            if (response.ok) {
                this.currentUser = await response.json();
                localStorage.setItem('webchat_user', JSON.stringify(this.currentUser));
                this.updateUserProfile();
                await this.loadConversations();
                this.connectWebSocket();
                return true;
            } else {
                console.error('User not found');
                this.showUserSetupModal();
                return false;
            }
        } catch (error) {
            console.error('Error loading user:', error);
            this.showUserSetupModal();
            return false;
        }
    }

    async loadUserByUsername(username) {
        try {
            const response = await fetch(`/api/users/username/${username}`);
            if (response.ok) {
                this.currentUser = await response.json();
                localStorage.setItem('webchat_user', JSON.stringify(this.currentUser));
                this.updateUserProfile();
                await this.loadConversations();
                this.connectWebSocket();
                return true;
            } else {
                console.error('User not found');
                this.showUserSetupModal();
                return false;
            }
        } catch (error) {
            console.error('Error loading user:', error);
            this.showUserSetupModal();
            return false;
        }
    }

    async switchUser(userId) {
        // Disconnect current WebSocket
        if (this.websocket) {
            this.websocket.close();
        }

        // Clear current data
        this.conversations.clear();
        this.users.clear();
        this.currentConversation = null;

        // Load new user
        await this.loadUserById(userId);

        // Update URL without page reload
        const url = new URL(window.location);
        url.searchParams.set('user_id', userId);
        window.history.pushState({}, '', url);

        // Clear chat area
        document.getElementById('chat-messages').innerHTML = '<div class="welcome-message"><h3>Welcome to WebChat!</h3><p>Select a conversation to start chatting</p></div>';
        document.getElementById('chat-footer').style.display = 'none';

        this.showInAppNotification(`Switched to user: ${this.currentUser.username}`, 'success');
    }

    connectWebSocket() {
        if (!this.currentUser) {
            console.log('No current user, cannot connect WebSocket');
            return;
        }

        // Close existing connection if any
        if (this.websocket) {
            this.websocket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.currentUser.id}`;

        console.log('Connecting WebSocket to:', wsUrl);
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('WebSocket connected successfully');
            this.isConnected = true;
            this.updateOnlineStatus(true);
            this.showInAppNotification('Connected to chat server', 'success');
        };

        this.websocket.onmessage = (event) => {
            console.log('WebSocket message received:', event.data);
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.websocket.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.isConnected = false;
            this.updateOnlineStatus(false);

            // Only attempt to reconnect if it wasn't a manual close
            if (event.code !== 1000) {
                this.showInAppNotification('Connection lost, reconnecting...', 'error');
                setTimeout(() => {
                    if (!this.isConnected && this.currentUser) {
                        console.log('Attempting to reconnect WebSocket...');
                        this.connectWebSocket();
                    }
                }, 3000);
            }
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showInAppNotification('Connection error', 'error');
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'message':
                this.handleIncomingMessage(data.message);
                break;
            case 'typing':
                this.handleTypingIndicator(data);
                break;
            case 'call':
                this.handleCallMessage(data);
                break;
            case 'webrtc-signal':
                this.handleWebRTCSignal(data);
                break;
            case 'reaction_update':
                this.handleReactionUpdate(data);
                break;
            case 'error':
                this.handleError(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleError(data) {
        console.error('WebSocket error:', data);
        // Show user-friendly error message
        this.showNotification('Error: ' + data.message, 'error');
    }

    async updateOnlineStatus(isOnline) {
        if (!this.currentUser) return;

        try {
            await fetch(`/api/users/${this.currentUser.id}/online-status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ is_online: isOnline })
            });
        } catch (error) {
            console.error('Error updating online status:', error);
        }
    }

    async loadConversations() {
        try {
            // Load direct messages
            const messagesResponse = await fetch(`/api/messages/?user_id=${this.currentUser.id}`);
            const messages = await messagesResponse.json();
            
            // Load user's groups
            const groupsResponse = await fetch(`/api/groups/user/${this.currentUser.id}`);
            const groups = await groupsResponse.json();
            
            this.processConversations(messages, groups);
            this.renderConversations();
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }

    processConversations(messages, groups) {
        // Process direct messages
        const directConversations = new Map();
        
        messages.forEach(message => {
            if (message.receiver_id || message.sender_id) {
                const otherUserId = message.sender_id === this.currentUser.id ? 
                    message.receiver_id : message.sender_id;
                
                if (!directConversations.has(otherUserId)) {
                    directConversations.set(otherUserId, {
                        type: 'direct',
                        userId: otherUserId,
                        lastMessage: message,
                        unreadCount: 0
                    });
                } else {
                    const conv = directConversations.get(otherUserId);
                    if (new Date(message.created_at) > new Date(conv.lastMessage.created_at)) {
                        conv.lastMessage = message;
                    }
                }
                
                // Count unread messages
                if (message.receiver_id === this.currentUser.id && !message.is_read) {
                    directConversations.get(otherUserId).unreadCount++;
                }
            }
        });
        
        // Process group conversations
        groups.forEach(group => {
            this.conversations.set(`group_${group.id}`, {
                type: 'group',
                group: group,
                lastMessage: null,
                unreadCount: 0
            });
        });
        
        // Merge direct conversations
        directConversations.forEach((conv, userId) => {
            this.conversations.set(`user_${userId}`, conv);
        });
    }

    async renderConversations() {
        const conversationsList = document.getElementById('conversations-list');
        conversationsList.innerHTML = '';

        for (const [key, conversation] of this.conversations) {
            const conversationElement = await this.createConversationElement(key, conversation);
            conversationsList.appendChild(conversationElement);
        }
    }

    async createConversationElement(key, conversation) {
        const div = document.createElement('div');
        div.className = 'msg';
        div.dataset.conversationId = key;

        let avatarUrl, name, lastMessageText, isOnline = false;

        if (conversation.type === 'direct') {
            // Get user info
            try {
                const userResponse = await fetch(`/api/users/${conversation.userId}`);
                const user = await userResponse.json();
                avatarUrl = user.avatar_url || '/static/images/default-avatar.png';
                name = user.username;
                isOnline = user.is_online;
                this.users.set(conversation.userId, user);
            } catch (error) {
                console.error('Error loading user:', error);
                avatarUrl = '/static/images/default-avatar.png';
                name = 'Unknown User';
            }
        } else {
            avatarUrl = conversation.group.avatar_url;
            name = conversation.group.name;
        }

        lastMessageText = conversation.lastMessage ?
            conversation.lastMessage.content || 'Media message' :
            'No messages yet';

        const timeAgo = conversation.lastMessage ?
            this.formatTimeAgo(conversation.lastMessage.created_at) : '';

        div.innerHTML = `
            ${conversation.type === 'direct' ?
                `<img class="msg-profile" src="${avatarUrl}" alt="${name}" />` :
                `<div class="msg-profile group">
                    <svg viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2l10 6.5v7L12 22 2 15.5v-7L12 2zM12 22v-6.5" />
                        <path d="M22 8.5l-10 7-10-7" />
                        <path d="M2 15.5l10-7 10 7M12 2v6.5" />
                    </svg>
                </div>`
            }
            <div class="msg-detail">
                <div class="msg-username">${name}</div>
                <div class="msg-content">
                    <span class="msg-message">${lastMessageText}</span>
                    ${timeAgo ? `<span class="msg-date">${timeAgo}</span>` : ''}
                </div>
            </div>
        `;

        if (isOnline && conversation.type === 'direct') {
            div.classList.add('online');
        }

        if (conversation.unreadCount > 0) {
            div.classList.add('unread');
        }

        div.addEventListener('click', () => {
            this.selectConversation(key, conversation);
        });

        return div;
    }

    async selectConversation(key, conversation) {
        // Remove active class from all conversations
        document.querySelectorAll('.msg').forEach(msg => msg.classList.remove('active'));

        // Add active class to selected conversation
        document.querySelector(`[data-conversation-id="${key}"]`).classList.add('active');

        this.currentConversation = { key, ...conversation };

        // Update chat header
        await this.updateChatHeader();

        // Load and display messages
        await this.loadMessages();

        // Show chat footer
        document.getElementById('chat-footer').style.display = 'flex';

        // Focus message input
        document.getElementById('message-input').focus();
    }

    async updateChatHeader() {
        const chatTitle = document.getElementById('chat-title');
        const chatParticipants = document.getElementById('chat-participants');

        if (this.currentConversation.type === 'direct') {
            const user = this.users.get(this.currentConversation.userId);
            chatTitle.textContent = user ? user.username : 'Unknown User';
            chatParticipants.style.display = 'none';
        } else {
            chatTitle.textContent = this.currentConversation.group.name;
            chatParticipants.style.display = 'flex';

            // Load group members
            try {
                const response = await fetch(`/api/groups/${this.currentConversation.group.id}/members`);
                const members = await response.json();

                chatParticipants.innerHTML = '';
                members.slice(0, 3).forEach(async (member) => {
                    const userResponse = await fetch(`/api/users/${member.user_id}`);
                    const user = await userResponse.json();

                    const img = document.createElement('img');
                    img.className = 'chat-area-profile';
                    img.src = user.avatar_url || '/static/images/default-avatar.png';
                    img.alt = user.username;
                    chatParticipants.appendChild(img);
                });

                if (members.length > 3) {
                    const span = document.createElement('span');
                    span.textContent = `+${members.length - 3}`;
                    chatParticipants.appendChild(span);
                }
            } catch (error) {
                console.error('Error loading group members:', error);
            }
        }
    }

    async loadMessages() {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';

        try {
            let messagesUrl;
            if (this.currentConversation.type === 'direct') {
                messagesUrl = `/api/messages/conversation/${this.currentUser.id}/${this.currentConversation.userId}`;
            } else {
                messagesUrl = `/api/messages/group/${this.currentConversation.group.id}`;
            }

            console.log('Loading messages from:', messagesUrl);
            const response = await fetch(messagesUrl);
            const messages = await response.json();

            console.log('Loaded messages:', messages.length);

            // Sort messages by creation time
            messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

            messages.forEach(message => {
                this.displayMessage(message);
            });

            // Force scroll to bottom after all messages are loaded
            setTimeout(() => {
                this.scrollToBottom();
            }, 100);

        } catch (error) {
            console.error('Error loading messages:', error);
            chatMessages.innerHTML = '<div class="welcome-message"><h3>Error loading messages</h3><p>Please try refreshing the page</p></div>';
        }
    }

    displayMessage(message) {
        const chatMessages = document.getElementById('chat-messages');

        // Remove welcome message if it exists
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Check if message already exists (avoid duplicates)
        const existingMessage = chatMessages.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMessage && !message.is_temp) {
            return; // Don't add duplicate messages
        }

        const messageElement = this.createMessageElement(message);
        chatMessages.appendChild(messageElement);

        // Auto-scroll to bottom
        this.scrollToBottom();
    }

    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = 'chat-msg';

        const isOwner = message.sender_id === this.currentUser.id;
        if (isOwner) {
            div.classList.add('owner');
        }

        // Add message identifier
        if (message.is_temp) {
            div.setAttribute('data-temp-id', message.id);
        } else {
            div.setAttribute('data-message-id', message.id);
        }

        const user = this.users.get(message.sender_id) || {
            username: 'Unknown',
            avatar_url: '/static/images/default-avatar.png'
        };

        const timeFormatted = this.formatMessageTime(message.created_at);

        div.innerHTML = `
            <div class="chat-msg-profile">
                <img class="chat-msg-img" src="${user.avatar_url}" alt="${user.username}" />
                <div class="chat-msg-date">${timeFormatted}</div>
            </div>
            <div class="chat-msg-content">
                <div class="chat-msg-text">${this.formatMessageContent(message)}</div>
                <div class="chat-msg-actions">
                    <button class="reaction-btn" onclick="window.chatApp.showReactionPicker(${message.id})">😊</button>
                </div>
            </div>
        `;

        return div;
    }

    formatMessageContent(message) {
        if (message.message_type === 'text') {
            return this.escapeHtml(message.content);
        } else if (message.message_type === 'image') {
            return `<img src="/api/media/${message.media_id}/view" alt="Image" style="max-width: 300px; border-radius: 10px;" />`;
        } else if (message.message_type === 'location') {
            try {
                const locationData = JSON.parse(message.content);
                const { latitude, longitude } = locationData;
                const mapUrl = `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}&zoom=15`;
                const googleMapsUrl = `https://www.google.com/maps?q=${latitude},${longitude}`;
                return `
                    <div class="location-message">
                        <div class="location-icon">📍</div>
                        <div class="location-content">
                            <div class="location-title">Location Shared</div>
                            <div class="location-coords">Lat: ${latitude.toFixed(6)}, Lng: ${longitude.toFixed(6)}</div>
                            <div class="location-links">
                                <a href="${googleMapsUrl}" target="_blank" class="location-link">View in Google Maps</a>
                                <a href="${mapUrl}" target="_blank" class="location-link">View in OpenStreetMap</a>
                            </div>
                        </div>
                    </div>
                `;
            } catch (e) {
                return '📍 Location (invalid data)';
            }
        } else if (message.message_type === 'audio') {
            return `<audio controls style="max-width: 300px;"><source src="/api/media/${message.media_id}/view" type="audio/mpeg">Your browser does not support the audio element.</audio>`;
        } else if (message.message_type === 'video') {
            return `<video controls style="max-width: 300px; max-height: 200px;"><source src="/api/media/${message.media_id}/view" type="video/mp4">Your browser does not support the video element.</video>`;
        } else if (message.media_id) {
            return `<a href="/api/media/${message.media_id}/download" target="_blank">📎 ${message.content || 'File'}</a>`;
        }
        return message.content || '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInMinutes = Math.floor((now - date) / (1000 * 60));

        if (diffInMinutes < 1) return 'now';
        if (diffInMinutes < 60) return `${diffInMinutes}m`;
        if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`;
        return `${Math.floor(diffInMinutes / 1440)}d`;
    }

    formatMessageTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const content = messageInput.value.trim();

        if (!content || !this.currentConversation) return;

        const messageData = {
            type: 'message',
            content: content,
            message_type: 'text'
        };

        if (this.currentConversation.type === 'direct') {
            messageData.receiver_id = this.currentConversation.userId;
        } else {
            messageData.group_id = this.currentConversation.group.id;
        }

        // Clear input immediately for better UX
        messageInput.value = '';

        // Create temporary message for immediate display
        const tempMessage = {
            id: 'temp_' + Date.now() + '_' + Math.random(),
            sender_id: this.currentUser.id,
            receiver_id: messageData.receiver_id,
            group_id: messageData.group_id,
            content: content,
            message_type: 'text',
            created_at: new Date().toISOString(),
            is_temp: true
        };

        // Display message immediately
        this.displayMessage(tempMessage);
        this.scrollToBottom();

        // Send via WebSocket (primary method)
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            console.log('Sending message via WebSocket:', messageData);
            this.websocket.send(JSON.stringify(messageData));
        } else {
            console.log('WebSocket not available, using API fallback');
            // Fallback to API if WebSocket is not available
            try {
                const response = await fetch('/api/messages/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(messageData)
                });

                if (response.ok) {
                    const message = await response.json();
                    // Replace temporary message with real one
                    this.replaceTempMessage(tempMessage.id, message);
                    this.scrollToBottom();
                } else {
                    // Remove temp message on error
                    this.removeTempMessage(tempMessage.id);
                    this.showNotification('Failed to send message', 'error');
                }
            } catch (error) {
                console.error('Error sending message:', error);
                this.removeTempMessage(tempMessage.id);
                this.showNotification('Failed to send message', 'error');
            }
        }
    }

    handleIncomingMessage(message) {
        console.log('Incoming message:', message);

        // Load user info if we don't have it
        if (!this.users.has(message.sender_id)) {
            this.loadUserInfo(message.sender_id);
        }

        // Check if this message belongs to current conversation
        const isCurrentConversation =
            (this.currentConversation?.type === 'direct' &&
             ((message.sender_id === this.currentConversation.userId && message.receiver_id === this.currentUser.id) ||
              (message.receiver_id === this.currentConversation.userId && message.sender_id === this.currentUser.id))) ||
            (this.currentConversation?.type === 'group' &&
             message.group_id === this.currentConversation.group.id);

        console.log('Is current conversation:', isCurrentConversation);
        console.log('Current conversation:', this.currentConversation);

        if (isCurrentConversation) {
            // Remove any temporary message with same content from same sender
            if (message.sender_id === this.currentUser.id) {
                this.removeTempMessageByContent(message.content);
            }

            // Check if message already exists to avoid duplicates
            const existingMessage = document.querySelector(`[data-message-id="${message.id}"]`);
            if (!existingMessage) {
                // Display the message
                this.displayMessage(message);

                // Force scroll to bottom
                this.scrollToBottom();
            }

            // Mark as delivered if not our own message
            if (message.sender_id !== this.currentUser.id) {
                this.markMessageAsDelivered(message.id);
            }
        }

        // Update conversation list
        this.updateConversationList(message);

        // Show notification if not current conversation and not our own message
        if (!isCurrentConversation && message.sender_id !== this.currentUser.id) {
            this.showNotification(message);
        }
    }

    async loadUserInfo(userId) {
        try {
            const response = await fetch(`/api/users/${userId}`);
            if (response.ok) {
                const user = await response.json();
                this.users.set(userId, user);
            }
        } catch (error) {
            console.error('Error loading user info:', error);
        }
    }

    replaceTempMessage(tempId, realMessage) {
        const tempElement = document.querySelector(`[data-temp-id="${tempId}"]`);
        if (tempElement) {
            tempElement.remove();
            this.displayMessage(realMessage);
        }
    }

    removeTempMessage(tempId) {
        const tempElement = document.querySelector(`[data-temp-id="${tempId}"]`);
        if (tempElement) {
            tempElement.remove();
        }
    }

    removeTempMessageByContent(content) {
        const tempElements = document.querySelectorAll('[data-temp-id]');
        tempElements.forEach(element => {
            const messageText = element.querySelector('.chat-msg-text');
            if (messageText && messageText.textContent.trim() === content.trim()) {
                element.remove();
            }
        });
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            // Use setTimeout to ensure DOM is updated
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 10);
        }
    }

    async markMessageAsDelivered(messageId) {
        try {
            await fetch(`/api/messages/${messageId}/delivered`, {
                method: 'PUT'
            });
        } catch (error) {
            console.error('Error marking message as delivered:', error);
        }
    }

    updateConversationList(message) {
        // Update the conversation in the list with new message
        // This would involve updating the last message and timestamp
        // For now, we'll reload conversations
        this.loadConversations();
    }

    showNotification(message, type = 'info') {
        // Browser notification for messages
        if (typeof message === 'object' && message.content) {
            if (Notification.permission === 'granted') {
                const sender = this.users.get(message.sender_id) || { username: 'Unknown User' };
                new Notification(`New message from ${sender.username}`, {
                    body: message.content || 'New message received',
                    icon: '/static/images/default-avatar.png'
                });
            }
        } else {
            // In-app notification
            this.showInAppNotification(message, type);
        }
    }

    showInAppNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;

        // Add to page
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    sendTypingIndicator(isTyping) {
        if (!this.currentConversation || !this.websocket ||
            this.websocket.readyState !== WebSocket.OPEN) return;

        // Clear existing timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }

        const typingData = {
            type: 'typing',
            is_typing: isTyping
        };

        if (this.currentConversation.type === 'direct') {
            typingData.receiver_id = this.currentConversation.userId;
        } else {
            typingData.group_id = this.currentConversation.group.id;
        }

        this.websocket.send(JSON.stringify(typingData));

        // Auto-stop typing after 3 seconds
        if (isTyping) {
            this.typingTimeout = setTimeout(() => {
                this.sendTypingIndicator(false);
            }, 3000);
        }
    }

    handleTypingIndicator(data) {
        // Show/hide typing indicator
        const isCurrentConversation =
            (this.currentConversation?.type === 'direct' &&
             data.user_id === this.currentConversation.userId) ||
            (this.currentConversation?.type === 'group' &&
             data.group_id === this.currentConversation.group.id);

        if (isCurrentConversation) {
            this.showTypingIndicator(data.user_id, data.is_typing);
        }
    }

    showTypingIndicator(userId, isTyping) {
        const chatMessages = document.getElementById('chat-messages');
        const existingIndicator = chatMessages.querySelector('.typing-indicator');

        if (isTyping) {
            if (!existingIndicator) {
                const user = this.users.get(userId) || { username: 'Someone' };
                const indicator = document.createElement('div');
                indicator.className = 'typing-indicator';
                indicator.innerHTML = `
                    ${user.username} is typing
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
                chatMessages.appendChild(indicator);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        } else {
            if (existingIndicator) {
                existingIndicator.remove();
            }
        }
    }

    async handleFileUpload(files) {
        if (!files.length || !this.currentConversation) return;

        for (const file of files) {
            // Show upload progress
            const progressId = this.showUploadProgress(file.name);

            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('user_id', this.currentUser.id);

                const response = await fetch('/api/media/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const media = await response.json();

                    // Hide upload progress
                    this.hideUploadProgress(progressId);

                    // Send message with media via WebSocket
                    const messageData = {
                        type: 'message',
                        content: file.name,
                        message_type: media.file_type,
                        media_id: media.id
                    };

                    if (this.currentConversation.type === 'direct') {
                        messageData.receiver_id = this.currentConversation.userId;
                    } else {
                        messageData.group_id = this.currentConversation.group.id;
                    }

                    // Create temporary message for immediate display
                    const tempMessage = {
                        id: 'temp_' + Date.now(),
                        sender_id: this.currentUser.id,
                        receiver_id: messageData.receiver_id,
                        group_id: messageData.group_id,
                        content: file.name,
                        message_type: media.file_type,
                        media_id: media.id,
                        created_at: new Date().toISOString(),
                        is_temp: true
                    };

                    // Display message immediately
                    this.displayMessage(tempMessage);

                    // Send via WebSocket
                    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                        this.websocket.send(JSON.stringify(messageData));
                    } else {
                        // Fallback to API
                        const messageResponse = await fetch('/api/messages/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                content: file.name,
                                message_type: media.file_type,
                                media_id: media.id,
                                receiver_id: messageData.receiver_id,
                                group_id: messageData.group_id
                            })
                        });

                        if (messageResponse.ok) {
                            const message = await messageResponse.json();
                            this.replaceTempMessage(tempMessage.id, message);
                        } else {
                            this.removeTempMessage(tempMessage.id);
                            this.showNotification('Failed to send file', 'error');
                        }
                    }
                } else {
                    this.hideUploadProgress(progressId);
                    const errorData = await response.json();
                    this.showNotification(`Upload failed: ${errorData.detail}`, 'error');
                }
            } catch (error) {
                console.error('Error uploading file:', error);
                this.hideUploadProgress(progressId);
                this.showNotification('Error uploading file', 'error');
            }
        }
    }

    showUploadProgress(filename) {
        const progressId = 'upload_' + Date.now();
        const chatMessages = document.getElementById('chat-messages');

        const progressElement = document.createElement('div');
        progressElement.id = progressId;
        progressElement.className = 'upload-progress';
        progressElement.innerHTML = `
            <div class="upload-info">
                <span>Uploading ${filename}...</span>
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
        `;

        chatMessages.appendChild(progressElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return progressId;
    }

    hideUploadProgress(progressId) {
        const element = document.getElementById(progressId);
        if (element) {
            element.remove();
        }
    }

    async loadUsersForChat() {
        try {
            const response = await fetch('/api/users/');
            const users = await response.json();

            const usersList = document.getElementById('users-list');
            usersList.innerHTML = '';

            users.filter(user => user.id !== this.currentUser.id).forEach(user => {
                const userElement = document.createElement('div');
                userElement.className = 'user-item';
                userElement.innerHTML = `
                    <img src="${user.avatar_url || '/static/images/default-avatar.png'}" alt="${user.username}" />
                    <span>${user.username}</span>
                `;

                userElement.addEventListener('click', () => {
                    this.startDirectChat(user);
                });

                usersList.appendChild(userElement);
            });
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    startDirectChat(user) {
        this.hideNewChatModal();

        // Check if conversation already exists
        const existingKey = `user_${user.id}`;
        if (this.conversations.has(existingKey)) {
            this.selectConversation(existingKey, this.conversations.get(existingKey));
        } else {
            // Create new conversation
            const conversation = {
                type: 'direct',
                userId: user.id,
                lastMessage: null,
                unreadCount: 0
            };

            this.conversations.set(existingKey, conversation);
            this.users.set(user.id, user);
            this.renderConversations();
            this.selectConversation(existingKey, conversation);
        }
    }

    async initiateCall(type) {
        if (!this.currentConversation) {
            this.showNotification('Please select a conversation first', 'error');
            return;
        }

        if (this.currentConversation.type !== 'direct') {
            this.showNotification('Group calls are not supported yet', 'error');
            return;
        }

        if (!this.callManager) {
            this.showNotification('Call functionality not available', 'error');
            return;
        }

        // Use WebRTC call manager
        await this.callManager.initiateCall(type, this.currentConversation.userId);
    }

    handleCallMessage(callData) {
        console.log('Call message received:', callData);

        if (this.callManager) {
            this.callManager.handleCallMessage(callData);
        } else {
            console.log('Call manager not available');
        }
    }

    handleWebRTCSignal(signalData) {
        console.log('WebRTC signal received:', signalData);

        if (this.callManager) {
            this.callManager.handleWebRTCSignal(signalData);
        } else {
            console.log('Call manager not available for WebRTC signal');
        }
    }



    searchConversations(query) {
        const conversations = document.querySelectorAll('.msg');
        conversations.forEach(conv => {
            const username = conv.querySelector('.msg-username').textContent.toLowerCase();
            const message = conv.querySelector('.msg-message').textContent.toLowerCase();

            if (username.includes(query.toLowerCase()) || message.includes(query.toLowerCase())) {
                conv.style.display = 'flex';
            } else {
                conv.style.display = 'none';
            }
        });
    }

    searchUsers(query) {
        const users = document.querySelectorAll('.user-item');
        users.forEach(user => {
            const username = user.textContent.toLowerCase();
            if (username.includes(query.toLowerCase())) {
                user.style.display = 'flex';
            } else {
                user.style.display = 'none';
            }
        });
    }

    async shareLocation() {
        if (!this.currentConversation) {
            this.showInAppNotification('Please select a conversation first', 'error');
            return;
        }

        if (!navigator.geolocation) {
            this.showInAppNotification('Geolocation is not supported by this browser', 'error');
            return;
        }

        this.showInAppNotification('Getting your location...', 'info');

        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                });
            });

            const { latitude, longitude } = position.coords;
            const locationData = {
                latitude,
                longitude,
                accuracy: position.coords.accuracy
            };

            const messageData = {
                type: 'message',
                content: JSON.stringify(locationData),
                message_type: 'location'
            };

            if (this.currentConversation.type === 'direct') {
                messageData.receiver_id = this.currentConversation.userId;
            } else {
                messageData.group_id = this.currentConversation.group.id;
            }

            // Send via WebSocket
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify(messageData));
                this.showInAppNotification('Location shared successfully!', 'success');
            } else {
                this.showInAppNotification('Unable to send location. Please try again.', 'error');
            }

        } catch (error) {
            console.error('Error getting location:', error);
            let errorMessage = 'Failed to get location';

            if (error.code === error.PERMISSION_DENIED) {
                errorMessage = 'Location access denied. Please enable location permissions.';
            } else if (error.code === error.POSITION_UNAVAILABLE) {
                errorMessage = 'Location information is unavailable.';
            } else if (error.code === error.TIMEOUT) {
                errorMessage = 'Location request timed out.';
            }

            this.showInAppNotification(errorMessage, 'error');
        }
    }

    toggleEmojiPicker() {
        let emojiPicker = document.getElementById('emoji-picker');

        if (!emojiPicker) {
            emojiPicker = this.createEmojiPicker();
            document.body.appendChild(emojiPicker);
        }

        if (emojiPicker.style.display === 'none' || !emojiPicker.style.display) {
            emojiPicker.style.display = 'block';
        } else {
            emojiPicker.style.display = 'none';
        }
    }

    createEmojiPicker() {
        const picker = document.createElement('div');
        picker.id = 'emoji-picker';
        picker.className = 'emoji-picker';

        const emojis = [
            '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇',
            '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚',
            '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩',
            '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣',
            '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬',
            '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗',
            '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯',
            '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐',
            '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈',
            '👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉',
            '👆', '🖕', '👇', '☝️', '👋', '🤚', '🖐️', '✋', '🖖', '👏',
            '🙌', '🤲', '🤝', '🙏', '✍️', '💪', '🦾', '🦿', '🦵', '🦶',
            '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔',
            '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️',
            '✝️', '☪️', '🕉️', '☸️', '✡️', '🔯', '🕎', '☯️', '☦️', '🛐'
        ];

        picker.innerHTML = `
            <div class="emoji-picker-header">
                <span>Choose an emoji</span>
                <button class="emoji-picker-close" onclick="document.getElementById('emoji-picker').style.display='none'">×</button>
            </div>
            <div class="emoji-picker-content">
                ${emojis.map(emoji => `<span class="emoji-item" onclick="window.chatApp.insertEmoji('${emoji}')">${emoji}</span>`).join('')}
            </div>
        `;

        return picker;
    }

    insertEmoji(emoji) {
        const messageInput = document.getElementById('message-input');
        const currentValue = messageInput.value;
        const cursorPosition = messageInput.selectionStart;

        const newValue = currentValue.slice(0, cursorPosition) + emoji + currentValue.slice(cursorPosition);
        messageInput.value = newValue;

        // Set cursor position after the emoji
        messageInput.setSelectionRange(cursorPosition + emoji.length, cursorPosition + emoji.length);
        messageInput.focus();

        // Hide emoji picker
        document.getElementById('emoji-picker').style.display = 'none';
    }

    showReactionPicker(messageId) {
        let reactionPicker = document.getElementById('reaction-picker');

        if (!reactionPicker) {
            reactionPicker = this.createReactionPicker();
            document.body.appendChild(reactionPicker);
        }

        reactionPicker.dataset.messageId = messageId;
        reactionPicker.style.display = 'block';

        // Position the picker near the message
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageElement) {
            const rect = messageElement.getBoundingClientRect();
            reactionPicker.style.top = `${rect.top - 60}px`;
            reactionPicker.style.left = `${rect.left + 50}px`;
        }
    }

    createReactionPicker() {
        const picker = document.createElement('div');
        picker.id = 'reaction-picker';
        picker.className = 'reaction-picker';

        const reactions = ['👍', '❤️', '😂', '😮', '😢', '😡'];

        picker.innerHTML = `
            <div class="reaction-picker-content">
                ${reactions.map(reaction => `<span class="reaction-item" onclick="window.chatApp.sendReaction('${reaction}')">${reaction}</span>`).join('')}
            </div>
        `;

        return picker;
    }

    sendReaction(emoji) {
        const reactionPicker = document.getElementById('reaction-picker');
        const messageId = reactionPicker.dataset.messageId;

        if (!messageId || !this.currentConversation) {
            return;
        }

        const reactionData = {
            type: 'reaction',
            emoji: emoji,
            target_message_id: parseInt(messageId)
        };

        // Send via WebSocket
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(reactionData));
        }

        // Hide reaction picker
        reactionPicker.style.display = 'none';
    }

    handleReactionUpdate(data) {
        console.log('Reaction update received:', data);

        const messageElement = document.querySelector(`[data-message-id="${data.message_id}"]`);
        if (!messageElement) {
            console.log('Message element not found for reaction update');
            return;
        }

        // Update reactions display
        this.updateMessageReactions(messageElement, data.reactions);

        // Show notification for reaction
        if (data.user_id !== this.currentUser.id) {
            const user = this.users.get(data.user_id) || { username: 'Someone' };
            const action = data.action === 'added' ? 'reacted with' : 'removed reaction';
            this.showInAppNotification(`${user.username} ${action} ${data.emoji}`, 'info');
        }
    }

    updateMessageReactions(messageElement, reactions) {
        // Remove existing reactions display
        const existingReactions = messageElement.querySelector('.message-reactions');
        if (existingReactions) {
            existingReactions.remove();
        }

        // If no reactions, don't show anything
        if (!reactions || Object.keys(reactions).length === 0) {
            return;
        }

        // Create reactions display
        const reactionsDiv = document.createElement('div');
        reactionsDiv.className = 'message-reactions';

        for (const [emoji, users] of Object.entries(reactions)) {
            const reactionSpan = document.createElement('span');
            reactionSpan.className = 'reaction-item';
            reactionSpan.innerHTML = `${emoji} ${users.length}`;

            // Add click handler to toggle reaction
            const messageId = messageElement.getAttribute('data-message-id');
            reactionSpan.addEventListener('click', () => {
                this.toggleReaction(messageId, emoji);
            });

            // Add tooltip with user names
            const userNames = users.map(user => {
                const userData = this.users.get(user.user_id);
                return userData ? userData.username : 'Unknown';
            }).join(', ');
            reactionSpan.title = userNames;

            // Highlight if current user reacted
            const currentUserReacted = users.some(user => user.user_id === this.currentUser.id);
            if (currentUserReacted) {
                reactionSpan.classList.add('user-reacted');
            }

            reactionsDiv.appendChild(reactionSpan);
        }

        // Add reactions to message
        const messageContent = messageElement.querySelector('.chat-msg-content');
        messageContent.appendChild(reactionsDiv);
    }

    toggleReaction(messageId, emoji) {
        const reactionData = {
            type: 'reaction',
            emoji: emoji,
            target_message_id: parseInt(messageId)
        };

        // Send via WebSocket
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(reactionData));
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }

    // Create app instance and make it globally available for call functions
    window.chatApp = new WebChatApp();
});

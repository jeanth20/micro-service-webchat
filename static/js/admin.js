class AdminPanel {
    constructor() {
        this.currentSection = 'dashboard';
        this.adminCredentials = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboard();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.closest('.nav-link').dataset.section;
                this.showSection(section);
            });
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });

        // Dashboard refresh
        document.getElementById('refresh-dashboard-btn').addEventListener('click', () => {
            this.loadDashboard();
        });

        // User management
        document.getElementById('add-user-btn').addEventListener('click', () => {
            this.showUserModal();
        });

        document.getElementById('search-users-btn').addEventListener('click', () => {
            this.searchUsers();
        });

        document.getElementById('user-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchUsers();
            }
        });

        // User form
        document.getElementById('user-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveUser();
        });

        // Group management
        document.getElementById('add-group-btn').addEventListener('click', () => {
            this.showGroupModal();
        });

        // Group form
        document.getElementById('group-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveGroup();
        });

        // Moderation
        document.getElementById('load-messages-btn').addEventListener('click', () => {
            this.loadMessages();
        });

        // Call logs
        document.getElementById('load-calls-btn').addEventListener('click', () => {
            this.loadCallLogs();
        });

        // Modal close
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                modal.style.display = 'none';
            });
        });

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }

    showSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');

        // Update sections
        document.querySelectorAll('.admin-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');

        // Update page title
        const titles = {
            dashboard: 'Dashboard',
            users: 'User Management',
            groups: 'Group Management',
            moderation: 'Chat Moderation',
            calls: 'Call Logs',
            settings: 'Settings',
            logs: 'Moderation Logs'
        };
        document.getElementById('page-title').textContent = titles[section];

        this.currentSection = section;

        // Load section data
        switch (section) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'users':
                this.loadUsers();
                break;
            case 'groups':
                this.loadGroups();
                break;
            case 'moderation':
                this.loadModerationFilters();
                break;
            case 'calls':
                this.loadCallFilters();
                break;
            case 'settings':
                this.loadSettings();
                break;
            case 'logs':
                this.loadModerationLogs();
                break;
        }
    }

    async makeRequest(url, options = {}) {
        try {
            // Show loading indicator
            this.showLoading(true);

            // Get stored credentials or use default
            const storedAuth = sessionStorage.getItem('adminAuth') || btoa('admin:admin123');

            const response = await fetch(url, {
                ...options,
                headers: {
                    'Authorization': `Basic ${storedAuth}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (response.status === 401) {
                this.showError('Authentication failed. Please refresh and login again.');
                sessionStorage.removeItem('adminAuth');
                setTimeout(() => {
                    window.location.href = '/admin';
                }, 2000);
                return null;
            }

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }

            const result = await response.json();
            this.showLoading(false);
            return result;
        } catch (error) {
            console.error('Request failed:', error);
            this.showError('Request failed: ' + error.message);
            this.showLoading(false);
            return null;
        }
    }

    showLoading(show) {
        const existingLoader = document.getElementById('admin-loader');
        if (show) {
            if (!existingLoader) {
                const loader = document.createElement('div');
                loader.id = 'admin-loader';
                loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                loader.style.cssText = `
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 4px;
                    z-index: 1002;
                `;
                document.body.appendChild(loader);
            }
        } else {
            if (existingLoader) {
                existingLoader.remove();
            }
        }
    }

    async loadDashboard() {
        // Initialize admin data first
        await this.initializeAdminData();

        const data = await this.makeRequest('/api/admin/dashboard');
        if (!data) return;

        // Update stats
        document.getElementById('total-users').textContent = data.stats.total_users;
        document.getElementById('active-users').textContent = data.stats.active_users;
        document.getElementById('online-users').textContent = data.stats.online_users;
        document.getElementById('total-messages').textContent = data.stats.total_messages;
        document.getElementById('total-groups').textContent = data.stats.total_groups;
        document.getElementById('total-calls').textContent = data.stats.total_calls;

        // Update recent activity
        this.updateRecentUsers(data.recent_activity.users);
        this.updateRecentMessages(data.recent_activity.messages);
    }

    async initializeAdminData() {
        try {
            await this.makeRequest('/api/admin/initialize', { method: 'POST' });
        } catch (error) {
            console.log('Admin data already initialized or error occurred:', error);
        }
    }

    updateRecentUsers(users) {
        const container = document.getElementById('recent-users');
        if (!users || users.length === 0) {
            container.innerHTML = '<div class="activity-item">No recent users</div>';
            return;
        }

        container.innerHTML = users.map(user => `
            <div class="activity-item">
                <strong>${user.username}</strong> - ${user.email || 'No email'}
                <br><small>Joined: ${new Date(user.created_at).toLocaleDateString()}</small>
                <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span>
            </div>
        `).join('');
    }

    updateRecentMessages(messages) {
        const container = document.getElementById('recent-messages');
        if (!messages || messages.length === 0) {
            container.innerHTML = '<div class="activity-item">No recent messages</div>';
            return;
        }

        container.innerHTML = messages.map(message => `
            <div class="activity-item">
                <strong>${message.sender?.username || `User ${message.sender_id}`}</strong>: ${message.content ? message.content.substring(0, 50) + '...' : '[Media]'}
                <br><small>${new Date(message.created_at).toLocaleString()}</small>
            </div>
        `).join('');
    }

    async loadUsers() {
        const users = await this.makeRequest('/api/admin/users');
        if (!users) return;

        const tbody = document.querySelector('#users-table tbody');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email || '-'}</td>
                <td><span class="status-badge ${user.role === 'admin' ? 'status-active' : ''}">${user.role}</span></td>
                <td><span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                <td><span class="status-badge ${user.can_create_chats ? 'status-active' : 'status-inactive'}">${user.can_create_chats ? 'Yes' : 'No'}</span></td>
                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="adminPanel.editUser(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="adminPanel.deleteUser(${user.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async searchUsers() {
        const search = document.getElementById('user-search').value;
        const users = await this.makeRequest(`/api/admin/users?search=${encodeURIComponent(search)}`);
        if (!users) return;

        const tbody = document.querySelector('#users-table tbody');
        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email || '-'}</td>
                <td><span class="status-badge ${user.role === 'admin' ? 'status-active' : ''}">${user.role}</span></td>
                <td><span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                <td><span class="status-badge ${user.can_create_chats ? 'status-active' : 'status-inactive'}">${user.can_create_chats ? 'Yes' : 'No'}</span></td>
                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-warning" onclick="adminPanel.editUser(${user.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="adminPanel.deleteUser(${user.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    showUserModal(user = null) {
        const modal = document.getElementById('user-modal');
        const title = document.getElementById('user-modal-title');
        const form = document.getElementById('user-form');

        if (user) {
            title.textContent = 'Edit User';
            document.getElementById('username').value = user.username;
            document.getElementById('email').value = user.email || '';
            document.getElementById('role').value = user.role;
            document.getElementById('is-active').checked = user.is_active;
            document.getElementById('can-create-chats').checked = user.can_create_chats;
            form.dataset.userId = user.id;
        } else {
            title.textContent = 'Add User';
            form.reset();
            delete form.dataset.userId;
        }

        modal.style.display = 'block';
    }

    async saveUser() {
        const form = document.getElementById('user-form');
        const formData = new FormData(form);
        const userData = {
            username: formData.get('username'),
            email: formData.get('email') || null,
            role: formData.get('role'),
            is_active: formData.has('is_active'),
            can_create_chats: formData.has('can_create_chats')
        };

        let result;
        if (form.dataset.userId) {
            // Update user
            result = await this.makeRequest(`/api/admin/users/${form.dataset.userId}`, {
                method: 'PUT',
                body: JSON.stringify(userData)
            });
        } else {
            // Create user
            result = await this.makeRequest('/api/admin/users', {
                method: 'POST',
                body: JSON.stringify(userData)
            });
        }

        if (result) {
            document.getElementById('user-modal').style.display = 'none';
            this.loadUsers();
            this.showSuccess('User saved successfully!');
        }
    }

    async editUser(userId) {
        const users = await this.makeRequest('/api/admin/users');
        const user = users.find(u => u.id === userId);
        if (user) {
            this.showUserModal(user);
        }
    }

    async deleteUser(userId) {
        if (confirm('Are you sure you want to delete this user?')) {
            const result = await this.makeRequest(`/api/admin/users/${userId}`, {
                method: 'DELETE'
            });

            if (result) {
                this.loadUsers();
                this.showSuccess('User deleted successfully!');
            }
        }
    }

    showSuccess(message) {
        // Simple success notification
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #d4edda;
            color: #155724;
            padding: 15px 20px;
            border-radius: 4px;
            border: 1px solid #c3e6cb;
            z-index: 1001;
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    showError(message) {
        // Simple error notification
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f8d7da;
            color: #721c24;
            padding: 15px 20px;
            border-radius: 4px;
            border: 1px solid #f5c6cb;
            z-index: 1001;
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }

    logout() {
        if (confirm('Are you sure you want to logout?')) {
            window.location.href = '/';
        }
    }

    showGroupModal() {
        const modal = document.getElementById('group-modal');
        const form = document.getElementById('group-form');
        form.reset();
        modal.style.display = 'block';
    }

    async saveGroup() {
        const form = document.getElementById('group-form');
        const formData = new FormData(form);
        const groupData = {
            name: formData.get('name'),
            description: formData.get('description') || null
        };
        const createdBy = formData.get('created_by');

        const result = await this.makeRequest(`/api/admin/groups?created_by=${createdBy}`, {
            method: 'POST',
            body: JSON.stringify(groupData)
        });

        if (result) {
            document.getElementById('group-modal').style.display = 'none';
            this.loadGroups();
            this.showSuccess('Group created successfully!');
        }
    }

    async loadGroups() {
        const groups = await this.makeRequest('/api/admin/groups');
        if (!groups) return;

        const tbody = document.querySelector('#groups-table tbody');
        tbody.innerHTML = groups.map(group => `
            <tr>
                <td>${group.id}</td>
                <td>${group.name}</td>
                <td>${group.description || '-'}</td>
                <td>${group.creator_username || `User ${group.created_by}`}</td>
                <td>${group.member_count || 0}</td>
                <td>${new Date(group.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="adminPanel.viewGroupMembers(${group.id})" title="View Members">
                        <i class="fas fa-users"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="adminPanel.deleteGroup(${group.id})" title="Delete Group">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async deleteGroup(groupId) {
        if (confirm('Are you sure you want to delete this group?')) {
            const result = await this.makeRequest(`/api/admin/groups/${groupId}`, {
                method: 'DELETE'
            });

            if (result) {
                this.loadGroups();
                this.showSuccess('Group deleted successfully!');
            }
        }
    }

    async viewGroupMembers(groupId) {
        const members = await this.makeRequest(`/api/admin/groups/${groupId}/members`);
        if (!members) return;

        let membersList = members.map(member =>
            `${member.user.username} ${member.is_admin ? '(Admin)' : ''}`
        ).join('\n');

        alert(`Group Members:\n\n${membersList || 'No members found'}`);
    }

    async loadModerationFilters() {
        // Load users for filter
        const users = await this.makeRequest('/api/admin/users');
        if (users) {
            const userFilter = document.getElementById('moderation-user-filter');
            userFilter.innerHTML = '<option value="">All Users</option>' +
                users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
        }

        // Load groups for filter
        const groups = await this.makeRequest('/api/admin/groups');
        if (groups) {
            const groupFilter = document.getElementById('moderation-group-filter');
            groupFilter.innerHTML = '<option value="">All Groups</option>' +
                groups.map(group => `<option value="${group.id}">${group.name}</option>`).join('');
        }
    }

    async loadMessages() {
        const userId = document.getElementById('moderation-user-filter').value;
        const groupId = document.getElementById('moderation-group-filter').value;

        let url = '/api/admin/messages?';
        if (userId) url += `user_id=${userId}&`;
        if (groupId) url += `group_id=${groupId}&`;

        const messages = await this.makeRequest(url);
        if (!messages) return;

        const tbody = document.querySelector('#messages-table tbody');
        tbody.innerHTML = messages.map(message => `
            <tr>
                <td>${message.id}</td>
                <td>${message.sender_username || `User ${message.sender_id}`}</td>
                <td>${message.content ? (message.content.length > 100 ? message.content.substring(0, 100) + '...' : message.content) : '[Media]'}</td>
                <td><span class="status-badge">${message.message_type}</span></td>
                <td>${message.group_id ? (message.group_name || `Group ${message.group_id}`) : (message.receiver_username || `User ${message.receiver_id}`)}</td>
                <td>${new Date(message.created_at).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="adminPanel.viewMessage(${message.id})" title="View Full Message">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="adminPanel.deleteMessage(${message.id})" title="Delete Message">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async viewMessage(messageId) {
        // Find the message in the current loaded messages
        const messages = await this.makeRequest(`/api/admin/messages?limit=1000`);
        const message = messages?.find(m => m.id === messageId);

        if (message) {
            const content = message.content || '[Media/File]';
            const sender = message.sender_username || `User ${message.sender_id}`;
            const target = message.group_id ?
                (message.group_name || `Group ${message.group_id}`) :
                (message.receiver_username || `User ${message.receiver_id}`);

            alert(`Message Details:\n\nID: ${message.id}\nSender: ${sender}\nTarget: ${target}\nType: ${message.message_type}\nCreated: ${new Date(message.created_at).toLocaleString()}\n\nContent:\n${content}`);
        }
    }

    async deleteMessage(messageId) {
        const reason = prompt('Reason for deletion (optional):');
        if (reason !== null) {
            const result = await this.makeRequest(`/api/admin/messages/${messageId}?reason=${encodeURIComponent(reason)}`, {
                method: 'DELETE'
            });

            if (result) {
                this.loadMessages();
                this.showSuccess('Message deleted successfully!');
            }
        }
    }

    async loadCallFilters() {
        // Load users for filter
        const users = await this.makeRequest('/api/admin/users');
        if (users) {
            const userFilter = document.getElementById('call-user-filter');
            userFilter.innerHTML = '<option value="">All Users</option>' +
                users.map(user => `<option value="${user.id}">${user.username}</option>`).join('');
        }
    }

    async loadCallLogs() {
        const userId = document.getElementById('call-user-filter').value;

        let url = '/api/admin/call-logs?';
        if (userId) url += `user_id=${userId}&`;

        const calls = await this.makeRequest(url);
        if (!calls) return;

        const tbody = document.querySelector('#calls-table tbody');
        tbody.innerHTML = calls.map(call => `
            <tr>
                <td>${call.id}</td>
                <td>${call.caller_username || `User ${call.caller_id}`}</td>
                <td>${call.receiver_id ? (call.receiver_username || `User ${call.receiver_id}`) : '-'}</td>
                <td><span class="status-badge status-${call.call_status.toLowerCase()}">${call.call_status}</span></td>
                <td>${call.duration ? `${call.duration}s` : '-'}</td>
                <td>${new Date(call.started_at).toLocaleString()}</td>
                <td>${call.ended_at ? new Date(call.ended_at).toLocaleString() : '-'}</td>
            </tr>
        `).join('');
    }

    async loadSettings() {
        const settings = await this.makeRequest('/api/admin/settings');
        if (!settings) return;

        // Update settings toggles
        document.getElementById('allow-user-chats').checked = settings.allow_user_chats === 'true';
        document.getElementById('allow-group-creation').checked = settings.allow_group_creation === 'true';

        // Add event listeners for settings changes
        document.getElementById('allow-user-chats').addEventListener('change', (e) => {
            this.updateSetting('allow_user_chats', e.target.checked.toString());
        });

        document.getElementById('allow-group-creation').addEventListener('change', (e) => {
            this.updateSetting('allow_group_creation', e.target.checked.toString());
        });
    }

    async updateSetting(key, value) {
        const result = await this.makeRequest(`/api/admin/settings/${key}`, {
            method: 'PUT',
            body: JSON.stringify({
                setting_value: value,
                description: `Updated by admin`
            })
        });

        if (result) {
            this.showSuccess('Setting updated successfully!');
        }
    }

    async loadModerationLogs() {
        const logs = await this.makeRequest('/api/admin/moderation-logs');
        if (!logs) return;

        const tbody = document.querySelector('#logs-table tbody');
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${log.id}</td>
                <td>User ${log.admin_id}</td>
                <td>${log.action}</td>
                <td>
                    ${log.user_id ? `User ${log.user_id}` : ''}
                    ${log.message_id ? `Message ${log.message_id}` : ''}
                    ${log.group_id ? `Group ${log.group_id}` : ''}
                </td>
                <td>${log.reason || '-'}</td>
                <td>${new Date(log.created_at).toLocaleString()}</td>
            </tr>
        `).join('');
    }
}

// Global functions
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Initialize admin panel
const adminPanel = new AdminPanel();

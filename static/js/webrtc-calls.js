// WebRTC Call Management
class WebRTCCallManager {
    constructor(chatApp) {
        this.chatApp = chatApp;
        this.localStream = null;
        this.remoteStream = null;
        this.peerConnection = null;
        this.isCallActive = false;
        this.isIncomingCall = false;
        this.currentCallId = null;
        this.callType = null; // 'audio' or 'video'
        this.currentCallData = null; // Store current call data
        this.receiverId = null; // Track the other party's ID
        this.isMuted = true; // Start muted by default
        this.isVideoEnabled = false; // Start with video off by default

        // WebRTC configuration
        this.rtcConfig = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        this.setupCallUI();
    }

    setupCallUI() {
        // Create call modal HTML
        const callModalHTML = `
            <div id="call-modal" class="call-modal" style="display: none;">
                <div class="call-modal-content">
                    <div class="call-header">
                        <h3 id="call-title">Call</h3>
                        <span id="call-status">Connecting...</span>
                        <div class="call-info">
                            <small style="color: #f44336; font-weight: bold;">🔇 You are muted - Click microphone to unmute</small>
                        </div>
                    </div>
                    
                    <div class="call-video-container">
                        <video id="remote-video" autoplay playsinline></video>
                        <video id="local-video" autoplay playsinline muted></video>
                    </div>
                    
                    <div class="call-controls">
                        <button id="mute-btn" class="call-btn mute-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                                <path d="M19 10v1a7 7 0 0 1-14 0v-1"/>
                                <path d="M12 18v4"/>
                                <path d="M8 22h8"/>
                            </svg>
                        </button>
                        
                        <button id="video-btn" class="call-btn video-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M23 7l-7 5 7 5V7z"/>
                                <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                            </svg>
                        </button>
                        
                        <button id="end-call-btn" class="call-btn end-call-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
            
            <div id="incoming-call-modal" class="call-modal" style="display: none;">
                <div class="call-modal-content incoming-call">
                    <div class="caller-info">
                        <img id="caller-avatar" src="/static/images/default-avatar.png" alt="Caller">
                        <h3 id="caller-name">Unknown Caller</h3>
                        <p id="call-type-text">Incoming call</p>
                    </div>
                    
                    <div class="incoming-call-controls">
                        <button id="accept-call-btn" class="call-btn accept-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                            </svg>
                        </button>
                        
                        <button id="decline-call-btn" class="call-btn decline-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.insertAdjacentHTML('beforeend', callModalHTML);
        
        // Setup event listeners
        this.setupCallEventListeners();
    }

    setupCallEventListeners() {
        document.getElementById('mute-btn').addEventListener('click', () => this.toggleMute());
        document.getElementById('video-btn').addEventListener('click', () => this.toggleVideo());
        document.getElementById('end-call-btn').addEventListener('click', () => this.endCall());
        document.getElementById('accept-call-btn').addEventListener('click', () => this.acceptCall());
        document.getElementById('decline-call-btn').addEventListener('click', () => this.declineCall());
    }

    async initiateCall(type, receiverId) {
        console.log(`Initiating ${type} call to user ${receiverId}`);

        this.callType = type;
        this.currentCallId = Date.now().toString();
        this.receiverId = receiverId;

        try {
            // Get user media
            const constraints = {
                audio: true,
                video: type === 'video'
            };

            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);

            // Start muted by default
            this.setInitialMuteState();

            // Show call modal
            this.showCallModal();

            // Setup local video
            const localVideo = document.getElementById('local-video');
            localVideo.srcObject = this.localStream;
            localVideo.style.display = type === 'video' ? 'block' : 'none';

            // Create peer connection
            this.createPeerConnection();

            // Add local stream to peer connection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });

            // Send call request
            const callData = {
                type: 'call',
                call_status: 'request',
                call_type: type,
                call_id: this.currentCallId,
                receiver_id: receiverId
            };

            if (this.chatApp.websocket && this.chatApp.websocket.readyState === WebSocket.OPEN) {
                this.chatApp.websocket.send(JSON.stringify(callData));
                document.getElementById('call-status').textContent = 'Calling...';
            } else {
                throw new Error('WebSocket not connected');
            }

        } catch (error) {
            console.error('Error initiating call:', error);
            this.chatApp.showInAppNotification('Failed to start call: ' + error.message, 'error');
            this.endCall();
        }
    }

    createPeerConnection() {
        this.peerConnection = new RTCPeerConnection(this.rtcConfig);
        
        // Handle remote stream
        this.peerConnection.ontrack = (event) => {
            console.log('Received remote stream');
            this.remoteStream = event.streams[0];
            const remoteVideo = document.getElementById('remote-video');
            remoteVideo.srcObject = this.remoteStream;
        };
        
        // Handle ICE candidates
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                console.log('Sending ICE candidate');
                this.sendSignalingMessage({
                    type: 'ice-candidate',
                    candidate: event.candidate
                });
            }
        };
        
        // Handle connection state changes
        this.peerConnection.onconnectionstatechange = () => {
            console.log('Connection state:', this.peerConnection.connectionState);
            const status = document.getElementById('call-status');
            
            switch (this.peerConnection.connectionState) {
                case 'connected':
                    status.textContent = 'Connected';
                    this.isCallActive = true;
                    break;
                case 'disconnected':
                case 'failed':
                    status.textContent = 'Connection failed';
                    this.endCall();
                    break;
                case 'closed':
                    this.endCall();
                    break;
            }
        };
    }

    sendSignalingMessage(message) {
        const signalData = {
            type: 'webrtc-signal',
            call_id: this.currentCallId,
            signal: message,
            receiver_id: this.receiverId
        };

        console.log('Sending signaling message:', signalData);

        if (this.chatApp.websocket && this.chatApp.websocket.readyState === WebSocket.OPEN) {
            this.chatApp.websocket.send(JSON.stringify(signalData));
        }
    }

    async handleIncomingCall(callData) {
        console.log('Incoming call:', callData);

        this.isIncomingCall = true;
        this.currentCallId = callData.call_id;
        this.callType = callData.call_type || 'audio'; // Default to audio if not specified
        this.receiverId = callData.caller_id; // Set receiver to the caller

        // Store caller info for later use
        this.currentCallData = callData;

        // Show incoming call modal
        this.showIncomingCallModal(callData);
    }

    showIncomingCallModal(callData) {
        console.log('Showing incoming call modal with data:', callData);

        const modal = document.getElementById('incoming-call-modal');
        const callerName = document.getElementById('caller-name');
        const callTypeText = document.getElementById('call-type-text');
        const callerAvatar = document.getElementById('caller-avatar');

        if (!modal || !callerName || !callTypeText || !callerAvatar) {
            console.error('Call modal elements not found');
            return;
        }

        // Get caller info
        const callerId = callData.caller_id || callData.call_log?.caller_id;
        const caller = this.chatApp.users.get(callerId) || { username: 'Unknown User' };
        const callType = callData.call_type || 'audio';

        console.log('Caller info:', caller, 'Call type:', callType);

        callerName.textContent = caller.username;
        callTypeText.textContent = `Incoming ${callType} call`;
        callerAvatar.src = caller.avatar_url || '/static/images/default-avatar.png';

        modal.style.display = 'flex';

        // Auto-decline after 30 seconds
        setTimeout(() => {
            if (this.isIncomingCall) {
                console.log('Auto-declining call after timeout');
                this.declineCall();
            }
        }, 30000);
    }

    async acceptCall() {
        console.log('Accepting call, callType:', this.callType);

        try {
            // Ensure we have call type
            if (!this.callType) {
                this.callType = this.currentCallData?.call_type || 'audio';
                console.log('Set callType to:', this.callType);
            }

            // Get user media
            const constraints = {
                audio: true,
                video: this.callType === 'video'
            };

            console.log('Requesting media with constraints:', constraints);
            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);

            // Start muted by default
            this.setInitialMuteState();

            // Hide incoming call modal and show call modal
            document.getElementById('incoming-call-modal').style.display = 'none';
            this.showCallModal();

            // Setup local video
            const localVideo = document.getElementById('local-video');
            localVideo.srcObject = this.localStream;
            localVideo.style.display = this.callType === 'video' ? 'block' : 'none';

            // Create peer connection
            this.createPeerConnection();

            // Add local stream
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });

            // Send accept message with proper receiver_id
            const acceptData = {
                type: 'call',
                call_status: 'accept',
                call_type: this.callType,
                call_id: this.currentCallId,
                receiver_id: this.currentCallData?.caller_id // Send back to the caller
            };

            console.log('Sending accept message:', acceptData);

            if (this.chatApp.websocket && this.chatApp.websocket.readyState === WebSocket.OPEN) {
                this.chatApp.websocket.send(JSON.stringify(acceptData));
            }

            this.isIncomingCall = false;

        } catch (error) {
            console.error('Error accepting call:', error);
            this.chatApp.showInAppNotification('Failed to accept call: ' + error.message, 'error');
            this.declineCall();
        }
    }

    declineCall() {
        console.log('Declining call');

        // Send decline message with proper receiver_id
        const declineData = {
            type: 'call',
            call_status: 'decline',
            call_type: this.callType || 'audio',
            call_id: this.currentCallId,
            receiver_id: this.currentCallData?.caller_id // Send back to the caller
        };

        console.log('Sending decline message:', declineData);

        if (this.chatApp.websocket && this.chatApp.websocket.readyState === WebSocket.OPEN) {
            this.chatApp.websocket.send(JSON.stringify(declineData));
        }

        // Hide incoming call modal
        document.getElementById('incoming-call-modal').style.display = 'none';

        this.isIncomingCall = false;
        this.currentCallId = null;
        this.currentCallData = null;
    }

    endCall() {
        console.log('Ending call');
        
        // Send end call message
        if (this.currentCallId) {
            const endData = {
                type: 'call',
                call_status: 'end',
                call_id: this.currentCallId
            };
            
            if (this.chatApp.websocket && this.chatApp.websocket.readyState === WebSocket.OPEN) {
                this.chatApp.websocket.send(JSON.stringify(endData));
            }
        }
        
        // Clean up
        this.cleanup();
    }

    setInitialMuteState() {
        if (this.localStream) {
            // Mute audio by default
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = false;
                this.isMuted = true;
            }

            // For video calls, start with video enabled but can be toggled
            const videoTrack = this.localStream.getVideoTracks()[0];
            if (videoTrack && this.callType === 'video') {
                videoTrack.enabled = true;
                this.isVideoEnabled = true;
            } else if (videoTrack) {
                videoTrack.enabled = false;
                this.isVideoEnabled = false;
            }

            // Update UI to reflect muted state
            this.updateMuteButtonUI();
            this.updateVideoButtonUI();
        }
    }

    async handleWebRTCSignal(signalData) {
        console.log('Received WebRTC signal:', signalData);

        if (!this.peerConnection) {
            console.error('No peer connection available for signal');
            return;
        }

        const signal = signalData.signal;

        try {
            switch (signal.type) {
                case 'offer':
                    console.log('Handling SDP offer');
                    await this.peerConnection.setRemoteDescription(new RTCSessionDescription(signal.sdp));

                    // Create and send answer
                    const answer = await this.peerConnection.createAnswer();
                    await this.peerConnection.setLocalDescription(answer);

                    this.sendSignalingMessage({
                        type: 'answer',
                        sdp: answer
                    });
                    break;

                case 'answer':
                    console.log('Handling SDP answer');
                    await this.peerConnection.setRemoteDescription(new RTCSessionDescription(signal.sdp));
                    break;

                case 'ice-candidate':
                    console.log('Handling ICE candidate');
                    await this.peerConnection.addIceCandidate(new RTCIceCandidate(signal.candidate));
                    break;

                default:
                    console.log('Unknown signal type:', signal.type);
            }
        } catch (error) {
            console.error('Error handling WebRTC signal:', error);
        }
    }

    cleanup() {
        console.log('Cleaning up call resources');

        // Stop local stream
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }

        // Close peer connection
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }

        // Hide modals
        const callModal = document.getElementById('call-modal');
        const incomingModal = document.getElementById('incoming-call-modal');

        if (callModal) callModal.style.display = 'none';
        if (incomingModal) incomingModal.style.display = 'none';

        // Reset state
        this.isCallActive = false;
        this.isIncomingCall = false;
        this.currentCallId = null;
        this.callType = null;
        this.remoteStream = null;
        this.currentCallData = null;
        this.receiverId = null;
        this.isMuted = true; // Reset to muted for next call
        this.isVideoEnabled = false; // Reset video state
    }

    showCallModal() {
        const modal = document.getElementById('call-modal');
        const title = document.getElementById('call-title');
        const videoBtn = document.getElementById('video-btn');

        title.textContent = `${this.callType.charAt(0).toUpperCase() + this.callType.slice(1)} Call`;

        // Show/hide video button based on call type
        videoBtn.style.display = this.callType === 'video' ? 'block' : 'none';

        // Set initial UI state for buttons
        this.updateMuteButtonUI();
        this.updateVideoButtonUI();

        // Show notification about starting muted
        setTimeout(() => {
            this.chatApp.showInAppNotification('Call started muted. Click microphone to unmute.', 'info');
        }, 1000);

        modal.style.display = 'flex';
    }

    toggleMute() {
        if (this.localStream) {
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                this.isMuted = !audioTrack.enabled;
                this.updateMuteButtonUI();

                // Show notification
                const status = this.isMuted ? 'muted' : 'unmuted';
                this.chatApp.showInAppNotification(`Microphone ${status}`, 'info');
            }
        }
    }

    toggleVideo() {
        if (this.localStream && this.callType === 'video') {
            const videoTrack = this.localStream.getVideoTracks()[0];
            if (videoTrack) {
                videoTrack.enabled = !videoTrack.enabled;
                this.isVideoEnabled = videoTrack.enabled;
                this.updateVideoButtonUI();

                // Show/hide local video element
                const localVideo = document.getElementById('local-video');
                localVideo.style.display = videoTrack.enabled ? 'block' : 'none';

                // Show notification
                const status = this.isVideoEnabled ? 'enabled' : 'disabled';
                this.chatApp.showInAppNotification(`Camera ${status}`, 'info');
            }
        }
    }

    updateMuteButtonUI() {
        const muteBtn = document.getElementById('mute-btn');
        const callInfo = document.querySelector('.call-info small');

        if (muteBtn) {
            muteBtn.classList.toggle('muted', this.isMuted);
            muteBtn.title = this.isMuted ? 'Unmute microphone' : 'Mute microphone';

            // Update button appearance to indicate state
            if (this.isMuted) {
                muteBtn.style.backgroundColor = '#f44336';
                muteBtn.style.color = 'white';
            } else {
                muteBtn.style.backgroundColor = '#4CAF50';
                muteBtn.style.color = 'white';
            }
        }

        // Update info text
        if (callInfo) {
            if (this.isMuted) {
                callInfo.textContent = '🔇 You are muted - Click microphone to unmute';
                callInfo.style.color = '#f44336';
            } else {
                callInfo.textContent = '🎤 Microphone is active';
                callInfo.style.color = '#4CAF50';
            }
        }
    }

    updateVideoButtonUI() {
        const videoBtn = document.getElementById('video-btn');
        if (videoBtn) {
            videoBtn.classList.toggle('disabled', !this.isVideoEnabled);
            videoBtn.title = this.isVideoEnabled ? 'Turn off camera' : 'Turn on camera';

            // Update button appearance
            if (!this.isVideoEnabled) {
                videoBtn.style.backgroundColor = '#f44336';
                videoBtn.style.color = 'white';
            } else {
                videoBtn.style.backgroundColor = '#2196F3';
                videoBtn.style.color = 'white';
            }
        }
    }

    handleCallMessage(callData) {
        console.log('Handling call message:', callData);

        // Extract call info from different possible structures
        const callStatus = callData.call_status || callData.call_log?.call_status;
        const callType = callData.call_type || 'audio';
        const callId = callData.call_id || callData.call_log?.id;
        const callerId = callData.caller_id || callData.call_log?.caller_id;

        // Update callData with normalized values
        const normalizedCallData = {
            ...callData,
            call_status: callStatus,
            call_type: callType,
            call_id: callId,
            caller_id: callerId
        };

        console.log('Normalized call data:', normalizedCallData);

        switch (callStatus) {
            case 'request':
                this.handleIncomingCall(normalizedCallData);
                break;
            case 'accept':
                this.handleCallAccepted(normalizedCallData);
                break;
            case 'decline':
                this.handleCallDeclined(normalizedCallData);
                break;
            case 'end':
                this.handleCallEnded(normalizedCallData);
                break;
            default:
                console.log('Unknown call status:', callStatus);
        }
    }

    async handleCallAccepted(callData) {
        console.log('Call accepted');
        document.getElementById('call-status').textContent = 'Call accepted, connecting...';
        this.chatApp.showInAppNotification('Call accepted', 'success');

        // Create and send SDP offer
        try {
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);

            this.sendSignalingMessage({
                type: 'offer',
                sdp: offer
            });

            console.log('SDP offer sent');
        } catch (error) {
            console.error('Error creating offer:', error);
            this.endCall();
        }
    }

    handleCallDeclined(callData) {
        console.log('Call declined');
        this.chatApp.showInAppNotification('Call declined', 'info');
        this.cleanup();
    }

    handleCallEnded(callData) {
        console.log('Call ended');
        this.chatApp.showInAppNotification('Call ended', 'info');
        this.cleanup();
    }
}

// Export for use in main app
window.WebRTCCallManager = WebRTCCallManager;

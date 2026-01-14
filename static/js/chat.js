// WebSocket connection
let chatSocket = null;
let typingTimeout = null;
let usersTyping = new Set();

function connect() {
    const roomId = document.getElementById('room-id').value;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws/chatroom/${roomId}/`;
    
    chatSocket = new WebSocket(socketUrl);
    
    chatSocket.onopen = function(e) {
        console.log('WebSocket connection established');
        loadPreviousMessages();
    };
    
    chatSocket.onclose = function(e) {
        console.log('WebSocket connection closed');
        setTimeout(function() {
            connect();
        }, 2000);
    };
    
    chatSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };
    
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        handleMessage(data);
    };
}

function handleMessage(data) {
    const messagesContainer = document.getElementById('messages-container');
    const typingIndicator = document.getElementById('typing-indicator');
    
    switch(data.type) {
        case 'message':
            addMessage(data);
            scrollToBottom();
            break;
            
        case 'user_list':
            updateUserList(data.users);
            break;
            
        case 'user_joined':
            showNotification(`${data.username} joined the chat`);
            updateOnlineCount();
            break;
            
        case 'user_left':
            showNotification(`${data.username} left the chat`);
            updateOnlineCount();
            break;
            
        case 'typing':
            if (data.is_typing) {
                usersTyping.add(data.username);
            } else {
                usersTyping.delete(data.username);
            }
            updateTypingIndicator();
            break;
    }
}

function addMessage(data) {
    const messagesContainer = document.getElementById('messages-container');
    const userId = document.getElementById('user-id').value;
    const isOwn = parseInt(data.sender_id) === parseInt(userId);
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${isOwn ? 'message-own' : 'message-other'}`;
    messageElement.id = `message-${data.message_id}`;
    
    const time = new Date(data.timestamp);
    const timeString = time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    messageElement.innerHTML = `
        <div class="message-sender">${isOwn ? 'You' : data.sender_username}</div>
        <div class="message-content">${escapeHtml(data.message)}</div>
        <div class="message-time">${timeString}</div>
    `;
    
    messagesContainer.appendChild(messageElement);
}

function sendMessage() {
    const messageInput = document.getElementById('chat-message-input');
    const message = messageInput.value.trim();
    
    if (message && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'chat_message',
            'message': message
        }));
        messageInput.value = '';
        stopTyping();
    }
}

function startTyping() {
    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'typing',
            'is_typing': true
        }));
        
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(stopTyping, 2000);
    }
}

function stopTyping() {
    if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'type': 'typing',
            'is_typing': false
        }));
    }
    clearTimeout(typingTimeout);
}

function updateTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (usersTyping.size > 0) {
        const names = Array.from(usersTyping);
        let text = '';
        if (names.length === 1) {
            text = `${names[0]} is typing...`;
        } else if (names.length === 2) {
            text = `${names[0]} and ${names[1]} are typing...`;
        } else {
            text = `${names.length} people are typing...`;
        }
        indicator.textContent = text;
        indicator.style.display = 'block';
    } else {
        indicator.style.display = 'none';
    }
}

function updateUserList(users) {
    const userList = document.getElementById('user-list');
    const userId = document.getElementById('user-id').value;
    
    // Simple implementation - update as needed
    console.log('Users online:', users);
    document.getElementById('online-count').textContent = `${users.length} online`;
}

function updateOnlineCount() {
    // You can implement more sophisticated online tracking here
}

function loadPreviousMessages() {
    const roomId = document.getElementById('room-id').value;
    const lastMessage = document.querySelector('.message');
    const lastMessageId = lastMessage ? lastMessage.id.replace('message-', '') : 0;
    
    fetch(`/chatroom/${roomId}/messages/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `last_message_id=${lastMessageId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.messages) {
            data.messages.forEach(msg => addMessage({
                message_id: msg.id,
                sender_id: msg.sender_id,
                sender_username: msg.sender_username,
                message: msg.content,
                timestamp: msg.timestamp
            }));
            scrollToBottom();
        }
    });
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('messages-container');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showNotification(message) {
    // Simple notification - you can use Toastr or similar for better notifications
    console.log('Notification:', message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    connect();
    
    const messageInput = document.getElementById('chat-message-input');
    const sendButton = document.getElementById('chat-message-submit');
    
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    messageInput.addEventListener('input', function() {
        if (this.value.trim()) {
            startTyping();
        } else {
            stopTyping();
        }
    });
    
    // Auto-scroll to bottom
    scrollToBottom();
});
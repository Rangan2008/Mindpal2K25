// chatbot.js - Handles all chatbot functionality

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages');
    const newChatBtn = document.getElementById('new-chat-btn');
    const chatHistoryList = document.getElementById('chat-history-list');
    const exportChatBtn = document.getElementById('export-chat-btn');
    const voiceBtn = document.getElementById('voice-btn');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar');
    const sidebar = document.getElementById('sidebar');

    // Chat state
    let currentChat = [];
    let chatHistory = [];
    let isWaitingForResponse = false;

    // NEW: Web Speech API for voice input
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false; // Stop listening after a single utterance
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
    } else {
        console.warn("Speech Recognition not supported in this browser.");
        voiceBtn.style.display = 'none'; // Hide button if not supported
    }


    // Initialize
    loadChatHistory();
    setupEventListeners();

    // ===== Event Listeners =====
    function setupEventListeners() {
        // Send message on button click or Enter key
        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !isWaitingForResponse) {
                sendMessage();
            }
        });

        // New chat button
        newChatBtn.addEventListener('click', startNewChat);

        // Export chat button
        exportChatBtn.addEventListener('click', exportChat);

        // NEW: Updated voice button listener
        if (recognition) {
            voiceBtn.addEventListener('click', toggleVoiceRecognition);
            recognition.addEventListener('result', handleVoiceResult);
            recognition.addEventListener('error', handleVoiceError);
            recognition.addEventListener('start', () => {
                voiceBtn.style.color = 'var(--primary-accent)';
                voiceBtn.classList.add('listening'); // For potential animation
            });
            recognition.addEventListener('end', () => {
                voiceBtn.style.color = ''; // Revert to default color
                voiceBtn.classList.remove('listening');
            });
        }

        // Toggle sidebar on mobile
        toggleSidebarBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // ===== NEW: Voice Recognition Functions =====
    function toggleVoiceRecognition() {
        if (voiceBtn.classList.contains('listening')) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (error) {
                console.error("Could not start voice recognition:", error);
                alert("Could not start voice recognition. Please ensure microphone permissions are granted.");
            }
        }
    }

    function handleVoiceResult(event) {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
        // Optionally, send the message automatically after transcription
        sendMessage();
    }

    function handleVoiceError(event) {
        console.error('Speech recognition error:', event.error);
        let errorMessage = "An error occurred during speech recognition.";
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
            errorMessage = "Microphone access was denied. Please allow microphone access in your browser settings.";
        } else if (event.error === 'no-speech') {
            errorMessage = "No speech was detected. Please try again.";
        }
        alert(errorMessage);
    }


    // ===== Core Chat Functions =====
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message || isWaitingForResponse) return;

        // Add user message to UI
        addMessage(message, 'user');
        chatInput.value = '';
        isWaitingForResponse = true;
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send message to Flask backend
            const response = await fetch('/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            });

                let data;
                if (!response.ok) {
                    let errorText = await response.text();
                    console.error(`HTTP error! status: ${response.status}`, errorText);
                    throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
                } else {
                    data = await response.json();
                }
            
            // Remove typing indicator
            removeTypingIndicator();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Add bot response to UI
            addMessage(data.response, 'bot');
            
            // Update chat history
            currentChat.push({ 
                user: message, 
                bot: data.response,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage("Sorry, I encountered an error. Please try again.", 'bot');
        } finally {
            isWaitingForResponse = false;
        }
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        // Format URLs as clickable links
        const formattedText = text.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Preserve line breaks and add link styling
        messageDiv.innerHTML = formattedText.replace(/\n/g, '<br>');
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // ===== Chat History Management =====
    function startNewChat() {
        if (currentChat.length > 0) {
            // Save current chat to history
            const timestamp = new Date().toLocaleString();
            chatHistory.push({
                id: Date.now(),
                title: currentChat[0].user.substring(0, 30) + (currentChat[0].user.length > 30 ? '...' : ''),
                timestamp: timestamp,
                messages: [...currentChat]
            });
            
            // Update chat history UI
            updateChatHistoryUI();
            
            // Save to localStorage
            saveChatHistory();
        }
        
        // Clear current chat
        currentChat = [];
        messagesContainer.innerHTML = `<div class="chat-message bot">
            Hello! 👋 I'm MindPal, your friendly AI companion designed specifically for students like you. I understand the unique challenges you face - from academic stress and exam anxiety to time management and personal concerns. 
            <br><br>
            I'm here to provide practical advice, emotional support, study tips, and help you navigate whatever you're going through. Whether you need help with:
            <br>📚 Study strategies & exam preparation
            <br>😥 Stress management & mental health
            <br>⏰ Time management & organization  
            <br>🎯 Career planning & future goals
            <br>💰 Financial concerns
            <br>🤝 Social & relationship issues
            <br><br>
            Feel free to share what's on your mind - I'm here to listen and help! What would you like to talk about today?
        </div>`;
    }

    async function loadChatHistory() {
        try {
            // First try to load from server
            const response = await fetch('/get_chats');
            
            if (response.ok) {
                const data = await response.json();
                if (data.chats && data.chats.length > 0) {
                    // Process server chat history
                    const processedChats = processServerChats(data.chats);
                    if (processedChats.length > 0) {
                        chatHistory = [{
                            id: Date.now(),
                            title: 'Previous Conversation',
                            timestamp: new Date().toLocaleString(),
                            messages: processedChats
                        }];
                        updateChatHistoryUI();
                        return;
                    }
                }
            }
            
            // Fallback to localStorage if no server history
            const savedHistory = localStorage.getItem('mindpalChatHistory');
            if (savedHistory) {
                chatHistory = JSON.parse(savedHistory);
                updateChatHistoryUI();
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    function processServerChats(serverChats) {
        const processed = [];
        let currentUserMessage = null;
        
        serverChats.forEach(chat => {
            if (chat.message.startsWith('You: ')) {
                currentUserMessage = chat.message.substring(5);
            } else if (chat.message.startsWith('Bot: ') && currentUserMessage) {
                processed.push({
                    user: currentUserMessage,
                    bot: chat.message.substring(5),
                    timestamp: chat.timestamp
                });
                currentUserMessage = null;
            }
        });
        
        return processed;
    }

    function saveChatHistory() {
        localStorage.setItem('mindpalChatHistory', JSON.stringify(chatHistory));
    }

    function updateChatHistoryUI() {
        chatHistoryList.innerHTML = '';
        chatHistory.forEach(chat => {
            const li = document.createElement('li');
            li.className = 'history-entry';
            li.innerHTML = `
                <span>${chat.title}</span>
                <small>${chat.timestamp}</small>
            `;
            li.addEventListener('click', () => loadChat(chat.id));
            chatHistoryList.appendChild(li);
        });
    }

    function loadChat(chatId) {
        const chat = chatHistory.find(c => c.id === chatId);
        if (!chat) return;
        
        messagesContainer.innerHTML = '';
        chat.messages.forEach(msg => {
            addMessage(msg.user, 'user');
            addMessage(msg.bot, 'bot');
        });
        
        // Set as current chat
        currentChat = [...chat.messages];
    }

    // ===== Export Functionality =====
    function exportChat() {
        if (currentChat.length === 0 && chatHistory.length === 0) {
            alert('No chat history to export');
            return;
        }
        
        let exportContent = 'MindPal Chat History\n===================\n\n';
        
        // Add current chat if exists
        if (currentChat.length > 0) {
            exportContent += 'Current Conversation:\n';
            currentChat.forEach(msg => {
                exportContent += `You: ${msg.user}\n`;
                exportContent += `Bot: ${msg.bot}\n\n`;
            });
        }
        
        // Add chat history
        if (chatHistory.length > 0) {
            exportContent += '\nPast Conversations:\n';
            chatHistory.forEach(chat => {
                exportContent += `\n${chat.title} (${chat.timestamp})\n`;
                chat.messages.forEach(msg => {
                    exportContent += `You: ${msg.user}\n`;
                    exportContent += `Bot: ${msg.bot}\n\n`;
                });
            });
        }
        
        // Create download link
        const blob = new Blob([exportContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mindpal_chat_${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
});

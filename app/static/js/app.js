// Best Friend AI Companion - Main JavaScript

class BestFriendApp {
    constructor() {
        this.currentStep = 0;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initOnboarding();
        this.initVoiceRecording();
    }

    bindEvents() {
        // Chat form submission
        const chatForm = document.getElementById('chatForm');
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        }

        // Voice button
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => this.showVoiceModal());
        }

        // Settings form
        const settingsForm = document.querySelector('form[action="/settings"]');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => this.handleSettingsSubmit(e));
        }

        // Onboarding navigation
        const nextBtns = document.querySelectorAll('.next-step');
        const prevBtns = document.querySelectorAll('.prev-step');
        
        nextBtns.forEach(btn => btn.addEventListener('click', () => this.nextStep()));
        prevBtns.forEach(btn => btn.addEventListener('click', () => this.prevStep()));
    }

    // Chat functionality
    async handleChatSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const messageInput = form.querySelector('input[name="message"]');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        messageInput.value = '';
        
        // Show loading state
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ message })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.addMessage('ai', data.response);
            } else {
                throw new Error('Failed to send message');
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('ai', 'Sorry, I encountered an error. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    addMessage(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.textContent = content;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showLoading(show) {
        const sendBtn = document.querySelector('#chatForm button[type="submit"]');
        if (sendBtn) {
            sendBtn.disabled = show;
            sendBtn.innerHTML = show ? '<span class="spinner"></span> Sending...' : 'Send';
        }
    }

    // Voice recording functionality
    initVoiceRecording() {
        const startBtn = document.getElementById('startRecording');
        const stopBtn = document.getElementById('stopRecording');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startRecording());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopRecording());
        }
    }

    async showVoiceModal() {
        const modal = document.getElementById('voiceModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    hideVoiceModal() {
        const modal = document.getElementById('voiceModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processAudio();
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            this.updateRecordingUI(true);
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Unable to access microphone. Please check permissions.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI(false);
            
            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }

    updateRecordingUI(recording) {
        const startBtn = document.getElementById('startRecording');
        const stopBtn = document.getElementById('stopRecording');
        
        if (startBtn) startBtn.style.display = recording ? 'none' : 'block';
        if (stopBtn) stopBtn.style.display = recording ? 'block' : 'none';
    }

    async processAudio() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob);
        
        try {
            const response = await fetch('/api/stt', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Add transcribed text to chat
                    this.addMessage('user', data.text);
                    
                    // Send to chat API
                    await this.sendTranscribedMessage(data.text);
                } else {
                    alert('Transcription failed: ' + data.error);
                }
            } else {
                throw new Error('STT request failed');
            }
        } catch (error) {
            console.error('Error processing audio:', error);
            alert('Failed to process audio. Please try again.');
        } finally {
            this.hideVoiceModal();
        }
    }

    async sendTranscribedMessage(text) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ message: text })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.addMessage('ai', data.response);
            } else {
                throw new Error('Failed to send transcribed message');
            }
        } catch (error) {
            console.error('Error sending transcribed message:', error);
            this.addMessage('ai', 'Sorry, I encountered an error processing your voice message.');
        }
    }

    // Onboarding functionality
    initOnboarding() {
        this.showStep(0);
    }

    nextStep() {
        if (this.currentStep < 3) { // 4 steps total (0-3)
            this.currentStep++;
            this.showStep(this.currentStep);
        }
    }

    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    showStep(step) {
        // Hide all steps
        const steps = document.querySelectorAll('.onboarding-step');
        steps.forEach(s => s.classList.remove('active'));
        
        // Show current step
        if (steps[step]) {
            steps[step].classList.add('active');
        }
        
        // Update step indicators
        const dots = document.querySelectorAll('.step-dot');
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === step);
        });
        
        // Update button states
        const prevBtn = document.querySelector('.prev-step');
        const nextBtn = document.querySelector('.next-step');
        
        if (prevBtn) prevBtn.style.display = step === 0 ? 'none' : 'block';
        if (nextBtn) nextBtn.textContent = step === 3 ? 'Complete Setup' : 'Next';
    }

    // Settings functionality
    async handleSettingsSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Saving...';
        
        try {
            const formData = new FormData(form);
            const response = await fetch('/settings', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                // Show success message
                this.showNotification('Settings saved successfully!', 'success');
            } else {
                throw new Error('Failed to save settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showNotification('Failed to save settings. Please try again.', 'error');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Settings';
        }
    }

    // Utility functions
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Memory search functionality
    async searchMemories(query) {
        try {
            const response = await fetch(`/api/memory/search?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayMemoryResults(data.memories);
            } else {
                throw new Error('Memory search failed');
            }
        } catch (error) {
            console.error('Error searching memories:', error);
        }
    }

    displayMemoryResults(memories) {
        const resultsContainer = document.getElementById('memoryResults');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = '';
        
        if (memories.length === 0) {
            resultsContainer.innerHTML = '<p class="text-gray-500">No memories found.</p>';
            return;
        }
        
        memories.forEach(memory => {
            const memoryDiv = document.createElement('div');
            memoryDiv.className = 'p-4 border rounded-lg mb-2';
            memoryDiv.innerHTML = `
                <p class="font-medium">${memory.content}</p>
                <p class="text-sm text-gray-500">
                    Type: ${memory.memory_type} | 
                    Relevance: ${(memory.relevance * 100).toFixed(1)}% |
                    Created: ${new Date(memory.created_at).toLocaleDateString()}
                </p>
            `;
            resultsContainer.appendChild(memoryDiv);
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BestFriendApp();
});

// Export for global access if needed
window.BestFriendApp = BestFriendApp;

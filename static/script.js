document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const modeIndicator = document.getElementById('mode-indicator');
    const currentMode = document.getElementById('current-mode');
    const fileUpload = document.getElementById('file-upload');
    const mainHeader = document.getElementById('main-header');
    const imageUpload = document.getElementById('image-upload');
    const imagePreviewModal = document.getElementById('image-preview-modal');
    const previewImage = document.getElementById('preview-image');
    const closePreview = document.getElementById('close-preview');
    const cancelUpload = document.getElementById('cancel-upload');
    const confirmUpload = document.getElementById('confirm-upload');

    let selectedFile = null;

    // Function to add a message to the chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = isUser ? 'U' : 'AI';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Convert newlines to <br> tags and preserve whitespace
        messageContent.innerHTML = content.replace(/\n/g, '<br>');

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageContent;
    }

    // Function to show typing indicator
    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return indicator;
    }

    // Function to update mode indicator
    function updateModeIndicator(mode) {
        currentMode.textContent = mode.charAt(0).toUpperCase() + mode.slice(1);
        modeIndicator.classList.add('active');
        setTimeout(() => modeIndicator.classList.remove('active'), 2000);
    }

    // Function to handle file download
    function downloadFile(content, filename) {
        // Create new PDF document
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Set font styles
        doc.setFont("helvetica", "bold");
        doc.setFontSize(16);
            
        // Add title
        doc.text("Analysis Report", 105, 20, { align: "center" });
        
        // Add timestamp
        doc.setFontSize(10);
        const timestamp = new Date().toLocaleString();
        doc.text(`Generated on: ${timestamp}`, 105, 30, { align: "center" });
        
        // Add separator line
        doc.setDrawColor(0);
        doc.line(20, 35, 190, 35);
        
        // Add content
        doc.setFont("helvetica", "normal");
        doc.setFontSize(12);
        
        // Split content into lines and add to PDF
        const lines = content.split('\n');
        let y = 45;
        const lineHeight = 7;
        
        lines.forEach(line => {
            if (line.trim() === '') {
                y += lineHeight;
                return;
            }
            
            // Handle section headers
            if (line.startsWith('=')) {
                doc.setFont("helvetica", "bold");
                doc.setFontSize(14);
                y += lineHeight;
                doc.text("Analysis Details", 20, y);
                doc.setFont("helvetica", "normal");
                doc.setFontSize(12);
                y += lineHeight * 2;
                return;
            }
            
            // Handle bullet points
            if (line.startsWith('•')) {
                doc.text(line, 25, y);
            } else {
                doc.text(line, 20, y);
            }
            
            y += lineHeight;
            
            // Add new page if needed
            if (y > 270) {
                doc.addPage();
                y = 20;
            }
        });
        
        // Save the PDF
        doc.save(filename.replace('.txt', '.pdf'));
    }

    // Handle image upload
    imageUpload.addEventListener('change', handleImageSelect);
    fileUpload.addEventListener('change', handleFileSelect);
    closePreview.addEventListener('click', closeImagePreview);
    cancelUpload.addEventListener('click', closeImagePreview);
    confirmUpload.addEventListener('click', handleImageUpload);

    function handleImageSelect(e) {
        const file = e.target.files[0];
        if (file && file.type.startsWith('image/')) {
            selectedFile = file;
            showImagePreview(file);
        } else {
            alert('Please select a valid image file (PNG, JPG, JPEG, or DICOM)');
            imageUpload.value = '';
        }
    }

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            uploadFile(file);
        }
    }

    function showImagePreview(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            imagePreviewModal.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }

    function closeImagePreview() {
        imagePreviewModal.classList.add('hidden');
        previewImage.src = '';
        selectedFile = null;
        imageUpload.value = '';
    }

    function handleImageUpload() {
        if (selectedFile) {
            uploadFile(selectedFile);
            closeImagePreview();
        }
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Show uploading message with image preview
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                addMessage(`Uploading ${file.name}...`, true);
            };
            reader.readAsDataURL(file);
        } else {
            addMessage(`Uploading ${file.name}...`, true);
        }

        // Show typing indicator
        const typingIndicator = showTypingIndicator();

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            typingIndicator.remove();

            if (data.error) {
                addMessage(`Error: ${data.error}`);
            } else {
                addMessage(data.response);
                if (data.mode) {
                    updateModeIndicator(data.mode);
                }
            }
        })
        .catch(error => {
            typingIndicator.remove();
            addMessage('Error: Failed to upload file. Please try again.');
            console.error('Error:', error);
        });
    }

    // Handle form submission with streaming
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, true);
        messageInput.value = '';

        // Add assistant message placeholder
        const messageContent = addMessage('', false);

        // Show typing indicator
        const typingIndicator = showTypingIndicator();

        try {
            const response = await fetch('/api/chat_stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            typingIndicator.remove();

            if (!response.body) {
                messageContent.innerHTML = 'Error: No response body.';
                return;
            }

            const reader = response.body.getReader();
            let fullText = '';
            let mode = 'chat';
            let documentData = null;

            const decoder = new TextDecoder();
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.error) {
                                messageContent.innerHTML = `Error: ${data.error}`;
                                return;
                            }

                            if (data.document) {
                                documentData = data.document;
                            }

                            if (data.response) {
                                fullText += data.response;
                                messageContent.innerHTML = fullText.replace(/\n/g, '<br>');
                            }

                            if (data.mode) {
                                mode = data.mode;
                                updateModeIndicator(mode);
                            }
                        } catch (e) {
                            console.error('Error parsing SSE data:', e);
                        }
                    }
                }
            }

            // Handle document download if available
            if (documentData) {
                downloadFile(documentData.content, documentData.filename);
            }

        } catch (error) {
            typingIndicator.remove();
            messageContent.innerHTML = 'Error: Failed to get response. Please try again.';
            console.error('Error:', error);
        }
    });

    // Handle Enter key
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Add welcome message
    addMessage('Hello! I\'m your AI assistant. I can help you with:\n\n' +
              '📧 Writing and sending emails\n' +
              '📊 Analyzing data from CSV/Excel files\n' +
              '🖼️ Analyzing breast MRI scans\n' +
              '💬 General chat and assistance\n\n' +
              'How can I help you today?');

    // Header minimization on scroll
    chatMessages.addEventListener('scroll', () => {
        if (chatMessages.scrollTop > 60) {
            mainHeader.classList.add('minimized');
        } else {
            mainHeader.classList.remove('minimized');
        }
    });
}); 
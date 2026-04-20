// Main JavaScript file for ExamAutoPro

// Utility Functions
const ExamAutoPro = {
    // Initialize the application
    init() {
        this.setupEventListeners();
        this.initializeTooltips();
        this.setupAutoRefresh();
        this.initializeDateTimePickers();
    },

    // Setup event listeners
    setupEventListeners() {
        // Handle form submissions
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Handle confirmations
        document.addEventListener('click', this.handleConfirmations.bind(this));
        
        // Handle file uploads
        document.addEventListener('change', this.handleFileUpload.bind(this));
        
        // Handle tab switching detection
        document.addEventListener('visibilitychange', this.handleTabSwitch.bind(this));
        
        // Handle copy/paste detection
        document.addEventListener('copy', this.handleCopyPaste.bind(this));
        document.addEventListener('paste', this.handleCopyPaste.bind(this));
        
        // Handle right-click detection
        document.addEventListener('contextmenu', this.handleRightClick.bind(this));
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    },

    // Initialize Bootstrap tooltips
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    // Setup auto-refresh for dashboards
    setupAutoRefresh() {
        // Only auto-refresh on dashboard pages
        if (window.location.pathname.includes('dashboard')) {
            setInterval(() => {
                this.refreshDashboard();
            }, 60000); // Refresh every 60 seconds
        }
    },

    // Initialize date/time pickers
    initializeDateTimePickers() {
        const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
        dateInputs.forEach(input => {
            // Set minimum date to current date/time
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            input.min = now.toISOString().slice(0, 16);
        });
    },

    // Handle form submissions
    handleFormSubmit(event) {
        const form = event.target;
        const submitBtn = form.querySelector('[type="submit"]');
        
        // Don't disable if it's the PDF upload form (handled specifically)
        if (form.id === 'pdf-upload-form') return;

        if (submitBtn) {
            // Show loading state
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            submitBtn.disabled = true;
            
            // Reset after 10 seconds (in case of slow network/errors)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 10000);
        }
    },

    // Handle confirmation dialogs
    handleConfirmations(event) {
        const target = event.target;
        
        if (target.hasAttribute('data-confirm')) {
            const message = target.getAttribute('data-confirm');
            if (!confirm(message)) {
                event.preventDefault();
                return false;
            }
        }
    },

    // Handle file uploads
    handleFileUpload(event) {
        const input = event.target;
        if (input.type === 'file' && input.files.length > 0) {
            const file = input.files[0];
            const maxSize = 50 * 1024 * 1024; // 50MB (matched with forms.py)
            
            if (file.size > maxSize) {
                alert('File size must be less than 50MB');
                input.value = '';
                return;
            }
            
            // Show file info
            const fileInfo = document.createElement('div');
            fileInfo.className = 'alert alert-info mt-2';
            fileInfo.innerHTML = `
                <i class="fas fa-file me-2"></i>
                Selected: ${file.name} (${this.formatFileSize(file.size)})
            `;
            
            // Remove existing file info
            const existingInfo = input.parentNode.querySelector('.alert');
            if (existingInfo) {
                existingInfo.remove();
            }
            
            input.parentNode.appendChild(fileInfo);
        }
    },

    // Format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Handle tab switching (for proctoring)
    handleTabSwitch() {
        if (document.hidden) {
            // Log tab switch event
            this.logProctoringEvent('tab_switch', {
                timestamp: new Date().toISOString(),
                page: window.location.pathname
            });
        }
    },

    // Handle copy/paste events (for proctoring)
    handleCopyPaste(event) {
        const eventType = event.type === 'copy' ? 'copy' : 'paste';
        this.logProctoringEvent(eventType, {
            timestamp: new Date().toISOString(),
            target: event.target.tagName,
            page: window.location.pathname
        });
    },

    // Handle right-click (for proctoring)
    handleRightClick(event) {
        this.logProctoringEvent('right_click', {
            timestamp: new Date().toISOString(),
            target: event.target.tagName,
            page: window.location.pathname
        });
    },

    // Handle keyboard shortcuts (for proctoring)
    handleKeyboardShortcuts(event) {
        // Detect common shortcuts
        const shortcuts = [
            { keys: ['Ctrl', 'c'], name: 'copy' },
            { keys: ['Ctrl', 'v'], name: 'paste' },
            { keys: ['Ctrl', 'x'], name: 'cut' },
            { keys: ['F5'], name: 'refresh' },
            { keys: ['F11'], name: 'fullscreen' },
            { keys: ['Alt', 'Tab'], name: 'alt_tab' }
        ];
        
        shortcuts.forEach(shortcut => {
            if (this.isShortcutPressed(event, shortcut.keys)) {
                this.logProctoringEvent('keyboard_shortcut', {
                    shortcut: shortcut.name,
                    timestamp: new Date().toISOString(),
                    page: window.location.pathname
                });
            }
        });
    },

    // Check if shortcut is pressed
    isShortcutPressed(event, keys) {
        const pressedKeys = [];
        
        if (event.ctrlKey) pressedKeys.push('Ctrl');
        if (event.altKey) pressedKeys.push('Alt');
        if (event.shiftKey) pressedKeys.push('Shift');
        if (event.key) pressedKeys.push(event.key);
        
        return keys.every(key => pressedKeys.includes(key));
    },

    // Log proctoring events
    logProctoringEvent(eventType, metadata) {
        // Only log if we're in an exam context
        if (window.location.pathname.includes('take_exam')) {
            const sessionId = this.getProctoringSessionId();
            
            if (sessionId) {
                fetch(`/proctoring/event/${sessionId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify({
                        event_type: eventType,
                        severity: 'low',
                        description: `${eventType} detected`,
                        metadata: metadata
                    })
                }).catch(error => {
                    console.error('Failed to log proctoring event:', error);
                });
            }
        }
    },

    // Get proctoring session ID
    getProctoringSessionId() {
        return localStorage.getItem('proctoring_session_id') || 
               sessionStorage.getItem('proctoring_session_id');
    },

    // Get CSRF token
    getCSRFToken() {
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    },

    // Refresh dashboard data
    refreshDashboard() {
        // Only refresh if page is visible
        if (!document.hidden) {
            fetch(window.location.pathname, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                // Update specific parts of the page
                this.updateDashboardContent(html);
            })
            .catch(error => {
                console.error('Dashboard refresh failed:', error);
            });
        }
    },

    // Update dashboard content
    updateDashboardContent(html) {
        // This is a simplified version - in production, you'd want to
        // update specific elements based on the response
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Update statistics cards
        const statsCards = doc.querySelectorAll('.stats-card');
        const currentStatsCards = document.querySelectorAll('.stats-card');
        
        statsCards.forEach((card, index) => {
            if (currentStatsCards[index]) {
                currentStatsCards[index].innerHTML = card.innerHTML;
            }
        });
    },

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },

    // Initialize exam timer
    initExamTimer(duration, onTimeUp) {
        let timeRemaining = duration * 60; // Convert minutes to seconds
        
        const timer = setInterval(() => {
            timeRemaining--;
            
            const hours = Math.floor(timeRemaining / 3600);
            const minutes = Math.floor((timeRemaining % 3600) / 60);
            const seconds = timeRemaining % 60;
            
            const display = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            const timerElement = document.getElementById('exam-timer');
            if (timerElement) {
                timerElement.textContent = display;
                
                // Change color when time is running out
                if (timeRemaining < 300) { // Less than 5 minutes
                    timerElement.className = 'text-danger';
                } else if (timeRemaining < 600) { // Less than 10 minutes
                    timerElement.className = 'text-warning';
                }
            }
            
            if (timeRemaining <= 0) {
                clearInterval(timer);
                if (onTimeUp) {
                    onTimeUp();
                }
            }
        }, 1000);
        
        return timer;
    },

    // Validate exam form
    validateExamForm() {
        const form = document.getElementById('exam-form');
        if (!form) return true;
        
        const title = form.querySelector('#id_title').value.trim();
        const duration = parseInt(form.querySelector('#id_duration').value);
        const startTime = form.querySelector('#id_start_time').value;
        const endTime = form.querySelector('#id_end_time').value;
        
        if (!title) {
            this.showNotification('Please enter an exam title', 'danger');
            return false;
        }
        
        if (duration < 1 || duration > 480) { // Max 8 hours
            this.showNotification('Duration must be between 1 and 480 minutes', 'danger');
            return false;
        }
        
        if (!startTime || !endTime) {
            this.showNotification('Please select start and end times', 'danger');
            return false;
        }
        
        if (new Date(startTime) >= new Date(endTime)) {
            this.showNotification('End time must be after start time', 'danger');
            return false;
        }
        
        return true;
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ExamAutoPro.init();
});

// Export for global access
window.ExamAutoPro = ExamAutoPro;

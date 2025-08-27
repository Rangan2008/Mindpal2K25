/**
 * MindPal Enhanced UI Interactions
 * Classy and soothing animations for stress management platform
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeInteractiveElements();
    initializeAccessibility();
    initializeWellnessFeatures();
});

/**
 * Initialize scroll-triggered animations
 */
function initializeAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
                
                // Stagger animation for child elements
                const children = entry.target.querySelectorAll('.feature-card, .dashboard-card');
                children.forEach((child, index) => {
                    setTimeout(() => {
                        child.classList.add('animate');
                    }, index * 100);
                });
            }
        });
    }, observerOptions);

    // Observe elements with animation classes
    document.querySelectorAll('.fade-in, .slide-up, .card-grid').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Initialize interactive UI elements
 */
function initializeInteractiveElements() {
    // Enhanced button hover effects
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Card hover effects with 3D tilt
    document.querySelectorAll('.feature-card, .dashboard-card').forEach(card => {
        card.addEventListener('mouseenter', function(e) {
            this.style.transform = 'translateY(-8px) rotateX(5deg)';
            this.style.boxShadow = '0 20px 40px rgba(74, 144, 226, 0.2)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) rotateX(0)';
            this.style.boxShadow = '';
        });

        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            this.style.transform = `translateY(-8px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
    });

    // Progress bar animations
    document.querySelectorAll('.progress-fill').forEach(progressBar => {
        const targetWidth = progressBar.style.width;
        progressBar.style.width = '0%';
        
        setTimeout(() => {
            progressBar.style.width = targetWidth;
        }, 500);
    });

    // Floating labels for forms
    document.querySelectorAll('.form-input').forEach(input => {
        const parent = input.parentElement;
        
        input.addEventListener('focus', () => {
            parent.classList.add('focused');
        });
        
        input.addEventListener('blur', () => {
            if (!input.value.trim()) {
                parent.classList.remove('focused');
            }
        });
        
        // Check if input has value on load
        if (input.value.trim()) {
            parent.classList.add('focused');
        }
    });
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Keyboard navigation for custom elements
    document.querySelectorAll('.mood-btn, .music-btn').forEach(btn => {
        btn.setAttribute('tabindex', '0');
        
        btn.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    // Focus management for modals
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this);
            }
        });
    });

    // Escape key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal-overlay.active');
            if (activeModal) {
                closeModal(activeModal);
            }
        }
    });
}

/**
 * Initialize wellness-specific features
 */
function initializeWellnessFeatures() {
    // Breathing exercise visual feedback
    initializeBreathingExercise();
    
    // Mood tracking animations
    initializeMoodTracking();
    
    // Stress level indicators
    initializeStressIndicators();
    
    // Motivational messages
    initializeMotivationalMessages();
}

/**
 * Enhanced breathing exercise with visual guidance
 */
function initializeBreathingExercise() {
    const breathingCircles = document.querySelectorAll('.breathing-exercise, .breathing-circle');
    
    breathingCircles.forEach(circle => {
        circle.addEventListener('click', function() {
            startBreathingAnimation(this);
        });
    });
}

function startBreathingAnimation(element) {
    let isAnimating = element.dataset.animating === 'true';
    
    if (isAnimating) {
        stopBreathingAnimation(element);
        return;
    }
    
    element.dataset.animating = 'true';
    element.classList.add('breathing-active');
    
    const breathingCycle = () => {
        if (element.dataset.animating !== 'true') return;
        
        // Inhale phase (4 seconds)
        element.style.transform = 'scale(1.2)';
        element.style.background = 'radial-gradient(circle, rgba(74, 144, 226, 0.3) 0%, rgba(94, 197, 167, 0.1) 100%)';
        
        setTimeout(() => {
            if (element.dataset.animating !== 'true') return;
            
            // Hold phase (4 seconds)
            element.style.background = 'radial-gradient(circle, rgba(142, 124, 195, 0.3) 0%, rgba(74, 144, 226, 0.1) 100%)';
            
            setTimeout(() => {
                if (element.dataset.animating !== 'true') return;
                
                // Exhale phase (6 seconds)
                element.style.transform = 'scale(1)';
                element.style.background = 'radial-gradient(circle, rgba(94, 197, 167, 0.2) 0%, transparent 70%)';
                
                setTimeout(() => {
                    breathingCycle(); // Repeat cycle
                }, 6000);
            }, 4000);
        }, 4000);
    };
    
    breathingCycle();
    
    // Show breathing instructions
    showNotification('Follow the circle: Inhale as it grows, hold, then exhale as it shrinks. Click again to stop.', 'info');
}

function stopBreathingAnimation(element) {
    element.dataset.animating = 'false';
    element.classList.remove('breathing-active');
    element.style.transform = 'scale(1)';
    element.style.background = '';
}

/**
 * Mood tracking with visual feedback
 */
function initializeMoodTracking() {
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const mood = this.dataset.mood;
            const icon = this.querySelector('i');
            
            // Animate the selected mood
            this.style.transform = 'scale(1.1)';
            this.style.background = 'var(--gradient-primary)';
            this.style.color = 'white';
            
            // Create ripple effect
            createRippleEffect(this);
            
            // Reset after animation
            setTimeout(() => {
                this.style.transform = '';
                this.style.background = '';
                this.style.color = '';
            }, 2000);
            
            // Show personalized response
            showMoodFeedback(mood);
        });
    });
}

function showMoodFeedback(mood) {
    const messages = {
        excellent: "Wonderful! You're radiating positive energy. Keep it up! ✨",
        good: "Great to hear you're doing well! What's making you feel good today? 😊",
        okay: "That's perfectly normal. Some days are just okay, and that's fine. 💙",
        struggling: "I hear you. Remember, it's okay to not be okay. Consider trying a breathing exercise. 🫂",
        overwhelmed: "Take a deep breath. You're stronger than you think. Let's find some calm together. 🌟"
    };
    
    const encouragements = {
        excellent: "Maybe share your positive energy with a friend today!",
        good: "This is a good time to tackle that goal you've been putting off.",
        okay: "How about listening to some calming music?",
        struggling: "Consider reaching out to someone you trust.",
        overwhelmed: "Let's break things down into smaller, manageable steps."
    };
    
    const message = messages[mood];
    const encouragement = encouragements[mood];
    
    setTimeout(() => {
        showNotification(`${message} ${encouragement}`, mood === 'struggling' || mood === 'overwhelmed' ? 'warning' : 'success');
    }, 900);
}

/**
 * Stress level visual indicators
 */
function initializeStressIndicators() {
    const stressIndicators = document.querySelectorAll('.stress-indicator');
    
    stressIndicators.forEach(indicator => {
        const level = parseInt(indicator.dataset.stress) || 0;
        updateStressIndicator(indicator, level);
    });
}

function updateStressIndicator(indicator, level) {
    const colors = {
        low: '#5ec5a7',
        medium: '#f4d03f',
        high: '#f5576c'
    };
    
    let color, message;
    
    if (level <= 3) {
        color = colors.low;
        message = 'Low stress - you\'re doing great!';
    } else if (level <= 6) {
        color = colors.medium;
        message = 'Moderate stress - consider taking a break';
    } else {
        color = colors.high;
        message = 'High stress - time for self-care';
    }
    
    indicator.style.background = `linear-gradient(90deg, ${color} ${level * 10}%, #e9ecef ${level * 10}%)`;
    indicator.setAttribute('title', message);
}

/**
 * Motivational messages system
 */
function initializeMotivationalMessages() {
    const messages = [
        "Remember: You're braver than you believe and stronger than you seem. 💪",
        "Taking care of your mental health is just as important as your physical health. 🧠",
        "Small steps every day lead to big changes over time. Keep going! 🌱",
        "It's okay to take breaks. Rest is not a reward for work completed, but a necessity. 🛋️",
        "You don't have to be perfect. You just have to be you. ✨",
        "Progress, not perfection. Every small step counts. 👣",
        "Your mental health matters. You matter. 💝"
    ];
    
    // Show a random motivational message occasionally
    if (Math.random() < 0.3) { // 30% chance
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        
        setTimeout(() => {
            showNotification(randomMessage, 'info');
        }, 10000); // Increased from 3000ms to 10000ms
    }
}

/**
 * Utility functions
 */
function createRippleEffect(element) {
    const ripple = document.createElement('div');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    
    ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        width: ${size}px;
        height: ${size}px;
        left: 50%;
        top: 50%;
        margin-left: -${size/2}px;
        margin-top: -${size/2}px;
        pointer-events: none;
    `;
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

function closeModal(modal) {
    modal.classList.remove('active');
    
    // Stop any ongoing animations
    if (modal.id === 'breathing-modal') {
        const breathingElement = modal.querySelector('.breathing-circle-large');
        if (breathingElement) {
            stopBreathingAnimation(breathingElement);
        }
    }
}

// Enhanced notification system
function showEnhancedNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} fade-in enhanced-notification`;
    
    const icons = {
        success: 'check-circle',
        error: 'exclamation-triangle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${icons[type]}" aria-hidden="true"></i>
            <span class="notification-text">${message}</span>
            <button class="alert-close" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="notification-progress"></div>
    `;
    
    // Position notification
    const container = document.querySelector('.flash-messages') || document.body;
    container.appendChild(notification);
    
    // Animate progress bar
    const progressBar = notification.querySelector('.notification-progress');
    progressBar.style.animation = `notification-progress ${duration}ms linear`;
    
    // Close functionality
    const closeBtn = notification.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
        notification.classList.add('slide-out');
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto-close
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('slide-out');
            setTimeout(() => notification.remove(), 300);
        }
    }, duration);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    @keyframes notification-progress {
        from { width: 100%; }
        to { width: 0%; }
    }
    
    .enhanced-notification {
        position: relative;
        overflow: hidden;
        margin-bottom: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 1.25rem;
    }
    
    .notification-text {
        flex: 1;
        font-weight: 500;
    }
    
    .notification-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        background: rgba(255, 255, 255, 0.3);
        width: 100%;
    }
    
    .slide-out {
        transform: translateX(100%);
        opacity: 0;
        transition: all 0.3s ease-out;
    }
    
    .breathing-active {
        box-shadow: 0 0 30px rgba(74, 144, 226, 0.5);
        transition: all 0.3s ease-in-out;
    }
    
    .animate {
        opacity: 1;
        transform: translateY(0);
        transition: all 0.6s ease-out;
    }
    
    .fade-in:not(.animate) {
        opacity: 0;
        transform: translateY(20px);
    }
    
    .slide-up:not(.animate) {
        opacity: 0;
        transform: translateY(30px);
    }
`;

document.head.appendChild(style);

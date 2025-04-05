document.addEventListener('DOMContentLoaded', () => {
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize section animations
    initSectionAnimations();
    
    // Initialize count-up effect for statistics
    initCountUp();
    
    // Initialize header scroll effect
    initScrollHeader();
    
    // Smooth scrolling for navigation links
    initSmoothScrolling();

    // Form submission
    initFormSubmission();
    
    // Feature card hover effect
    initFeatureCards();
});

// Mobile Menu Toggle
function initMobileMenu() {
    const menuToggle = document.createElement('div');
    menuToggle.className = 'mobile-menu-toggle';
    menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
    
    const nav = document.querySelector('nav');
    const navLinks = document.querySelector('.nav-links');
    
    if (nav && !document.querySelector('.mobile-menu-toggle')) {
        nav.insertBefore(menuToggle, navLinks);
        
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            menuToggle.innerHTML = navLinks.classList.contains('active') 
                ? '<i class="fas fa-times"></i>' 
                : '<i class="fas fa-bars"></i>';
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !menuToggle.contains(e.target) && navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
    }
}

// Section Animations
function initSectionAnimations() {
    const sections = document.querySelectorAll('section');
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                sectionObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    sections.forEach(section => {
        sectionObserver.observe(section);
    });
}

// Count-up Animation for Statistics
function initCountUp() {
    const stats = document.querySelectorAll('.stat h3');
    const options = {
        root: null,
        rootMargin: '0px',
        threshold: 0.5
    };
    
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const valueText = target.textContent;
                const prefix = valueText.match(/^\D*/)[0] || '';
                let targetValue = parseFloat(valueText.replace(/[^\d.]/g, ''));
                const suffix = valueText.includes('+') ? '+' : '';
                
                if (!isNaN(targetValue)) {
                    // Add a "viewed" class to the parent element for additional styling
                    target.parentElement.classList.add('viewed');
                    
                    let startValue = 0;
                    const duration = 2500; // Slightly longer animation
                    const increment = targetValue / (duration / 16);
                    
                    target.textContent = prefix + '0' + suffix;
                    
                    const updateCounter = () => {
                        startValue += increment;
                        if (startValue < targetValue) {
                            if (targetValue >= 1000) {
                                // Add commas for thousands separator
                                const formattedValue = Math.ceil(startValue).toLocaleString();
                                target.textContent = prefix + formattedValue + suffix;
                            } else {
                                target.textContent = prefix + Math.ceil(startValue) + suffix;
                            }
                            requestAnimationFrame(updateCounter);
                        } else {
                            if (targetValue >= 1000) {
                                const formattedValue = Math.ceil(targetValue).toLocaleString();
                                target.textContent = prefix + formattedValue + suffix;
                            } else {
                                target.textContent = prefix + Math.ceil(targetValue) + suffix;
                            }
                            
                            // Apply a scaling animation when count is complete
                            target.style.transform = 'scale(1.1)';
                            setTimeout(() => {
                                target.style.transform = 'scale(1)';
                            }, 200);
                        }
                    };
                    
                    requestAnimationFrame(updateCounter);
                    statsObserver.unobserve(target);
                }
            }
        });
    }, options);
    
    stats.forEach(stat => {
        statsObserver.observe(stat);
    });
}

// Header Scroll Effect
function initScrollHeader() {
    const header = document.querySelector('header');
    
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }
}

// Smooth Scrolling
function initSmoothScrolling() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    // Add scroll functionality to the existing scroll indicator
    const scrollIndicator = document.querySelector('.scroll-indicator');
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', () => {
            const heroSection = document.getElementById('hero');
            const nextSection = heroSection.nextElementSibling;
            if (nextSection) {
                const headerHeight = document.querySelector('header').offsetHeight;
                const elementPosition = nextSection.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.scrollY - headerHeight;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    }
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            
            // Close mobile menu if open
            const navLinks = document.querySelector('.nav-links');
            if (navLinks && navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                const menuToggle = document.querySelector('.mobile-menu-toggle');
                if (menuToggle) {
                    menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
                }
            }
            
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerHeight = document.querySelector('header').offsetHeight;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.scrollY - headerHeight;
                
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Form Submission
function initFormSubmission() {
    const leadForm = document.getElementById('lead-form');
    const formStatus = document.getElementById('form-status');

    if (leadForm) {
        // Add icons to form inputs
        enhanceFormInputs();
        
        leadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Show loading state
            const submitButton = leadForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            submitButton.disabled = true;
            
            // Prepare form data
            const formData = new FormData(leadForm);
            const data = {
                name: formData.get('name') || '',
                email: formData.get('email') || '',
                phone: formData.get('phone') || '123-456-7890', // Default value if not provided
                message: `Company: ${formData.get('company')}, Network Type: ${formData.get('network')}`,
            };

            try {
                // Send data to backend
                const response = await fetch('/submit_lead', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                
                // Show success or error message
                formStatus.classList.remove('hidden', 'success', 'error');
                
                if (result.message && !result.error) {
                    // Success
                    formStatus.innerHTML = `<i class="fas fa-check-circle"></i> ${result.message || 'Demo requested successfully!'}`;
                    formStatus.classList.add('success');
                    leadForm.reset();
                    
                    // If user consented to newsletter, show additional confirmation
                    if (formData.get('newsletter_consent') === 'on') {
                        const newsConfirmation = document.createElement('p');
                        newsConfirmation.innerHTML = '<strong>Thanks for subscribing!</strong> Please check your email to confirm your subscription.';
                        formStatus.appendChild(newsConfirmation);
                    }
                } else {
                    // Error
                    formStatus.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${result.error || 'Something went wrong. Please try again.'}`;
                    formStatus.classList.add('error');
                }
            } catch (error) {
                console.error('Error:', error);
                formStatus.classList.remove('hidden');
                formStatus.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Network error. Please try again later.';
                formStatus.classList.add('error');
            } finally {
                // Reset button state
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
                
                // Scroll to form status
                setTimeout(() => {
                    formStatus.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
                
                // Hide status message after 5 seconds
                setTimeout(() => {
                    formStatus.classList.add('hidden');
                }, 5000);
            }
        });
    }
}

// Enhance form inputs with icons
function enhanceFormInputs() {
    // Update CTA button with icon and microcopy
    const ctaButtons = document.querySelectorAll('.cta-button');
    ctaButtons.forEach(button => {
        if (!button.querySelector('i') && button.textContent.includes('Demo')) {
            const text = button.textContent;
            button.innerHTML = `<i class="fas fa-calendar-check"></i> ${text}`;
            if (button.closest('#hero')) {
                button.innerHTML += '<span class="microcopy">No credit card needed</span>';
            }
        }
    });
    
    // Style the form submit button
    const submitButton = document.querySelector('.submit-button');
    if (submitButton && !submitButton.querySelector('i')) {
        submitButton.innerHTML = `<i class="fas fa-paper-plane"></i> ${submitButton.textContent}`;
    }
}

// Feature card hover effects
function initFeatureCards() {
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            const icon = card.querySelector('.feature-icon i');
            if (icon) {
                icon.classList.add('fa-bounce');
            }
        });
        
        card.addEventListener('mouseleave', () => {
            const icon = card.querySelector('.feature-icon i');
            if (icon) {
                icon.classList.remove('fa-bounce');
            }
        });
    });
} 
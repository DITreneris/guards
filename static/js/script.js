document.addEventListener('DOMContentLoaded', () => {
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize section animations with IntersectionObserver
    initSectionAnimations();
    
    // Initialize count-up effect for statistics
    initCountUp();
    
    // Initialize header scroll effect with debounce
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
        
        // Close menu when clicking outside - delegated event
        document.addEventListener('click', (e) => {
            if (!navLinks.contains(e.target) && !menuToggle.contains(e.target) && navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
    }
}

// Section Animations with IntersectionObserver
function initSectionAnimations() {
    const sections = document.querySelectorAll('section');
    if (!sections.length) return;
    
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

// Count-up Animation for Statistics using IntersectionObserver
function initCountUp() {
    const stats = document.querySelectorAll('.stat h3');
    if (!stats.length) return;
    
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
                    const duration = 2500;
                    const increment = targetValue / (duration / 16);
                    
                    target.textContent = prefix + '0' + suffix;
                    
                    const updateCounter = () => {
                        startValue += increment;
                        if (startValue < targetValue) {
                            const formattedValue = Math.ceil(startValue).toLocaleString();
                            target.textContent = prefix + formattedValue + suffix;
                            requestAnimationFrame(updateCounter);
                        } else {
                            const formattedValue = Math.ceil(targetValue).toLocaleString();
                            target.textContent = prefix + formattedValue + suffix;
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

// Header Scroll Effect with Debounce
function initScrollHeader() {
    const header = document.querySelector('header');
    if (!header) return;
    
    // Simple debounce function
    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }
    
    // Use requestAnimationFrame for smoother scrolling effect
    let lastScrollPosition = 0;
    let ticking = false;
    
    function updateHeaderClass() {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        ticking = false;
    }
    
    window.addEventListener('scroll', () => {
        lastScrollPosition = window.scrollY;
        if (!ticking) {
            window.requestAnimationFrame(() => {
                updateHeaderClass();
                ticking = false;
            });
            ticking = true;
        }
    });
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

// Form Submission with validation
function initFormSubmission() {
    const leadForm = document.getElementById('lead-form');
    const formStatus = document.getElementById('form-status');

    if (!leadForm) return;
    
    // Add validation before submission
    leadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Validate form
        const nameInput = leadForm.querySelector('input[name="name"]');
        const emailInput = leadForm.querySelector('input[name="email"]');
        
        if (!nameInput.value.trim()) {
            formStatus.innerHTML = '<div class="error">Please enter your name</div>';
            return;
        }
        
        if (!emailInput.value.trim() || !isValidEmail(emailInput.value)) {
            formStatus.innerHTML = '<div class="error">Please enter a valid email address</div>';
            return;
        }
        
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
            phone: formData.get('phone') || '',
            message: `Company: ${formData.get('company') || 'Not provided'}, Network Type: ${formData.get('network') || 'Not provided'}`,
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

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const result = await response.json();
            
            // Reset form on success
            leadForm.reset();
            
            // Show success message
            formStatus.innerHTML = '<div class="success">Thank you! We will contact you shortly.</div>';
        } catch (error) {
            formStatus.innerHTML = '<div class="error">Something went wrong. Please try again later.</div>';
        } finally {
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
        }
    });
}

// Email validation helper
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Feature Cards Interaction
function initFeatureCards() {
    const featureCards = document.querySelectorAll('.feature-card');
    if (!featureCards.length) return;
    
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.classList.add('active');
        });
        
        card.addEventListener('mouseleave', () => {
            card.classList.remove('active');
        });
    });
} 
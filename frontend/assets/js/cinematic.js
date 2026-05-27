document.addEventListener('DOMContentLoaded', () => {
    // Background Slideshow (Simulating Video Pan/Zoom)
    const slides = document.querySelectorAll('.bg-slide');
    if (slides.length > 0) {
        let currentSlide = 0;
        
        setInterval(() => {
            slides[currentSlide].classList.remove('active');
            currentSlide = (currentSlide + 1) % slides.length;
            slides[currentSlide].classList.add('active');
        }, 8000); // Changed to 8s for slower, more cinematic video-like feel
    }

    // Particles JS Configuration
    if (document.getElementById('particles-js') && typeof particlesJS !== 'undefined') {
        particlesJS("particles-js", {
            "particles": {
                "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
                "color": { "value": ["#ffffff", "#22c55e", "#4ade80"] },
                "shape": { "type": "circle" },
                "opacity": {
                    "value": 0.4, "random": true,
                    "anim": { "enable": true, "speed": 1, "opacity_min": 0.1, "sync": false }
                },
                "size": {
                    "value": 4, "random": true,
                    "anim": { "enable": true, "speed": 2, "size_min": 0.1, "sync": false }
                },
                "line_linked": { "enable": false },
                "move": {
                    "enable": true, "speed": 0.8, "direction": "top",
                    "random": true, "straight": false, "out_mode": "out", "bounce": false,
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": { "enable": true, "mode": "bubble" },
                    "onclick": { "enable": true, "mode": "repulse" },
                    "resize": true
                },
                "modes": {
                    "bubble": { "distance": 250, "size": 8, "duration": 2, "opacity": 1, "speed": 3 },
                    "repulse": { "distance": 400, "duration": 0.4 }
                }
            },
            "retina_detect": true
        });
    }

    // --- Premium UI/UX Scroll Animations ---
    
    // Add base reveal class to all elements we want to animate
    const animatedSelectors = [
        '.section-tag', '.section-title', '.section-desc', 
        '.feat-card', '.mbar-item', 
        '.comp-table tr', '.class-pill', '.cd-card', 
        '.cta-inner', '.footer-col', '.footer-brand'
    ];
    
    animatedSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach((el, index) => {
            el.classList.add('reveal-on-scroll');
            // Stagger animation delays slightly for siblings
            if (el.parentNode) {
                const siblings = Array.from(el.parentNode.children);
                const i = siblings.indexOf(el);
                if (i > 0 && i < 10) {
                    el.style.transitionDelay = `${i * 0.1}s`;
                }
            }
        });
    });

    const revealOptions = {
        threshold: 0.15,
        rootMargin: "0px 0px -50px 0px"
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-revealed');
                observer.unobserve(entry.target);
            }
        });
    }, revealOptions);

    document.querySelectorAll('.reveal-on-scroll, .reveal-left, .reveal-right').forEach(el => revealObserver.observe(el));

    // --- Smooth Parallax for Hero Background ---
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const bg = document.querySelector('.cinematic-bg');
        const heroContent = document.querySelector('.cinematic-inner');
        
        if (bg && scrolled < window.innerHeight) {
            // Parallax background
            bg.style.transform = `translateY(${scrolled * 0.4}px)`;
            // Fade out content on scroll down
            if(heroContent) {
                heroContent.style.opacity = 1 - (scrolled / window.innerHeight) * 1.5;
                heroContent.style.transform = `translateY(${scrolled * 0.2}px)`;
            }
        }
    });
});

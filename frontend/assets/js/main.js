/* CIRCVIS Main — Professional Design */

document.addEventListener('DOMContentLoaded', async () => {
    setupScrollAnimations();
    setupNavScroll();
    setupSmoothScroll();

    // Optionally check backend
    try {
        if (typeof API_BASE !== 'undefined') {
            await initApiConnection();
        }
    } catch (e) { /* backend optional */ }
});

function setupNavScroll() {
    const nav = document.querySelector('.nav');
    if (!nav) return;
    window.addEventListener('scroll', () => {
        if (window.scrollY > 60) {
            nav.style.background = 'rgba(9,9,11,0.97)';
        } else {
            nav.style.background = 'rgba(9,9,11,0.85)';
        }
    }, { passive: true });
}

function setupScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feat-card, .cd-card, .mbar-item, .about-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
}

function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

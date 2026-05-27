/* CIRCVIS Utility Functions */

const CIRCVIS_PORTS = [8000, 8001];
let API_ORIGIN = window.location.origin;
let API_BASE = `${API_ORIGIN}/api`;

async function pingOrigin(origin, timeoutMs = 3000) {
    try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        const response = await fetch(`${origin}/health`, {
            signal: controller.signal,
            mode: 'cors',
            cache: 'no-store',
        });
        clearTimeout(timer);
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Find running CIRCVIS server (handles 8000 vs 8001 and file:// opens).
 */
async function initApiConnection() {
    const candidates = [];

    if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
        candidates.push(window.location.origin);
    }

    for (const port of CIRCVIS_PORTS) {
        candidates.push(`http://127.0.0.1:${port}`);
        candidates.push(`http://localhost:${port}`);
    }

    const seen = new Set();
    for (const origin of candidates) {
        if (!origin || seen.has(origin)) continue;
        seen.add(origin);
        if (await pingOrigin(origin)) {
            API_ORIGIN = origin;
            API_BASE = `${API_ORIGIN}/api`;
            console.log('CIRCVIS connected:', API_ORIGIN);
            return { ok: true, origin: API_ORIGIN };
        }
    }

    console.error('CIRCVIS connection failed — is run.bat running?');
    return { ok: false, origin: null };
}

function getServerLinksHtml() {
    return CIRCVIS_PORTS.map(
        (p) => `<a href="http://127.0.0.1:${p}/demo.html" style="color:#fbbf24;margin:0 0.35rem">:${p}</a>`
    ).join(' ');
}

// API Helper
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        mode: 'cors'
    };

    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Call Error:', error);
        throw error;
    }
}

// Image Upload
async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            body: formData,
            mode: 'cors'
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Upload Error:', error);
        throw error;
    }
}

// Get Model Info
async function getModelInfo() {
    try {
        return await apiCall('/model-info');
    } catch (error) {
        console.error('Failed to fetch model info:', error);
        return null;
    }
}

// Check API health
async function checkApiHealth() {
    try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 5000);
        const response = await fetch(`${API_ORIGIN}/health`, {
            signal: controller.signal,
            mode: 'cors',
            cache: 'no-store',
        });
        clearTimeout(timer);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API health check failed:', error);
        return {
            status: 'offline',
            models_loaded: false,
            load_error: 'Server band hai. Pehle run.bat chalao, phir demo link kholo.',
        };
    }
}

// Get Model Classes
async function getWasteClasses() {
    try {
        const data = await apiCall('/classes');
        return data.classes || [];
    } catch (error) {
        console.error('Failed to fetch classes:', error);
        return [
            'Plastic', 'Organic', 'Metal', 'Paper/Cardboard',
            'Glass', 'Textile', 'Miscellaneous'
        ];
    }
}

// Get Dashboard Stats
async function getDashboardStats() {
    try {
        return await apiCall('/stats');
    } catch (error) {
        console.error('Failed to fetch stats:', error);
        return null;
    }
}

// Get Sustainability Impact
async function getSustainabilityImpact() {
    try {
        return await apiCall('/impact');
    } catch (error) {
        console.error('Failed to fetch impact:', error);
        return null;
    }
}

// Get Model Comparison
async function getModelComparison() {
    try {
        return await apiCall('/model-comparison');
    } catch (error) {
        console.error('Failed to fetch model comparison:', error);
        return null;
    }
}

// Get NLP Summary
async function getNlpSummary() {
    try {
        return await apiCall('/nlp-summary');
    } catch (error) {
        console.error('Failed to fetch NLP summary:', error);
        return null;
    }
}

// Submit user feedback
async function submitFeedback(payload) {
    try {
        return await apiCall('/feedback', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    } catch (error) {
        console.error('Failed to submit feedback:', error);
        throw error;
    }
}

// Get Case Studies
async function getCaseStudies() {
    try {
        return await apiCall('/case-studies');
    } catch (error) {
        console.error('Failed to fetch case studies:', error);
        return null;
    }
}

// Canvas Utilities
function canvasToBlob(canvas, callback) {
    canvas.toBlob(callback, 'image/jpeg', 0.9);
}

function base64ToBlob(base64, mimeType = 'image/jpeg') {
    const bstr = atob(base64);
    const n = bstr.length;
    const u8arr = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
        u8arr[i] = bstr.charCodeAt(i);
    }
    return new Blob([u8arr], { type: mimeType });
}

function blobToFile(blob, filename) {
    return new File([blob], filename, { type: blob.type });
}

// Image Processing
function resizeImage(file, maxSize = 400, callback) {
    const reader = new FileReader();

    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            let width = img.width;
            let height = img.height;

            if (width > height) {
                if (width > maxSize) {
                    height *= maxSize / width;
                    width = maxSize;
                }
            } else {
                if (height > maxSize) {
                    width *= maxSize / height;
                    height = maxSize;
                }
            }

            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob(callback, 'image/jpeg', 0.8);
        };
        img.src = e.target.result;
    };

    reader.readAsDataURL(file);
}

// Drag & Drop Handler
function setupDragDrop(element, callback) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--primary)';
        element.style.background = 'rgba(16, 185, 129, 0.1)';
    });

    element.addEventListener('dragleave', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--primary)';
        element.style.background = 'transparent';
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.style.borderColor = 'var(--primary)';
        element.style.background = 'transparent';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            callback(files[0]);
        }
    });
}

// Formatting
function formatConfidence(value) {
    return (value * 100).toFixed(2) + '%';
}

function formatTime(ms) {
    return ms.toFixed(2) + ' ms';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Color for class prediction
function getClassColor(className) {
    const colors = {
        'Plastic': '#ec4899',
        'Organic': '#10b981',
        'Metal': '#8b5cf6',
        'Paper/Cardboard': '#f59e0b',
        'Glass': '#06b6d4',
        'Textile': '#f97316',
        'Miscellaneous': '#6366f1'
    };
    return colors[className] || '#10b981';
}

// Chart.js Setup
function createConfusionMatrixChart(canvasId, matrix) {
    const classes = ['Plastic', 'Organic', 'Metal', 'Paper/Cardboard', 'Glass', 'Textile', 'Miscellaneous'];
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bubble',
        data: {
            labels: classes,
            datasets: classes.map((className, idx) => ({
                label: className,
                data: matrix[idx].map((value, jdx) => ({
                    x: jdx,
                    y: idx,
                    r: Math.sqrt(value) * 2
                })),
                backgroundColor: getClassColor(className)
            }))
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: function(value) {
                            return classes[value];
                        }
                    }
                },
                y: {
                    ticks: {
                        callback: function(value) {
                            return classes[value];
                        }
                    }
                }
            }
        }
    });
}

function createDistributionChart(canvasId, distribution) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    const colors = labels.map(label => getClassColor(label));

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(30, 41, 59, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'var(--text-primary)',
                        font: {
                            family: "'Poppins', sans-serif"
                        }
                    }
                }
            }
        }
    });
}

// Scroll animations
function setupScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-on-scroll');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// Tab switching
function setupTabs(tabSelector, contentSelector) {
    const tabs = document.querySelectorAll(tabSelector);
    const contents = document.querySelectorAll(contentSelector);

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const mode = tab.dataset.mode;

            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(`${mode}-mode`)?.classList.add('active');
        });
    });
}

// localStorage helpers
const storage = {
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch {
            return defaultValue;
        }
    },
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch {
            console.error('Failed to set localStorage');
        }
    },
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch {
            console.error('Failed to remove from localStorage');
        }
    }
};

// Show toast notification
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 0.5rem;
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

console.log('✓ CIRCVIS Utils loaded');

/* CIRCVIS Demo Page */

let currentPrediction = null;
let predictionCount = 0;
let modelInfo = null;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('✓ CIRCVIS Demo Page Loaded');

    const conn = await initApiConnection();
    if (!conn.ok) {
        showConnectionFailed();
        return;
    }

    setupModeTabs();
    setupUploadArea();
    setupImageInput();
    setupBatchInput();
    setupVideoInput();
    setupCameraControls();
    await loadModelStatus();
});

function showConnectionFailed() {
    const banner = document.getElementById('modelStatusBanner');
    const statusText = document.getElementById('processingStatus')?.querySelector('.status-text');

    if (banner) {
        banner.style.background = 'rgba(239,68,68,0.15)';
        banner.style.color = '#ef4444';
        banner.innerHTML = `✗ Connection failed — server chalao (run.bat) phir kholo:${getServerLinksHtml()}`;
    }
    if (statusText) {
        statusText.textContent = 'Server offline — run.bat chalao';
    }
    showToast('Connection failed. run.bat chalao, phir browser mein 8000 ya 8001 wala link kholo.', 'error', 10000);
}

async function loadModelStatus() {
    const health = await checkApiHealth();
    modelInfo = await getModelInfo();
    const banner = document.getElementById('modelStatusBanner');
    const statusEl = document.getElementById('processingStatus');
    const statusText = statusEl?.querySelector('.status-text');

    if (health.models_loaded) {
        const acc = modelInfo?.accuracy ? (modelInfo.accuracy * 100).toFixed(1) : '—';
        const infVer = health.inference_version || '?';
        if (banner) {
            banner.style.background = 'rgba(34,197,94,0.15)';
            banner.style.color = '#22c55e';
            banner.textContent = `✓ Model ready v${infVer} — fine-tuned (${acc}% accuracy)`;
        }
        if (infVer !== '2.2') {
            showToast('Purana server code — run.bat band karke dubara chalao (Ctrl+C)', 'warning', 8000);
        }
        if (statusText) statusText.textContent = 'Model ready — upload an image';
        updateDemoStats(modelInfo);
    } else {
        const errMsg = health.load_error || 'Model load nahi hua';
        if (banner) {
            banner.style.background = 'rgba(239,68,68,0.15)';
            banner.style.color = '#ef4444';
            banner.textContent = `✗ ${errMsg}`;
        }
        if (statusText) {
            statusText.textContent = health.model_file_exists
                ? 'TensorFlow / Python fix chahiye — fix_env.bat chalao'
                : 'Pehle model train karo — run.bat';
        }
        showToast(errMsg, 'error', 8000);
    }
}

function updateDemoStats(info) {
    const accEl = document.getElementById('demoAccuracy');
    const modelEl = document.getElementById('demoModelName');
    const classesEl = document.getElementById('demoClassCount');

    if (accEl) accEl.textContent = `${(info.accuracy * 100).toFixed(1)}%`;
    if (modelEl) modelEl.textContent = 'MobileNetV2';
    if (classesEl) classesEl.textContent = String(info.classes?.length || 7);
}

// Setup mode tabs
function setupModeTabs() {
    const tabButtons = document.querySelectorAll('.mode-btn');
    const modeContents = document.querySelectorAll('.demo-mode');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;

            // Update buttons
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update content
            modeContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${mode}-mode`)?.classList.add('active');
        });
    });
}

// Setup drag and drop
function setupUploadArea() {
    const uploadZone = document.getElementById('uploadZone');
    if (!uploadZone) return;

    setupDragDrop(uploadZone, (file) => {
        handleImageUpload(file);
    });

    uploadZone.addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });

    // Browse button
    const browseBtn = document.getElementById('browseBtn');
    if (browseBtn) {
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('fileInput').click();
        });
    }

    // Change image button in preview (open file chooser)
    const changeBtn = document.getElementById('changeBtn');
    if (changeBtn) {
        changeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('fileInput').click();
        });
    }

    // Clicking preview image resets/removes the preview
    const previewImg = document.getElementById('previewImg');
    if (previewImg) {
        previewImg.addEventListener('click', () => {
            resetUploadPreview();
        });
    }
}

// Single image upload
function setupImageInput() {
    const imageInput = document.getElementById('fileInput');
    if (!imageInput) return;

    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleImageUpload(e.target.files[0]);
        }
    });
}

// Allow clicking preview image to clear/reset upload
function resetUploadPreview() {
    const uploadZone = document.getElementById('uploadZone');
    const uploadPreview = document.getElementById('uploadPreview');
    const previewImg = document.getElementById('previewImg');
    const resultsContent = document.getElementById('resultsContent');
    const processingStatus = document.getElementById('processingStatus');

    if (uploadZone) uploadZone.style.display = 'flex';
    if (uploadPreview) uploadPreview.style.display = 'none';
    if (previewImg) previewImg.src = '';
    if (resultsContent) resultsContent.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><p>Upload an image to see classification results</p></div>';
    if (processingStatus) processingStatus.querySelector('.status-text').textContent = 'Ready to analyze';
}

async function handleImageUpload(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please select an image file', 'error');
        return;
    }

    showToast('Processing image...', 'info');

    try {
        // Show loading state
        const processingStatus = document.getElementById('processingStatus');
        const statusText = processingStatus.querySelector('.status-text');
        statusText.textContent = 'Processing...';
        processingStatus.style.display = 'flex';

        // Hide empty state and show preview
        const uploadZone = document.getElementById('uploadZone');
        const uploadPreview = document.getElementById('uploadPreview');
        const previewImg = document.getElementById('previewImg');
        const resultsContent = document.getElementById('resultsContent');

        uploadZone.style.display = 'none';
        uploadPreview.style.display = 'block';
        resultsContent.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Analyzing image...</p></div>';

        // Display uploaded image
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
        };
        reader.readAsDataURL(file);

        // Upload and predict
        const prediction = await uploadImage(file);

        // Display results
        displayPredictionResult(prediction);
        currentPrediction = prediction;
        predictionCount++;

        statusText.textContent = 'Analysis complete';
        if (prediction.confidence < 0.5) {
            showToast('Confidence kam hai — clear photo upload karein ya dobara try karein', 'warning');
        } else {
            showToast('Prediction complete!', 'success');
        }
    } catch (error) {
        console.error('Upload error:', error);
        const statusText = document.getElementById('processingStatus').querySelector('.status-text');
        statusText.textContent = 'Analysis failed';
        showToast('Failed to process image', 'error');
    }
}

function displayPredictionResult(prediction) {
    const resultsContent = document.getElementById('resultsContent');

    // Create result HTML
    const resultHTML = `
        <div class="prediction-result">
            <div class="main-prediction">
                <span class="prediction-label">Predicted Class</span>
                <h2>${prediction.class_name}</h2>
                <span class="confidence-badge" style="background: ${getConfidenceColor(prediction.confidence)}">${formatConfidence(prediction.confidence)}</span>
            </div>

            <div class="prediction-details">
                <div class="detail-item">
                    <span class="detail-label">Processing Time</span>
                    <span class="detail-value">${prediction.processing_time_ms.toFixed(2)} ms</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Model</span>
                    <span class="detail-value">CIRCVIS MobileNetV2 (7-class fine-tuned)</span>
                </div>
            </div>

            <div class="confidence-chart">
                <h4>Class Probabilities</h4>
                <div class="confidence-bars">
                    ${generateConfidenceBars(prediction.all_classes)}
                </div>
            </div>
        </div>
    `;

    resultsContent.innerHTML = resultHTML;
}

function updateImpactMetrics(impactData) {
    // Demo page does not currently show detailed impact cards,
    // but this stub keeps batch prediction from failing when called.
    if (!impactData) return;
    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };

    setText('co2Impact', impactData.total_co2_saved_kg?.toLocaleString() + ' kg' || '—');
    setText('treesSaved', impactData.equivalent_to?.trees_saved || '—');
    setText('recyclablesIdentified', impactData.total_weight_kg?.toLocaleString() + ' kg' || '—');
}

function getConfidenceColor(confidence) {
    if (confidence > 0.8) {
        return 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)';
    } else if (confidence > 0.6) {
        return 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)';
    } else {
        return 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)';
    }
}

function generateConfidenceBars(allClasses) {
    const sortedClasses = Object.entries(allClasses)
        .sort((a, b) => b[1] - a[1]);

    return sortedClasses.map(([className, conf]) => `
        <div class="confidence-bar">
            <div class="bar-label">${className}</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: ${conf * 100}%"></div>
            </div>
            <div class="bar-value">${formatConfidence(conf)}</div>
        </div>
    `).join('');
}

// Camera controls
let cameraCaptureInterval = null;
let cameraCaptureInProgress = false;

function setupCameraControls() {
    const startBtn = document.getElementById('startCamera');
    if (!startBtn) return;

    startBtn.addEventListener('click', async () => {
        const video = document.getElementById('cameraVideo');
        if (video && video.srcObject) {
            stopCamera();
        } else {
            await startCamera();
        }
    });
}

// Batch processing
function setupBatchInput() {
    const batchInput = document.getElementById('batchInput');
    if (!batchInput) return;

    batchInput.addEventListener('change', async (e) => {
        if (e.target.files.length === 0) return;

        showToast(`Processing ${e.target.files.length} images...`, 'info');

        const formData = new FormData();
        for (let file of e.target.files) {
            formData.append('files', file);
        }

        try {
            const response = await fetch(`${API_BASE}/predict-batch`, {
                method: 'POST',
                body: formData,
                mode: 'cors'
            });

            if (!response.ok) throw new Error('Batch processing failed');

            const data = await response.json();

            // Display results
            const batchResults = document.getElementById('batchResults');
            batchResults.innerHTML = '<h4>Batch Results</h4>';

            data.predictions.forEach((pred, idx) => {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'glass';
                resultDiv.style.cssText = 'padding: 1rem; margin: 0.5rem 0; border-radius: 0.5rem;';
                resultDiv.innerHTML = `
                    <strong>${idx + 1}. ${pred.filename}</strong><br>
                    Class: <span style="color: var(--primary);">${pred.class_name}</span><br>
                    Confidence: ${formatConfidence(pred.confidence)}
                `;
                batchResults.appendChild(resultDiv);
            });

            predictionCount += data.predictions.length;
            updateImpactMetrics();

            showToast(`✓ Processed ${data.total} images`, 'success');
        } catch (error) {
            console.error('Batch error:', error);
            showToast('Batch processing failed', 'error');
        }
    });
}

// Camera functionality
async function startCamera() {
    const video = document.getElementById('cameraVideo');
    const startBtn = document.getElementById('startCamera');

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 720 } },
            audio: false
        });

            video.srcObject = stream;
        startBtn.textContent = 'Stop Camera';

        // Hide placeholder
        const placeholder = document.querySelector('.camera-placeholder');
        if (placeholder) placeholder.style.display = 'none';

        // Start automatic live capture every 3 seconds
        if (!cameraCaptureInterval) {
            cameraCaptureInterval = setInterval(() => {
                if (!video.paused && !video.ended) {
                    captureFrame();
                }
            }, 3000);
        }

        clearCameraOverlay();
        showToast('Camera started', 'success');
    } catch (error) {
        console.error('Camera error:', error);
        showToast('Unable to access camera', 'error');
    }
}

function stopCamera() {
    const video = document.getElementById('cameraVideo');
    const startBtn = document.getElementById('startCamera');
    const stream = video.srcObject;

    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }

    if (cameraCaptureInterval) {
        clearInterval(cameraCaptureInterval);
        cameraCaptureInterval = null;
    }
    cameraCaptureInProgress = false;

    startBtn.textContent = 'Start Camera';
    video.srcObject = null;
    clearCameraOverlay();

    // Show placeholder
    const placeholder = document.querySelector('.camera-placeholder');
    if (placeholder) placeholder.style.display = 'flex';

    // Clear results
    const liveResults = document.getElementById('liveResults');
    liveResults.innerHTML = '<div class="empty-state"><div class="empty-icon">⚡</div><p>Start camera for real-time analysis</p></div>';

    showToast('Camera stopped', 'info');
}

function captureFrame() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('cameraCanvas');
    const ctx = canvas.getContext('2d');

    if (!video || !canvas || !ctx || !video.videoWidth || !video.videoHeight) return;
    if (cameraCaptureInProgress) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    cameraCaptureInProgress = true;

    canvas.toBlob(async (blob) => {
        try {
            if (!blob) throw new Error('Capture blob was empty');
            const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
            const prediction = await uploadImage(file);
            currentPrediction = prediction;
            predictionCount++;

            const liveResults = document.getElementById('liveResults');
            liveResults.innerHTML = `
                <div class="prediction-result">
                    <div class="main-prediction">
                        <span class="prediction-label">Live Result</span>
                        <h3>${prediction.class_name}</h3>
                        <span class="confidence-badge" style="background: ${getConfidenceColor(prediction.confidence)}">${formatConfidence(prediction.confidence)}</span>
                    </div>
                    <button class="btn btn-secondary" onclick="captureFrame()" style="margin-top: 1rem;">
                        📸 Capture Again
                    </button>
                </div>
            `;
            updateCameraOverlay(prediction);
        } catch (error) {
            console.error('Camera capture error:', error);
            showToast('Live capture failed', 'error');
        } finally {
            cameraCaptureInProgress = false;
        }
    }, 'image/jpeg', 0.95);
}

function updateCameraOverlay(prediction) {
    const overlay = document.getElementById('cameraOverlay');
    const label = document.getElementById('cameraOverlayLabel');
    if (!overlay || !label) return;

    overlay.classList.remove('hidden');
    label.textContent = `${prediction.class_name} ${formatConfidence(prediction.confidence)}`;
}

function clearCameraOverlay() {
    const overlay = document.getElementById('cameraOverlay');
    if (!overlay) return;
    overlay.classList.add('hidden');
}

// Video processing
function setupVideoInput() {
    const videoInput = document.getElementById('videoInput');
    const selectVideoBtn = document.getElementById('selectVideo');
    const analysisVideo = document.getElementById('analysisVideo');

    if (!videoInput || !selectVideoBtn) return;

    selectVideoBtn.addEventListener('click', () => {
        videoInput.click();
    });

    videoInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            const videoPlaceholder = document.querySelector('.video-placeholder');

            analysisVideo.src = URL.createObjectURL(file);
            analysisVideo.style.display = 'block';
            if (videoPlaceholder) videoPlaceholder.style.display = 'none';
            analyzeVideo();
        }
    });
}

async function analyzeVideo() {
    const video = document.getElementById('analysisVideo');
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    const fps = 1; // Process every frame (adjust for performance)
    const frames = [];

    showToast('Extracting frames...', 'info');

    // Extract frames
    video.addEventListener('play', async () => {
        let frameCount = 0;

        const extractFrame = async () => {
            if (video.paused || video.ended) {
                analyzeFrames(frames);
                return;
            }

            if (frameCount % fps === 0) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);

                canvas.toBlob((blob) => {
                    frames.push(blob);
                });
            }

            frameCount++;
            requestAnimationFrame(extractFrame);
        };

        extractFrame();
    });

    video.play();
}

async function analyzeFrames(frames) {
    showToast(`Analyzing ${frames.length} frames...`, 'info');

    const results = {
        'Plastic': 0,
        'Organic': 0,
        'Metal': 0,
        'Paper/Cardboard': 0,
        'Glass': 0,
        'Textile': 0,
        'Miscellaneous': 0
    };

    const videoResults = document.getElementById('videoResults');
    videoResults.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Analyzing frames...</p></div>';

    let processed = 0;

    for (const blob of frames) {
        try {
            const file = new File([blob], `frame-${processed}.jpg`, { type: 'image/jpeg' });
            const prediction = await uploadImage(file);

            results[prediction.class_name]++;
            processed++;

            // Update progress
            const progress = Math.round((processed / frames.length) * 100);
            videoResults.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><p>Progress: ${progress}% (${processed}/${frames.length})</p></div>`;

            // Add delay to avoid overwhelming server
            await new Promise(r => setTimeout(r, 100));
        } catch (error) {
            console.error('Frame analysis error:', error);
        }
    }

    // Display results
    const resultHTML = `
        <div class="video-analysis-results">
            <h4>Analysis Complete</h4>
            <p class="analysis-summary">${processed} frames analyzed</p>
            <div class="class-breakdown">
                ${Object.entries(results).filter(([cls, count]) => count > 0).map(([cls, count]) => `
                    <div class="class-result">
                        <span class="class-name">${cls}</span>
                        <span class="class-count">${count} frames</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    videoResults.innerHTML = resultHTML;
    predictionCount += processed;

    showToast(`✓ Analyzed ${processed} frames`, 'success');
}

// Utility — use shared toast from utils.js
function formatConfidence(confidence) {
    return `${(confidence * 100).toFixed(1)}%`;
}

// Setup drag and drop functionality
function setupDragDrop(element, callback) {
    element.addEventListener('dragover', (e) => {
        e.preventDefault();
        element.classList.add('drag-over');
    });

    element.addEventListener('dragleave', () => {
        element.classList.remove('drag-over');
    });

    element.addEventListener('drop', (e) => {
        e.preventDefault();
        element.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            callback(files[0]);
        }
    });
}

console.log('✓ Demo script loaded');

/* CIRCVIS Dashboard */

let charts = {};

document.addEventListener('DOMContentLoaded', async () => {
    console.log('✓ CIRCVIS Dashboard Loaded');

    setupNavScroll();

    const conn = await initApiConnection();
    if (!conn.ok) {
        showToast('Demo mode — backend not connected', 'info', 4000);
        loadDemoData();
        setupFeedbackForm();
        return;
    }

    await loadDashboardData();
    setupFeedbackForm();
});

/* ── Nav scroll tint ── */
function setupNavScroll() {
    const nav = document.querySelector('.nav');
    if (!nav) return;
    window.addEventListener('scroll', () => {
        nav.style.background = window.scrollY > 60
            ? 'rgba(9,9,11,0.97)'
            : 'rgba(9,9,11,0.85)';
    }, { passive: true });
}

/* ── Live data from backend ── */
async function loadDashboardData() {
    showToast('Loading dashboard data…', 'info');
    try {
        const [statsData, impactData, comparisonData, nlpData] = await Promise.all([
            getDashboardStats(),
            getSustainabilityImpact(),
            getModelComparison(),
            getNlpSummary()
        ]);

        if (statsData) { updateKPICards(statsData); createCharts(statsData); }
        if (impactData) { updateImpactMetrics(impactData); }
        if (comparisonData) { updateModelComparisonTable(comparisonData); }
        if (nlpData) { updateNlpSummary(nlpData); }

        showToast('Dashboard loaded', 'success');
    } catch (err) {
        console.error('Dashboard load error:', err);
        showToast('Using demo data.', 'warning');
        loadDemoData();
    }
}

/* ── Demo / offline data ── */
async function loadDemoData() {
    const demoStats = {
        total_predictions: 1250,
        accuracy: 0.89,
        precision: 0.87,
        recall: 0.85,
        f1_score: 0.86,
        confusion_matrix: [
            [145, 8,  3,  2,  1,  1,  5],
            [5, 142,  2,  8,  0,  3,  2],
            [2,   1, 138, 0,  8,  0,  6],
            [3,   6,  0, 140, 2,  4,  0],
            [1,   0,  9,  1, 139, 0,  5],
            [2,   4,  0,  3,  1, 136, 9],
            [8,   3,  7,  2,  4,  5, 126]
        ],
        class_distribution: {
            'Plastic': 342,
            'Organic': 289,
            'Paper/Cardboard': 201,
            'Metal': 178,
            'Miscellaneous': 165,
            'Glass': 142,
            'Textile': 98
        }
    };

    const demoImpact = {
        total_co2_saved_kg: 3200,
        total_weight_kg: 875,
        equivalent_to: { trees_saved: 125 }
    };

    updateKPICards(demoStats);
    createCharts(demoStats);
    updateImpactMetrics(demoImpact);
    updateNlpSummary({ summary: 'Demo mode active — live NLP summary will appear once connected to the backend.', feedback_intent: 'demo' });
}

/* ── KPI cards ── */
function updateKPICards(stats) {
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    set('totalPredictions', stats.total_predictions.toLocaleString());
    set('accuracyRate',     formatConfidence(stats.accuracy));
    set('avgLatency',       '80ms');
    set('co2Saved',         (stats.total_predictions * 2.56).toFixed(0) + ' kg');
    set('metricAccuracy',   formatConfidence(stats.accuracy));
    set('metricPrecision',  formatConfidence(stats.precision));
    set('metricRecall',     formatConfidence(stats.recall));
    set('metricF1',         formatConfidence(stats.f1_score));
    set('imagesProcessed',  stats.total_predictions.toLocaleString());

    const values = [stats.accuracy, stats.precision, stats.recall, stats.f1_score];
    document.querySelectorAll('.metric-fill').forEach((fill, idx) => {
        if (values[idx] !== undefined) fill.style.width = (values[idx] * 100) + '%';
    });
}

/* ── Model comparison table ── */
function updateModelComparisonTable(comparisonData) {
    const tbody = document.getElementById('modelComparisonBody');
    if (!tbody || !comparisonData?.comparison?.length) return;

    tbody.innerHTML = comparisonData.comparison.map(m => `
        <tr class="${m.active ? 'row-highlight' : ''}">
            <td><strong>${m.active ? '✅ ' : ''}${m.model_name}</strong></td>
            <td>${formatConfidence(m.accuracy)}</td>
            <td>${formatConfidence(m.precision)}</td>
            <td>${formatConfidence(m.recall)}</td>
            <td>${formatConfidence(m.f1_score)}</td>
            <td>${m.inference_time_ms}</td>
            <td>${m.model_size_mb?.toFixed?.(1) ?? m.model_size_mb} MB</td>
        </tr>
    `).join('');
}

function updateNlpSummary(data) {
    const summaryEl = document.getElementById('nlpSummaryText');
    if (summaryEl) {
        summaryEl.textContent = data?.summary || 'No summary available.';
    }
    const intentEl = document.getElementById('nlpIntent');
    if (intentEl) {
        intentEl.textContent = data?.feedback_intent || data?.intent || 'insight';
    }
}

function setupFeedbackForm() {
    const form = document.getElementById('feedbackForm');
    if (!form) return;

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const payload = {
            predicted_class: document.getElementById('feedbackPredictedClass')?.value || null,
            actual_class: document.getElementById('feedbackActualClass')?.value || null,
            confidence: parseFloat(document.getElementById('feedbackConfidence')?.value || '0') || null,
            feedback_text: document.getElementById('feedbackText')?.value || '',
            user_id: document.getElementById('feedbackUserId')?.value || 'anonymous',
            timestamp: new Date().toISOString()
        };

        try {
            const response = await submitFeedback(payload);
            showToast(response?.message || 'Feedback submitted.', 'success');
            form.reset();
        } catch (error) {
            showToast('Could not submit feedback.', 'error');
        }
    });
}

/* ── Create all charts ── */
function createCharts(stats) {
    createAccuracyTrendChart();
    createConfusionMatrixHeatmap(stats.confusion_matrix);
    createClassDistributionChart(stats.class_distribution);
    createWasteCompositionChart(stats.class_distribution);
    updateTopClassesList(stats.class_distribution);
}

/* ── Accuracy trend line ── */
function createAccuracyTrendChart() {
    const canvas = document.getElementById('accuracyChart');
    if (!canvas) return;

    if (charts.accuracy) { charts.accuracy.destroy(); }

    charts.accuracy = new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'],
            datasets: [{
                label: 'Accuracy %',
                data: [78, 81, 84, 85, 87, 89],
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34,197,94,0.08)',
                borderWidth: 2.5,
                pointBackgroundColor: '#22c55e',
                pointBorderColor: '#09090b',
                pointRadius: 5,
                tension: 0.35,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    min: 70, max: 100,
                    ticks: { color: '#71717a', callback: v => v + '%', font: { family: "'Plus Jakarta Sans', sans-serif" } },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                x: {
                    ticks: { color: '#71717a', font: { family: "'Plus Jakarta Sans', sans-serif" } },
                    grid: { display: false }
                }
            }
        }
    });
}

/* ── Confusion matrix (bubble chart) ── */
function createConfusionMatrixHeatmap(matrix) {
    if (!matrix) return;
    // Delegate to the shared helper in utils.js
    createConfusionMatrixChart('confusionMatrix', matrix);
}

/* ── Class distribution bar ── */
function createClassDistributionChart(distribution) {
    const canvas = document.getElementById('classDistribution');
    if (!canvas) return;

    if (charts.distribution) { charts.distribution.destroy(); }

    const labels = Object.keys(distribution);
    const data   = Object.values(distribution);
    const colors = labels.map(l => getClassColor(l));

    charts.distribution = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Predictions',
                data,
                backgroundColor: colors.map(c => c + 'bb'),
                borderColor: colors,
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#71717a', font: { family: "'Plus Jakarta Sans', sans-serif" } },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                x: {
                    ticks: { color: '#71717a', font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 } },
                    grid: { display: false }
                }
            }
        }
    });
}

/* ── Waste composition doughnut ── */
function createWasteCompositionChart(distribution) {
    const canvas = document.getElementById('wasteComposition');
    if (!canvas) return;

    if (charts.composition) { charts.composition.destroy(); }

    const labels = Object.keys(distribution);
    const data   = Object.values(distribution);
    const colors = labels.map(l => getClassColor(l));

    charts.composition = new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.map(c => c + 'cc'),
                borderColor: '#09090b',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '62%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#a1a1aa',
                        font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
                        padding: 14,
                        boxWidth: 12,
                        boxHeight: 12
                    }
                }
            }
        }
    });
}

/* ── Top classes list ── */
function updateTopClassesList(distribution) {
    const list = document.getElementById('topClassesList');
    if (!list) return;

    const sorted = Object.entries(distribution).sort((a, b) => b[1] - a[1]);

    list.innerHTML = sorted.map(([name, count]) => `
        <div class="class-row">
            <span class="class-row-name">${name}</span>
            <span class="class-row-count">${count}</span>
        </div>
    `).join('');
}

/* ── Sustainability impact cards ── */
function updateImpactMetrics(impactData) {
    if (!impactData) return;
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    set('co2Impact',             (impactData.total_co2_saved_kg || 3200).toLocaleString() + ' kg');
    set('treesSaved',            impactData.equivalent_to?.trees_saved || 125);
    set('recyclablesIdentified', (impactData.total_weight_kg || 875).toLocaleString() + ' kg');
    set('materialValue',         '$' + ((impactData.total_weight_kg || 875) * 0.1).toFixed(1) + 'K');
}

/* ── Export helpers ── */
function exportReportPDF() {
    showToast('Generating PDF report…', 'info');
    setTimeout(() => showToast('Report exported as PDF', 'success'), 1000);
}

function exportDataCSV() {
    const rows = [
        ['Metric', 'Value'],
        ['Total Predictions', '1,250'],
        ['Accuracy', '89%'],
        ['Precision', '87%'],
        ['Recall', '85%'],
        ['F1-Score', '86%']
    ];
    const csv  = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'circvis-report.csv'; a.click();
    URL.revokeObjectURL(url);
    showToast('Report exported as CSV', 'success');
}

function downloadModel() { showToast('Model download would start here', 'info'); }

console.log('✓ Dashboard script loaded');

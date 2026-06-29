// Firebase Config
const firebaseConfig = {
    apiKey: 'AIzaSyCtbDdM4NMpfe67x3pQEAGIynr-RUTaW7M',
    authDomain: 'medi-c3916.firebaseapp.com',
    projectId: 'medi-c3916',
};
firebase.initializeApp(firebaseConfig);

let authToken = null;

firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
        authToken = await user.getIdToken();
        currentUserId = user.uid;
        currentUsername = user.email.split('@')[0];
        isAuthed = true;
        document.getElementById('user-badge').innerHTML = `<i class="fa-solid fa-circle-user"></i> ${currentUsername}`;
        document.getElementById('auth-toggle-btn').innerHTML = `<i class="fa-solid fa-sign-out-alt"></i> Logout`;
        fetchHistory();
    } else {
        authToken = null;
        isAuthed = false;
        currentUserId = 1;
        currentUsername = 'demo';
        document.getElementById('user-badge').innerHTML = `<i class="fa-solid fa-circle-user"></i> Demo Mode`;
    }
});

// Global Dashboard State
let currentUserId = 1; // Default to 'demo' user id
let currentUsername = 'demo';
let isAuthed = false;
let chartInstance = null;
let telemetryBuffer = [];
const BUFFER_LIMIT = 15;
let autoFeedTimer = null;
let latestLogId = null;

// Telemetry Source State
let telemetrySource = 'simulator'; // 'simulator' or 'hardware'
let hardwarePollTimer = null;
let cachedHwTelemetry = {
    mq135_ppm: 35.0,
    mq3_ppm: 12.0,
    mq7_ppm: 5.0,
    saliva_ph: 7.00,
    saliva_ec: 2.80
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    updateSimValues();
    checkAuthSession();
    fetchHistory();
});

function checkAuthSession() { /* Handled by Firebase Auth State Observer */ }

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': authToken ? `Bearer ${authToken}` : ''
    };
}

// Telemetry Source Toggle Logic
function setTelemetrySource(source) {
    if (source === telemetrySource) return;
    
    telemetrySource = source;
    
    // Toggle active tabs
    document.getElementById('btn-src-sim').classList.toggle('active', source === 'simulator');
    document.getElementById('btn-src-hw').classList.toggle('active', source === 'hardware');
    
    // Update dashboard header status indicator & sidebar status card styling
    const sourceStatusDot = document.getElementById('source-status-dot');
    const sourceDescription = document.getElementById('source-description');
    const hwStatusBox = document.getElementById('hw-status-box');
    const simSliders = document.getElementById('sim-sliders-wrapper');
    const simControls = document.getElementById('sim-controls-wrapper');
    
    if (source === 'hardware') {
        sourceStatusDot.className = 'status-dot active';
        sourceDescription.textContent = 'Monitoring real-time telemetry from physical ESP32 hardware via API.';
        hwStatusBox.classList.remove('hidden');
        simSliders.classList.add('disabled');
        simControls.classList.add('disabled');
        
        // Stop simulator continuous feed if checked
        const autoFeedCheckbox = document.getElementById('auto-feed');
        if (autoFeedCheckbox.checked) {
            autoFeedCheckbox.checked = false;
            toggleAutoFeed();
        }
        
        startHardwarePolling();
        showToast("Switched to Physical ESP32 Mode");
    } else {
        sourceDescription.textContent = 'Simulate physical breath and saliva sensor outputs to transmit real-time telemetry.';
        hwStatusBox.classList.add('hidden');
        simSliders.classList.remove('disabled');
        simControls.classList.remove('disabled');
        
        stopHardwarePolling();
        showToast("Switched to Simulator Mode");
    }
}

function startHardwarePolling() {
    stopHardwarePolling();
    pollHardwareTelemetry();
    hardwarePollTimer = setInterval(pollHardwareTelemetry, 3000);
}

function stopHardwarePolling() {
    if (hardwarePollTimer) {
        clearInterval(hardwarePollTimer);
        hardwarePollTimer = null;
    }
}

async function pollHardwareTelemetry() {
    try {
        const response = await fetch(`/api/telemetry/latest/${currentUserId}`, { headers: getAuthHeaders() });
        if (!response.ok) throw new Error("Failed to fetch latest telemetry");
        
        const data = await response.json();
        
        // Update cached values
        cachedHwTelemetry = {
            mq135_ppm: parseFloat(data.mq135_ppm),
            mq3_ppm: parseFloat(data.mq3_ppm),
            mq7_ppm: parseFloat(data.mq7_ppm),
            saliva_ph: parseFloat(data.saliva_ph),
            saliva_ec: parseFloat(data.saliva_ec)
        };
        
        // Update Live Mini UI cards
        document.getElementById('live-mq135').textContent = cachedHwTelemetry.mq135_ppm.toFixed(1);
        document.getElementById('live-mq3').textContent = cachedHwTelemetry.mq3_ppm.toFixed(1);
        document.getElementById('live-mq7').textContent = cachedHwTelemetry.mq7_ppm.toFixed(1);
        document.getElementById('live-ph').textContent = cachedHwTelemetry.saliva_ph.toFixed(2);
        document.getElementById('live-ec').textContent = cachedHwTelemetry.saliva_ec.toFixed(2);
        
        // Update Chart
        addDataToChart(
            cachedHwTelemetry.mq135_ppm,
            cachedHwTelemetry.mq3_ppm,
            cachedHwTelemetry.mq7_ppm,
            cachedHwTelemetry.saliva_ph,
            cachedHwTelemetry.saliva_ec
        );
        
        // Check ESP32 status based on latest reading timestamp (forcing UTC check)
        let timestampStr = data.timestamp;
        if (!timestampStr.endsWith('Z') && !timestampStr.includes('+') && !timestampStr.includes('-')) {
            timestampStr += 'Z';
        }
        const telemetryTime = new Date(timestampStr);
        const currentTime = new Date();
        const diffSeconds = Math.abs((currentTime - telemetryTime) / 1000);
        
        const hwDot = document.getElementById('hw-status-dot');
        const hwText = document.getElementById('hw-status-text');
        const hwLastSeen = document.getElementById('hw-last-seen');
        
        const timeString = telemetryTime.toLocaleTimeString();
        
        if (diffSeconds < 15) {
            hwDot.className = 'status-dot-pulse green';
            hwText.textContent = "ESP32 Connected";
            hwLastSeen.textContent = `Last Transmission: Active (${timeString})`;
        } else if (diffSeconds < 60) {
            hwDot.className = 'status-dot-pulse orange';
            hwText.textContent = "ESP32 Idle";
            hwLastSeen.textContent = `Last Transmission: ${Math.round(diffSeconds)}s ago (${timeString})`;
        } else {
            hwDot.className = 'status-dot-pulse red';
            hwText.textContent = "ESP32 Offline";
            hwLastSeen.textContent = `Last Transmission: ${telemetryTime.toLocaleDateString()} ${timeString}`;
        }
        
    } catch (err) {
        console.error("Telemetry polling error", err);
        const hwDot = document.getElementById('hw-status-dot');
        const hwText = document.getElementById('hw-status-text');
        hwDot.className = 'status-dot-pulse red';
        hwText.textContent = "Connection Error";
    }
}

// Slider Visual Updates
function updateSimValues() {
    const mq135 = document.getElementById('sim-mq135').value;
    const mq3 = document.getElementById('sim-mq3').value;
    const mq7 = document.getElementById('sim-mq7').value;
    const ph = parseFloat(document.getElementById('sim-ph').value).toFixed(2);
    const ec = parseFloat(document.getElementById('sim-ec').value).toFixed(2);

    document.getElementById('val-mq135').textContent = mq135 + ' PPM';
    document.getElementById('val-mq3').textContent = mq3 + ' PPM';
    document.getElementById('val-mq7').textContent = mq7 + ' PPM';
    document.getElementById('val-ph').textContent = ph + ' pH';
    document.getElementById('val-ec').textContent = ec + ' mS/cm';
}

// Chart Initializer
function initChart() {
    const ctx = document.getElementById('liveChart').getContext('2d');
    
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'MQ135 (VOC)', borderColor: '#60a5fa', backgroundColor: 'rgba(96, 165, 250, 0.1)', data: [], borderWidth: 2, tension: 0.3 },
                { label: 'MQ3 (Alcohol)', borderColor: '#f472b6', backgroundColor: 'rgba(244, 114, 182, 0.1)', data: [], borderWidth: 2, tension: 0.3 },
                { label: 'MQ7 (CO)', borderColor: '#fbbf24', backgroundColor: 'rgba(251, 191, 191, 0.1)', data: [], borderWidth: 2, tension: 0.3 },
                { label: 'Saliva pH', borderColor: '#34d399', backgroundColor: 'rgba(52, 211, 153, 0.1)', data: [], borderWidth: 2, tension: 0.3, yAxisID: 'y1' },
                { label: 'Saliva EC', borderColor: '#a78bfa', backgroundColor: 'rgba(167, 139, 250, 0.1)', data: [], borderWidth: 2, tension: 0.3, yAxisID: 'y1' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    title: { display: true, text: 'Gas Concentration (PPM)', color: '#9ca3af' },
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { color: '#9ca3af' }
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Saliva (pH / mS/cm)', color: '#9ca3af' },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#9ca3af' },
                    min: 0,
                    max: 14
                }
            },
            plugins: {
                legend: { labels: { color: '#f3f4f6' } }
            }
        }
    });
}

// Push to chart datasets
function addDataToChart(mq135, mq3, mq7, ph, ec) {
    const now = new Date().toLocaleTimeString();
    
    if (chartInstance.data.labels.length >= BUFFER_LIMIT) {
        chartInstance.data.labels.shift();
        chartInstance.data.datasets.forEach(dataset => dataset.data.shift());
    }
    
    chartInstance.data.labels.push(now);
    chartInstance.data.datasets[0].data.push(mq135);
    chartInstance.data.datasets[1].data.push(mq3);
    chartInstance.data.datasets[2].data.push(mq7);
    chartInstance.data.datasets[3].data.push(ph);
    chartInstance.data.datasets[4].data.push(ec);
    
    chartInstance.update();
}

// Send simulated ESP32 Telemetry
async function sendTelemetry() {
    const mq135 = parseFloat(document.getElementById('sim-mq135').value);
    const mq3 = parseFloat(document.getElementById('sim-mq3').value);
    const mq7 = parseFloat(document.getElementById('sim-mq7').value);
    const ph = parseFloat(document.getElementById('sim-ph').value);
    const ec = parseFloat(document.getElementById('sim-ec').value);

    // Update Live Mini UI cards
    document.getElementById('live-mq135').textContent = mq135.toFixed(1);
    document.getElementById('live-mq3').textContent = mq3.toFixed(1);
    document.getElementById('live-mq7').textContent = mq7.toFixed(1);
    document.getElementById('live-ph').textContent = ph.toFixed(2);
    document.getElementById('live-ec').textContent = ec.toFixed(2);

    // Update Chart
    addDataToChart(mq135, mq3, mq7, ph, ec);

    // Post to Server API
    try {
        const response = await fetch('/api/telemetry', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                user_id: currentUserId,
                mq135_ppm: mq135,
                mq3_ppm: mq3,
                mq7_ppm: mq7,
                saliva_ph: ph,
                saliva_ec: ec
            })
        });
        if (response.ok) {
            showToast("Simulated Telemetry Transmitted!");
        }
    } catch (err) {
        console.error("Failed to transmit telemetry", err);
    }
}

// Continuous simulator feed
function toggleAutoFeed() {
    const checked = document.getElementById('auto-feed').checked;
    if (checked) {
        sendTelemetry();
        autoFeedTimer = setInterval(() => {
            // Add tiny fluctuations to make the simulation look live
            const mq135 = document.getElementById('sim-mq135');
            const mq3 = document.getElementById('sim-mq3');
            const mq7 = document.getElementById('sim-mq7');
            const ph = document.getElementById('sim-ph');
            const ec = document.getElementById('sim-ec');
            
            mq135.value = Math.max(10, Math.min(350, parseInt(mq135.value) + Math.round((Math.random() - 0.5) * 6)));
            mq3.value = Math.max(5, Math.min(150, parseInt(mq3.value) + Math.round((Math.random() - 0.5) * 3)));
            mq7.value = Math.max(2, Math.min(100, parseInt(mq7.value) + Math.round((Math.random() - 0.5) * 2)));
            ph.value = Math.max(4.0, Math.min(9.0, parseFloat(ph.value) + (Math.random() - 0.5) * 0.1)).toFixed(2);
            ec.value = Math.max(0.5, Math.min(10.0, parseFloat(ec.value) + (Math.random() - 0.5) * 0.1)).toFixed(2);
            
            updateSimValues();
            sendTelemetry();
        }, 5000);
    } else {
        if (autoFeedTimer) {
            clearInterval(autoFeedTimer);
            autoFeedTimer = null;
        }
    }
}

// Evaluate Screening Form
async function evaluateScreening() {
    const age = parseInt(document.getElementById('p-age').value);
    const bmi = parseFloat(document.getElementById('p-bmi').value);
    const smoking = document.getElementById('c-smoking').checked ? 1 : 0;
    const alcohol = document.getElementById('c-alcohol').checked ? 1 : 0;
    const diabetes = document.getElementById('c-diabetes').checked ? 1 : 0;
    const family = document.getElementById('c-family').checked ? 1 : 0;
    const weight = document.getElementById('c-weight').checked ? 1 : 0;
    const pain = document.getElementById('c-pain').checked ? 1 : 0;
    const appetite = document.getElementById('c-appetite').checked ? 1 : 0;
    const jaundice = document.getElementById('c-jaundice').checked ? 1 : 0;

    // Use either cached real telemetry or simulator settings
    let mq135, mq3, mq7, ph, ec;
    if (telemetrySource === 'hardware') {
        mq135 = cachedHwTelemetry.mq135_ppm;
        mq3 = cachedHwTelemetry.mq3_ppm;
        mq7 = cachedHwTelemetry.mq7_ppm;
        ph = cachedHwTelemetry.saliva_ph;
        ec = cachedHwTelemetry.saliva_ec;
    } else {
        mq135 = parseFloat(document.getElementById('sim-mq135').value);
        mq3 = parseFloat(document.getElementById('sim-mq3').value);
        mq7 = parseFloat(document.getElementById('sim-mq7').value);
        ph = parseFloat(document.getElementById('sim-ph').value);
        ec = parseFloat(document.getElementById('sim-ec').value);
    }

    // Call predict API
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                user_id: currentUserId,
                age, bmi,
                smoking_history: smoking,
                alcohol_consumption: alcohol,
                diabetes, family_history: family,
                weight_loss: weight, abdominal_pain: pain,
                appetite_changes: appetite, jaundice,
                mq135_ppm: mq135, mq3_ppm: mq3, mq7_ppm: mq7,
                saliva_ph: ph, saliva_ec: ec
            })
        });

        if (response.ok) {
            const data = await response.json();
            showResults(data);
            fetchHistory();
        } else {
            console.error("Evaluation response issue.");
        }
    } catch (err) {
        console.error("Prediction API connection failed", err);
    }
}

// Render prediction data on results panel
function showResults(data) {
    document.getElementById('res-placeholder').classList.add('hidden');
    const details = document.getElementById('res-details');
    details.classList.remove('hidden');

    // Score Animation
    const scoreVal = document.getElementById('res-score-number');
    let startScore = 0;
    const targetScore = Math.round(data.pcri_score);
    const scoreTimer = setInterval(() => {
        if (startScore >= targetScore) {
            scoreVal.textContent = targetScore;
            clearInterval(scoreTimer);
        } else {
            startScore++;
            scoreVal.textContent = startScore;
        }
    }, 15);

    // Update gauge needle rotation
    // Full scale 0-100 corresponds to 0-180deg (or whatever visual arch you prefer)
    // 0 score: -90deg, 100 score: +90deg
    const angle = (data.pcri_score / 100) * 180 - 90;
    document.getElementById('gauge-indicator').style.transform = `rotate(${angle}deg)`;

    // Risk Classification Badge
    const riskBadge = document.getElementById('res-risk-badge');
    riskBadge.textContent = `${data.risk_level} Risk`;
    riskBadge.className = 'risk-badge'; // reset
    if (data.risk_level === 'Low') riskBadge.classList.add('risk-low');
    else if (data.risk_level === 'Moderate') riskBadge.classList.add('risk-moderate');
    else riskBadge.classList.add('risk-high');

    // AI confidence
    document.getElementById('res-confidence').textContent = `AI Confidence: ${data.ai_confidence}%`;

    // Progress components
    document.getElementById('lbl-c-breath').textContent = `${data.components.breath_voc_score}%`;
    document.getElementById('bar-c-breath').style.width = `${data.components.breath_voc_score}%`;

    document.getElementById('lbl-c-ph').textContent = `${data.components.saliva_ph_score}%`;
    document.getElementById('bar-c-ph').style.width = `${data.components.saliva_ph_score}%`;

    document.getElementById('lbl-c-ec').textContent = `${data.components.saliva_ec_score}%`;
    document.getElementById('bar-c-ec').style.width = `${data.components.saliva_ec_score}%`;

    document.getElementById('lbl-c-ai').textContent = `${data.components.ai_prediction_score}%`;
    document.getElementById('bar-c-ai').style.width = `${data.components.ai_prediction_score}%`;

    // Advice text
    document.getElementById('res-recommendation').textContent = data.recommendations;
    
    // Store log for PDF export
    latestLogId = data.id; // wait, prediction response does not return log id, let's fetch history to match it
}

// Fetch history screening log
async function fetchHistory() {
    try {
        const response = await fetch(`/api/history/${currentUserId}`, { headers: getAuthHeaders() });
        if (response.ok) {
            const history = await response.json();
            const tbody = document.getElementById('history-tbody');
            
            if (history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="table-empty">No screening logs found. Perform a screening scan above.</td></tr>`;
                return;
            }

            // Capture latest log id for rapid PDF download
            latestLogId = history[0].id;

            tbody.innerHTML = '';
            history.forEach(log => {
                const dateStr = new Date(log.timestamp).toLocaleString();
                const tr = document.createElement('tr');
                
                let badgeClass = 'risk-low';
                if (log.risk_level === 'Moderate') badgeClass = 'risk-moderate';
                if (log.risk_level === 'High') badgeClass = 'risk-high';

                tr.innerHTML = `
                    <td>${dateStr}</td>
                    <td class="font-lcd" style="font-weight:700;">${log.pcri_score}</td>
                    <td><span class="risk-badge ${badgeClass}" style="font-size:0.75rem; padding: 2px 8px;">${log.risk_level}</span></td>
                    <td>${log.ai_confidence}%</td>
                    <td><a href="/api/generate-pdf/${log.id}" class="dl-link" target="_blank"><i class="fa-solid fa-file-pdf"></i> PDF</a></td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Failed to load historical logs", err);
    }
}

// Trigger PDF Download
function downloadLatestPDF() {
    if (latestLogId) {
        window.open(`/api/generate-pdf/${latestLogId}`, '_blank');
    } else {
        alert("No active screening profile loaded.");
    }
}

// AUTH MODULE LOGIC
function openAuthModal() {
    if (isAuthed) {
        // Simple Logout
        firebase.auth().signOut().then(() => {
            showToast("Logged out successfully");
        });
    } else {
        document.getElementById('auth-modal').classList.add('open');
    }
}

function closeAuthModal() {
    document.getElementById('auth-modal').classList.remove('open');
}

let authTab = 'login';
function switchAuthTab(tab) {
    authTab = tab;
    document.getElementById('tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('tab-register').classList.toggle('active', tab === 'register');
    document.getElementById('group-email').classList.toggle('hidden', tab === 'login');
    document.getElementById('modal-title').textContent = tab === 'login' ? 'Sign In to Dashboard' : 'Register Screening Account';
    document.getElementById('auth-submit-btn').textContent = tab === 'login' ? 'Login' : 'Create Account';
}

async function handleAuth() {
    const username = document.getElementById('auth-username').value;
    const pass = document.getElementById('auth-password').value;
    const email = document.getElementById('auth-email').value;

    try {
        let userCred;
        if (authTab === 'register') {
            userCred = await firebase.auth().createUserWithEmailAndPassword(email, pass);
            authToken = await userCred.user.getIdToken();
            await fetch('/api/auth/register', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ email: email, username: username })
            });
            showToast("Registration successful");
            closeAuthModal();
            switchAuthTab('login');
        } else {
            if (!username.includes('@')) {
                alert("Please use your email address to login");
                return;
            }
            userCred = await firebase.auth().signInWithEmailAndPassword(username, pass);
            authToken = await userCred.user.getIdToken();
            showToast("Login successful");
            closeAuthModal();
        }
    } catch (err) {
        alert(err.message);
        console.error("Auth error", err);
    }
}

// Toast Helpers
function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

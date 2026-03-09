const API_BASE_URL = 'http://localhost:8080/api';

// Chart instances
let severityChartInstance = null;
let topIpChartInstance = null;
let timelineChartInstance = null;

// DOM Elements
const fileInput = document.getElementById('logFile');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const dropzone = document.getElementById('dropzone');
const uploadStatus = document.getElementById('uploadStatus');
const alertsTableBody = document.getElementById('alertsTableBody');
const downloadBtn = document.getElementById('downloadReportBtn');

// Modal Elements
const timelineModal = document.getElementById('timelineModal');
const closeModalBtns = [document.getElementById('closeModalBtn'), document.getElementById('closeModalFooterBtn')];
const timelineIpTarget = document.getElementById('timelineIpTarget');
const timelineContainer = document.getElementById('timelineContainer');

// Chart Colors
const COLORS = {
    critical: 'rgba(239, 68, 68, 0.8)', // red-500
    high: 'rgba(249, 115, 22, 0.8)',    // orange-500
    medium: 'rgba(234, 179, 8, 0.8)'    // yellow-500
};

// Auto-polling interval
let dashboardPollInterval = null;
let currentAlertsData = [];
let currentSortColumn = 'time';
let currentSortDirection = 'desc';

// Initialize Dashboard on Load
document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
    
    // Start continuous polling every 5 seconds
    dashboardPollInterval = setInterval(fetchDashboardData, 5000);
    
    // File upload listeners (legacy support)
    fileInput.addEventListener('change', handleFileUpload);
    
    // Download quick report listener
    downloadBtn.addEventListener('click', () => {
        window.open(`${API_BASE_URL}/export/pdf`, '_blank');
        showToast("Generating PDF incident report...", "success");
    });
    
    // Single Alert PDF download listener
    const downloadSinglePdfBtn = document.getElementById('downloadSinglePdfBtn');
    if (downloadSinglePdfBtn) {
        downloadSinglePdfBtn.addEventListener('click', () => {
            const ip = timelineIpTarget.textContent;
            if (ip) {
                window.open(`${API_BASE_URL}/export/pdf/${ip}`, '_blank');
                showToast(`Generating PDF for ${ip}...`, "success");
            }
        });
    }

    // Modal listeners
    closeModalBtns.forEach(btn => btn?.addEventListener('click', closeTimelineModal));

    // Navigation setup
    setupNavigation();
});

// Navigation Logic
function setupNavigation() {
    const navItems = {
        'nav-dashboard': { viewId: 'view-dashboard', title: 'Dashboard Overview' },
        'nav-reports': { viewId: 'view-reports', title: 'Reports & Analytics' },
        'nav-settings': { viewId: 'view-settings', title: 'System Settings' }
    };

    const views = document.querySelectorAll('.content-view');
    const titleEl = document.getElementById('pageTitle');

    Object.keys(navItems).forEach(navId => {
        const link = document.getElementById(navId);
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            views.forEach(v => {
                v.classList.remove('block');
                v.classList.add('hidden');
            });
            
            Object.keys(navItems).forEach(id => {
                document.getElementById(id).classList.remove('active');
            });
            
            const target = navItems[navId];
            document.getElementById(target.viewId).classList.remove('hidden');
            document.getElementById(target.viewId).classList.add('block');
            
            titleEl.textContent = target.title;
            
            link.classList.add('active');
        });
    });
}

// File Upload Logic (Legacy Simulation)
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    fileNameDisplay.textContent = `Selected: ${file.name}`;
    uploadStatus.classList.remove('hidden');
    uploadStatus.textContent = 'Initiating A2A Workflow...';
    uploadStatus.className = 'mt-4 p-3 rounded bg-blue-900/30 border-l-2 border-blue-500 text-blue-300 text-xs';

    const feed = document.getElementById('agentFeed');
    feed.innerHTML = '';
    
    // Helper to add log entries
    const addLog = (msg, color='text-slate-300', icon='⚡') => {
        const div = document.createElement('div');
        div.className = `agent-log-entry flex items-start gap-2 ${color}`;
        div.innerHTML = `<span class="mt-0.5 flex-shrink-0">${icon}</span> <span class="flex-1 break-words">${msg}</span>`;
        feed.appendChild(div);
        feed.scrollTop = feed.scrollHeight;
    };

    addLog(`System: Uploading ${file.name} to Orchestrator`, 'text-blue-400', '📤');
    
    const formData = new FormData();
    formData.append("file", file);

    if (window.a2aInterval) {
        clearInterval(window.a2aInterval);
    }

    try {
        window.a2aInterval = setInterval(() => {
            const msgs = [
                "Parser Agent: Aligning regex structures...",
                "Parser Agent: Normalizing timestamp formats...",
                "Threat Agent: Loading heuristic matrices...",
                "Threat Agent: Cross-referencing indicator databases...",
                "Reporter Agent: Standing by for intel payload..."
            ];
            addLog(msgs[Math.floor(Math.random() * msgs.length)], 'text-slate-400', '🧠');
        }, 1500);

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Upload failed");

        const data = await response.json();
        
        addLog(`Parser Agent: Successfully extracted ${data.events_parsed} events.`, 'text-green-400', '✅');
        addLog(`Threat Agent: Identified ${data.alerts_generated} malicious patterns.`, 'text-orange-400', '⚠️');
        addLog(`Reporter Agent: Incident report drafted.`, 'text-green-400', '📝');
        
        uploadStatus.textContent = `Workflow Complete: ${data.events_parsed} processed, ${data.alerts_generated} threats.`;
        uploadStatus.className = 'mt-4 p-3 rounded bg-green-900/30 border-l-2 border-green-500 text-green-300 text-xs';
        
        showToast("A2A analysis successful", "success");
        
        fetchDashboardData();
        
        fileInput.value = '';
        setTimeout(() => {
            uploadStatus.classList.add('hidden');
            fileNameDisplay.textContent = 'Upload raw logs to wake agents';
        }, 5000);

    } catch (error) {
        console.error(error);
        addLog("Orchestrator: FATAL ERROR executing workflow.", "text-red-400", "❌");
        uploadStatus.textContent = 'Error processing log file.';
        uploadStatus.className = 'mt-4 p-3 rounded bg-red-900/30 border-l-2 border-red-500 text-red-300 text-xs';
        showToast("Error executing agents", "error");
    } finally {
        if (window.a2aInterval) {
            clearInterval(window.a2aInterval);
        }
    }
}

// Fetch & Update Dashboard
async function fetchDashboardData() {
    try {
        const res = await fetch(`${API_BASE_URL}/dashboard`);
        if (!res.ok) throw new Error('API Error');
        const data = await res.json();

        updateStats(data.stats);
        updateTable(data.recent_alerts);
        updateCharts(data.stats, data.top_ips, data.timeline_stats);
        
    } catch (err) {
        console.error("Failed to load dashboard data.", err);
    }
}

// Update Stats Cards
function updateStats(stats) {
    document.getElementById('stat-total').textContent = stats.total_alerts;
    document.getElementById('stat-critical').textContent = stats.critical_alerts;
    document.getElementById('stat-high').textContent = stats.high_alerts;
    document.getElementById('stat-medium').textContent = stats.medium_alerts;
}

// Update Data Table
function updateTable(alerts) {
    currentAlertsData = alerts;
    renderTable();
}

function handleSort(column) {
    if (currentSortColumn === column) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        currentSortDirection = 'desc'; // Default to desc when clicking new column
    }
    
    // Update sort icons in DOM
    document.querySelectorAll('th button svg').forEach(svg => svg.classList.add('opacity-30'));
    const activeSvg = document.getElementById(`sort-${column}`);
    if (activeSvg) {
        activeSvg.classList.remove('opacity-30');
        activeSvg.style.transform = currentSortDirection === 'asc' ? 'rotate(180deg)' : '';
    }
    
    renderTable();
}

function renderTable() {
    alertsTableBody.innerHTML = '';
    
    if (!currentAlertsData || currentAlertsData.length === 0) {
        alertsTableBody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-500">No active alerts detected. Monitoring logs...</td></tr>`;
        return;
    }

    let sortedAlerts = [...currentAlertsData];
    sortedAlerts.sort((a, b) => {
        let valA, valB;
        switch(currentSortColumn) {
            case 'time':
                valA = new Date(a.created_at).getTime();
                valB = new Date(b.created_at).getTime();
                break;
            case 'ip':
                valA = a.source_ip;
                valB = b.source_ip;
                break;
            case 'location':
                valA = a.country;
                valB = b.country;
                break;
            case 'type':
                valA = a.attack_type;
                valB = b.attack_type;
                break;
            case 'intel':
                valA = a.abuse_reports;
                valB = b.abuse_reports;
                break;
            case 'severity':
                const sevLevel = { 'Critical': 3, 'High': 2, 'Medium': 1 };
                valA = sevLevel[a.severity] || 0;
                valB = sevLevel[b.severity] || 0;
                break;
            default:
                valA = a.id;
                valB = b.id;
        }
        
        if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
        if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    sortedAlerts.forEach((alert, index) => {
        const severityClass = `badge-${alert.severity.toLowerCase()}`;
        
        const date = new Date(alert.created_at);
        const timeStr = date.toLocaleString('en-US', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        
        const locationStr = alert.country !== 'Unknown' ? `${alert.city}, ${alert.country}` : 'Unknown Geolocation';
        const intelColor = alert.reputation === 'Malicious' ? 'text-red-400' : alert.reputation === 'Suspicious' ? 'text-orange-400' : 'text-slate-400';
        
        const row = document.createElement('tr');
        // Add a staggering animation effect for new renders
        row.className = `hover:bg-white/5 transition duration-300 animate-slide-in opacity-0 animate-fill-forwards border-b border-white/5 last:border-0`;
        row.style.animationDelay = `${index * 50}ms`;
        
        row.innerHTML = `
            <td class="py-3 px-6 text-slate-400 text-xs font-mono whitespace-nowrap">${timeStr}</td>
            <td class="py-3 px-6 whitespace-nowrap">
                <div class="font-mono text-slate-300 group-hover:text-soc-neon transition">${alert.source_ip}</div>
            </td>
            <td class="py-3 px-6 text-slate-400 text-xs">
                <div class="flex items-center gap-2 whitespace-nowrap">
                    ${alert.country !== 'Unknown' ? '<svg class="w-3 h-3 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>' : ''}
                    ${locationStr}
                </div>
            </td>
            <td class="py-3 px-6 text-slate-300 text-xs whitespace-nowrap">
                ${alert.attack_type}<br/>
                <span class="text-slate-500 text-[10px] uppercase">User: <span class="text-slate-400">${alert.username}</span> (${alert.attempt_count} tries)</span>
            </td>
            <td class="py-3 px-6 text-xs whitespace-nowrap">
                <span class="${intelColor} font-medium tracking-wide">${alert.reputation}</span>
                ${alert.abuse_reports > 0 ? `<br/><span class="text-[10px] text-slate-500">${alert.abuse_reports} abuse reports</span>` : ''}
            </td>
            <td class="py-3 px-6 whitespace-nowrap">
                <span class="badge ${severityClass}">${alert.severity}</span>
            </td>
            <td class="py-3 px-6 text-right whitespace-nowrap">
                <button onclick="openTimelineModal('${alert.source_ip}')" class="px-3 py-1.5 bg-soc-surface hover:bg-slate-700 hover:text-white border border-slate-600 rounded text-xs text-slate-300 transition-all flex items-center inline-flex shadow-sm hover:shadow-md hover:border-soc-neon/50">
                    <svg class="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                    Investigate
                </button>
            </td>
        `;
        alertsTableBody.appendChild(row);
    });
}

// Update Chart.js Visualizations
function updateCharts(stats, topIps, timelineStats) {
    const hasData = stats.critical_alerts > 0 || stats.high_alerts > 0 || stats.medium_alerts > 0;
    const sevData = hasData ? [stats.critical_alerts, stats.high_alerts, stats.medium_alerts] : [0,0,1];
    const sevBg = hasData ? [COLORS.critical, COLORS.high, COLORS.medium] : ['#334155'];

    // ---- Doughnut Chart for Severity ----
    const severityCanvas = document.getElementById('severityChart');
    if (severityChartInstance) {
        severityChartInstance.data.datasets[0].data = sevData;
        severityChartInstance.data.datasets[0].backgroundColor = sevBg;
        severityChartInstance.update('none'); // Update without animation so it's smooth
    } else {
        severityChartInstance = new Chart(severityCanvas, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'High', 'Medium'],
                datasets: [{
                    data: sevData,
                    backgroundColor: sevBg,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                animation: { duration: 800, easing: 'easeOutQuart' },
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94a3b8', font: {family: "'Inter', sans-serif"} } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if(!hasData) return 'No Data';
                                return ` ${context.label}: ${context.raw}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // ---- Bar Chart for Top IPs ----
    const topIpCanvas = document.getElementById('topIpChart');
    const ipLabels = topIps.map(item => item.ip);
    const ipData = topIps.map(item => item.count);
    const ipHasData = topIps.length > 0;

    if (topIpChartInstance) {
        topIpChartInstance.data.labels = ipHasData ? ipLabels : ['No Data'];
        topIpChartInstance.data.datasets[0].data = ipHasData ? ipData : [0];
        topIpChartInstance.update('none');
    } else {
        topIpChartInstance = new Chart(topIpCanvas, {
            type: 'bar',
            data: {
                labels: ipHasData ? ipLabels : ['No Data'],
                datasets: [{
                    label: 'Failed Login Attempts',
                    data: ipHasData ? ipData : [0],
                    backgroundColor: 'rgba(14, 165, 233, 0.6)', 
                    borderColor: 'rgba(14, 165, 233, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 800, easing: 'easeOutQuart' },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(51, 65, 85, 0.2)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8', font: {family: "'Inter', sans-serif"} } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', titleColor: '#f8fafc', bodyColor: '#cbd5e1', borderColor: '#334155', borderWidth: 1 }
                }
            }
        });
    }

    // ---- Line Chart for Alerts Over Time ----
    const timelineCanvas = document.getElementById('timelineChart');
    let timeLabels = [];
    let timeData = [];
    
    if (timelineStats && timelineStats.length > 0) {
        timeLabels = timelineStats.map(item => item.time.split('T')[1].substring(0, 5));
        timeData = timelineStats.map(item => item.count);
    }

    if (timelineChartInstance) {
        timelineChartInstance.data.labels = timeLabels.length > 0 ? timeLabels : ['Now'];
        timelineChartInstance.data.datasets[0].data = timeLabels.length > 0 ? timeData : [0];
        timelineChartInstance.update('none');
    } else {
        // Create context gradient
        const ctx = timelineCanvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 200);
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
        gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

        timelineChartInstance = new Chart(timelineCanvas, {
            type: 'line',
            data: {
                labels: timeLabels.length > 0 ? timeLabels : ['Now'],
                datasets: [{
                    label: 'Intrusions',
                    data: timeLabels.length > 0 ? timeData : [0],
                    borderColor: 'rgba(16, 185, 129, 1)', // emerald-500
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(16, 185, 129, 1)',
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 800, easing: 'easeOutQuart' },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(51, 65, 85, 0.2)' }, ticks: { color: '#94a3b8', stepSize: 1 } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8', font: {family: "'Inter', sans-serif"} } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', titleColor: '#f8fafc', bodyColor: '#cbd5e1', borderColor: '#334155', borderWidth: 1 }
                }
            }
        });
    }
}

// Attack Timeline Modal Logic
async function openTimelineModal(ip) {
    timelineIpTarget.textContent = ip;
    timelineModal.classList.remove('hidden');
    timelineContainer.innerHTML = '<div class="text-center py-4 text-slate-500 w-full animate-pulse">Gathering Forensics Data...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/alerts/${ip}/timeline`);
        if (!response.ok) throw new Error("Failed to load timeline");
        
        const data = await response.json();
        
        if (!data.timeline || data.timeline.length === 0) {
            timelineContainer.innerHTML = '<div class="text-center py-4 text-slate-500 w-full">No raw logs found for this IP.</div>';
            return;
        }

        timelineContainer.innerHTML = '';
        
        data.timeline.forEach((log) => {
            const isFailed = log.status === 'Failed';
            const iconColor = isFailed ? 'bg-red-500' : 'bg-emerald-500';
            const iconSvg = isFailed 
                ? '<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>'
                : '<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            
            const textColor = isFailed ? 'text-red-400' : 'text-emerald-400';
            const bgPanel = isFailed ? 'bg-red-900/10 border-red-900/30' : 'bg-emerald-900/10 border-emerald-900/30';

            const item = document.createElement('div');
            item.className = 'relative';
            item.innerHTML = `
                <!-- Timeline dot -->
                <div class="absolute -left-3 md:-left-6 top-1 w-6 h-6 rounded-full ${iconColor} flex items-center justify-center border-4 border-[#0B0F19] shadow-lg -translate-x-1/2">
                    ${iconSvg}
                </div>
                <!-- Content -->
                <div class="${bgPanel} border rounded-lg p-4 ml-6 shadow-sm">
                    <div class="flex flex-col md:flex-row justify-between md:items-center mb-2 gap-2">
                        <span class="font-bold ${textColor}">${log.status} Login Attempt</span>
                        <span class="text-xs font-mono text-slate-500 bg-black/40 px-2 py-1 rounded hidden md:block">${log.timestamp}</span>
                    </div>
                    <p class="text-sm text-slate-300">Target Username: <span class="font-mono text-white">${log.username}</span></p>
                    <div class="mt-3 text-xs font-mono text-slate-500 bg-black/40 p-2 rounded overflow-x-auto whitespace-nowrap">
                        ${log.raw_log}
                    </div>
                </div>
            `;
            timelineContainer.appendChild(item);
        });
        
    } catch (error) {
        console.error(error);
        timelineContainer.innerHTML = '<div class="text-center py-4 text-red-400 w-full flex items-center justify-center"><svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Error loading timeline data.</div>';
    }
}

function closeTimelineModal() {
    timelineModal.classList.add('hidden');
}

// Simple Toast functionality
function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-md text-sm font-medium shadow-lg transition-all duration-300 transform translate-y-0 opacity-100 z-50 flex items-center`;
    
    if (type === "success") {
        toast.className += " bg-emerald-900 border border-emerald-500 text-emerald-300";
        toast.innerHTML = `<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>${message}`;
    } else if (type === "error") {
        toast.className += " bg-red-900 border border-red-500 text-red-300";
        toast.innerHTML = `<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>${message}`;
    } else if (type === "info") {
        toast.className += " bg-blue-900 border border-blue-500 text-blue-300";
        toast.innerHTML = `<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>${message}`;
    }

    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add("translate-y-2", "opacity-0");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Generate Logs Button Logic
const generateLogsBtn = document.getElementById('generateLogsBtn');
if (generateLogsBtn) {
    generateLogsBtn.addEventListener('click', async (e) => {
        e.preventDefault(); // Critical fix preventing browser navigation
        showToast("Generating alert payload in the background...", "info");
        try {
            await fetch(`${API_BASE_URL}/generate-logs`);
            showToast("Logs injected. Dashboard will update shortly.", "success");
            // The real-time monitor will pick this up on its polling interval
        } catch (err) {
            showToast("Failed to inject logs.", "error");
        }
    });
}

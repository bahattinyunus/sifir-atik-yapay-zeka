/**
 * Sıfır Atık YZ - Akıllı Kontrol Paneli v2.0
 * Gerçek zamanlı WebSocket iletişimi, interaktif grafikler ve sistem yönetimi.
 */

// API Temel Adresi
const API_BASE = window.location.origin.includes('8000') 
    ? window.location.origin 
    : 'http://localhost:8000';
const WS_URL = API_BASE.replace('http', 'ws') + '/ws';

// Malzeme ve Polimer Tanımlamaları
const wasteTypesConfig = {
    'PET': { name: 'PET Şişe / Levha', class: 'pet', icon: '🍾' },
    'HDPE': { name: 'HDPE Bidon / Kapak', class: 'hdpe', icon: '🧴' },
    'Naylon': { name: 'Naylon (Poliamid)', class: 'nylon', icon: '🧵' },
    'PUR': { name: 'PUR (Poliüretan)', class: 'pur', icon: '🧽' },
    'Metal': { name: 'Alüminyum / Metal', class: 'metal', icon: '🥫' },
    'Reject': { name: 'Tanımlanamayan / Diğer', class: 'reject', icon: '🗑️' }
};

// Global Durum
let stats = {
    total_count: 0,
    counts: { PET: 0, HDPE: 0, Naylon: 0, PUR: 0, Metal: 0, Reject: 0 },
    avg_confidence: 94.2,
    ppm: 0.0
};

let doughnutChart = null;
let hourlyChart = null;
let ws = null;
let reconnectTimer = null;

// ===================== SEKME (TAB) YÖNETİMİ =====================
function initTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const pageTitle = document.getElementById('page-title');

    const titles = {
        'tab-dashboard': 'Sistem Kontrol Merkezi (Genel Bakış)',
        'tab-camera': 'Canlı Konveyör Bant ve Görsel Yapay Zeka',
        'tab-analytics': 'Polimer Sınıflandırma ve Veri Analitiği',
        'tab-reports': 'Atık Kayıt Kütüğü ve Denetim (Audit Log)',
        'tab-settings': 'Sistem Kalibrasyonu ve Donanım Parametreleri'
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetId = item.getAttribute('data-tab');
            navItems.forEach(n => n.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            item.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');

            if (pageTitle && titles[targetId]) {
                pageTitle.innerText = titles[targetId];
            }

            // Sekme açıldığında ilgili veriyi güncelle
            if (targetId === 'tab-reports') loadHistoryData();
            if (targetId === 'tab-analytics') fetchStatsAndRefreshCharts();
            if (targetId === 'tab-settings') loadSettingsAndHealth();
        });
    });
}

// ===================== BİLDİRİM (TOAST) =====================
function showToast(message, isError = false) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${isError ? 'error' : ''}`;
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ===================== WEBSOCKET BAĞLANTISI =====================
function connectWebSocket() {
    if (ws) {
        try { ws.close(); } catch(e) {}
    }

    const pulse = document.getElementById('ws-pulse');
    const statusText = document.getElementById('ws-status-text');

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log("WebSocket bağlantısı başarıyla kuruldu.");
        if (pulse) pulse.className = "pulse-dot online";
        if (statusText) statusText.innerText = "Canlı Edge Bağlı";
        showToast("Sunucuya canlı WebSocket bağlantısı sağlandı.");
        clearInterval(reconnectTimer);
    };

    ws.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            handleIncomingMessage(payload);
        } catch (e) {
            console.error("Gelen veri işleme hatası:", e);
        }
    };

    ws.onclose = () => {
        if (pulse) pulse.className = "pulse-dot";
        if (statusText) statusText.innerText = "Bağlantı Bekleniyor...";
        console.log("WebSocket koptu. 3 saniye sonra yeniden deneniyor...");
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
        console.warn("WebSocket bağlantı hatası:", err);
    };
}

// Gelen WebSocket Olaylarını Yönetme
function handleIncomingMessage(msg) {
    if (msg.event === 'init_stats') {
        updateStatsState(msg.data);
    } else if (msg.event === 'detection') {
        addLiveFeedItem(msg);
        if (msg.stats) updateStatsState(msg.stats);
        // Canlı kameradaki HUD çıkarım süresini güncelle
        const hudInf = document.getElementById('hud-inference');
        if (hudInf && msg.inference_ms) {
            hudInf.innerText = `Inference: ${msg.inference_ms} ms`;
        }
    } else if (msg.event === 'emergency_stop') {
        showToast("🛑 DİKKAT: Acil durdurma (E-STOP) tetiklendi!", true);
        const badge = document.getElementById('system-badge');
        if (badge) {
            badge.innerText = "E-STOP KİLİTLENDİ";
            badge.style.background = "rgba(239, 68, 68, 0.2)";
            badge.style.borderColor = "#ef4444";
            badge.style.color = "#ef4444";
        }
    } else if (msg.event === 'emergency_stop_reset') {
        showToast("✅ Acil durdurma sıfırlandı. Sistem çalışıyor.");
        const badge = document.getElementById('system-badge');
        if (badge) {
            badge.innerText = "Aktif - Otonom Mod";
            badge.style.background = "rgba(16, 185, 129, 0.15)";
            badge.style.borderColor = "rgba(16, 185, 129, 0.3)";
            badge.style.color = "var(--accent)";
        }
    }
}

// İstatistikleri ve Arayüzü Güncelleme
function updateStatsState(newStats) {
    stats = newStats;
    const c = stats.counts || {};

    const elPet = document.getElementById('pet-count');
    const elHdpe = document.getElementById('hdpe-count');
    const elNylon = document.getElementById('nylon-count');
    const elPur = document.getElementById('pur-count');
    const elMetal = document.getElementById('metal-count');
    const elReject = document.getElementById('reject-count');

    if (elPet) elPet.innerText = (c.PET || 0).toLocaleString('tr-TR');
    if (elHdpe) elHdpe.innerText = (c.HDPE || 0).toLocaleString('tr-TR');
    if (elNylon) elNylon.innerText = (c.Naylon || 0).toLocaleString('tr-TR');
    if (elPur) elPur.innerText = (c.PUR || 0).toLocaleString('tr-TR');
    if (elMetal) elMetal.innerText = (c.Metal || 0).toLocaleString('tr-TR');
    if (elReject) elReject.innerText = (c.Reject || 0).toLocaleString('tr-TR');

    const totalCounter = document.getElementById('total-feed-counter');
    if (totalCounter) totalCounter.innerText = `Toplam: ${(stats.total_count || 0).toLocaleString('tr-TR')}`;

    const ppmVal = document.getElementById('ppm-val');
    if (ppmVal) ppmVal.innerText = (stats.ppm || 0.0).toFixed(1);

    // Verimlilik Halkası
    const effVal = document.getElementById('efficiency-value');
    const circle = document.getElementById('progress-circle');
    const conf = stats.avg_confidence || 94.2;
    if (effVal) effVal.innerText = `%${conf.toFixed(1)}`;
    if (circle) {
        const deg = (conf / 100) * 360;
        circle.style.background = `conic-gradient(var(--accent) ${deg}deg, rgba(255, 255, 255, 0.08) 0deg)`;
    }

    // Grafikleri güncelle
    updateDoughnutChart();
}

// Canlı Akışa Yeni Öğe Ekleme
function addLiveFeedItem(data) {
    const feedList = document.getElementById('feed-list');
    if (!feedList) return;

    const wasteConfig = wasteTypesConfig[data.type] || wasteTypesConfig['Reject'];
    const item = document.createElement('div');
    item.className = 'feed-item';

    item.innerHTML = `
        <div class="feed-item-left">
            <span style="font-size: 1.5rem">${wasteConfig.icon}</span>
            <div>
                <span class="badge ${wasteConfig.class}">${wasteConfig.name}</span>
                <div class="time">${data.timestamp || 'Yeni'} • ${data.inference_ms ? data.inference_ms + ' ms' : ''}</div>
            </div>
        </div>
        <div class="feed-item-right">
            <div class="confidence">%${Number(data.confidence || 0).toFixed(1)}</div>
            <div class="time">${data.actuated !== false ? '⚡ Valf Açıldı' : '🛑 Pas Geçildi'}</div>
        </div>
    `;

    feedList.insertBefore(item, feedList.firstChild);

    // Listede en fazla 7 öğe tut
    if (feedList.children.length > 7) {
        feedList.removeChild(feedList.lastChild);
    }

    const lastUp = document.getElementById('last-update');
    if (lastUp) lastUp.innerText = data.timestamp || new Date().toLocaleTimeString('tr-TR');
}

// ===================== CHART.JS GRAFİKLERİ =====================
function initCharts() {
    const doughnutCanvas = document.getElementById('chart-doughnut');
    if (doughnutCanvas && typeof Chart !== 'undefined') {
        const ctx = doughnutCanvas.getContext('2d');
        doughnutChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['PET', 'HDPE', 'Naylon', 'PUR', 'Metal', 'Reject'],
                datasets: [{
                    data: [0, 0, 0, 0, 0, 0],
                    backgroundColor: ['#38bdf8', '#f59e0b', '#c084fc', '#2dd4bf', '#94a3b8', '#ef4444'],
                    borderColor: '#0f172a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
                    }
                }
            }
        });
    }

    const hourlyCanvas = document.getElementById('chart-hourly');
    if (hourlyCanvas && typeof Chart !== 'undefined') {
        const ctx2 = hourlyCanvas.getContext('2d');
        hourlyChart = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00'],
                datasets: [
                    {
                        label: 'PET / HDPE',
                        data: [42, 58, 65, 48, 72, 80],
                        backgroundColor: '#38bdf8'
                    },
                    {
                        label: 'Naylon / PUR / Metal',
                        data: [18, 24, 30, 22, 35, 41],
                        backgroundColor: '#2dd4bf'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                },
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                }
            }
        });
    }
}

function updateDoughnutChart() {
    if (!doughnutChart) return;
    const c = stats.counts || {};
    doughnutChart.data.datasets[0].data = [
        c.PET || 0,
        c.HDPE || 0,
        c.Naylon || 0,
        c.PUR || 0,
        c.Metal || 0,
        c.Reject || 0
    ];
    doughnutChart.update();
}

async function fetchStatsAndRefreshCharts() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (res.ok) {
            const data = await res.json();
            if (data.summary) updateStatsState(data.summary);
            if (data.hourly_breakdown && hourlyChart) {
                // Saatlik dökümü grafiğe işle
                const hours = [...new Set(data.hourly_breakdown.map(h => h.hour))];
                if (hours.length > 0) {
                    hourlyChart.data.labels = hours;
                    hourlyChart.update();
                }
            }
        }
    } catch (e) {
        console.warn("Grafik verileri alınamadı:", e);
    }
}

// ===================== RAPORLAR VE AUDIT LOG =====================
async function loadHistoryData() {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">Kayıtlar SQLite kütüğünden getiriliyor...</td></tr>';
    try {
        const res = await fetch(`${API_BASE}/api/history?limit=40`);
        if (!res.ok) throw new Error("HTTP " + res.status);
        const list = await res.json();

        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading-cell">Henüz kayıtlı atık tespiti bulunmuyor.</td></tr>';
            return;
        }

        tbody.innerHTML = list.map(item => {
            const cfg = wasteTypesConfig[item.waste_type] || wasteTypesConfig['Reject'];
            return `
                <tr>
                    <td>#${item.id}</td>
                    <td><span class="badge ${cfg.class}">${cfg.icon} ${item.waste_type}</span></td>
                    <td><strong>%${Number(item.confidence).toFixed(1)}</strong></td>
                    <td>${item.timestamp} <small style="color:var(--text-muted)">(${item.created_at || ''})</small></td>
                    <td>${item.inference_ms || 14.5} ms</td>
                    <td>${item.actuated ? '<span style="color:#10b981">Ayrıştırıldı (Valf)</span>' : '<span style="color:#ef4444">Pas Geçildi</span>'}</td>
                    <td><code>${item.source || 'edge'}</code></td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="loading-cell" style="color:#ef4444">Kayıtlar yüklenemedi: ${err.message}</td></tr>`;
    }
}

// ===================== SİSTEM AYARLARI VE DONANIM SAĞLIĞI =====================
async function loadSettingsAndHealth() {
    try {
        const [cfgRes, healthRes] = await Promise.all([
            fetch(`${API_BASE}/api/config`),
            fetch(`${API_BASE}/api/system-status`)
        ]);

        if (cfgRes.ok) {
            const cfg = await cfgRes.json();
            if (cfg.conveyor_speed_m_s) document.getElementById('cfg-conveyor-speed').value = cfg.conveyor_speed_m_s;
            if (cfg.valve_delay_ms) document.getElementById('cfg-valve-delay').value = cfg.valve_delay_ms;
            if (cfg.valve_pulse_ms) document.getElementById('cfg-valve-pulse').value = cfg.valve_pulse_ms;
            if (cfg.confidence_threshold) document.getElementById('cfg-confidence').value = cfg.confidence_threshold;
        }

        if (healthRes.ok) {
            const h = await healthRes.json();
            document.getElementById('sys-cpu').innerText = `%${h.cpu_usage_pct}`;
            document.getElementById('sys-ram').innerText = `%${h.ram_usage_pct} (${h.ram_available_mb} MB Boş)`;
            document.getElementById('sys-disk').innerText = `${h.disk_free_gb} GB Boş`;
            document.getElementById('sys-uptime').innerText = h.uptime_formatted;
            document.getElementById('sys-ws').innerText = `${h.active_ws_clients} Aktif İstemci`;

            // Mini metrikler
            const mCpu = document.getElementById('mini-cpu');
            const mRam = document.getElementById('mini-ram');
            if (mCpu) mCpu.innerText = `%${h.cpu_usage_pct}`;
            if (mRam) mRam.innerText = `${h.ram_available_mb} MB`;
        }
    } catch (e) {
        console.warn("Ayarlar veya donanım durumu alınamadı:", e);
    }
}

// ===================== BUTON ETKİLEŞİMLERİ =====================
function initEventHandlers() {
    // Hızlı Simülasyon
    const btnSim = document.getElementById('btn-quick-sim');
    if (btnSim) {
        btnSim.addEventListener('click', async () => {
            btnSim.disabled = true;
            btnSim.innerText = "⏳ Gönderiliyor...";
            try {
                const res = await fetch(`${API_BASE}/api/simulate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ count: 1 })
                });
                if (res.ok) {
                    showToast("⚡ Simüle atık tespiti üretildi ve sisteme aktarıldı.");
                } else {
                    showToast("Simülasyon gönderilemedi.", true);
                }
            } catch (e) {
                showToast("Backend'e ulaşılamadı.", true);
            } finally {
                btnSim.disabled = false;
                btnSim.innerText = "⚡ Simüle Atık Gönder";
            }
        });
    }

    // CSV İndir
    const btnCsv = document.getElementById('btn-export-csv');
    if (btnCsv) {
        btnCsv.addEventListener('click', () => {
            window.open(`${API_BASE}/api/export/csv`, '_blank');
            showToast("📥 CSV Raporu indirme isteği gönderildi.");
        });
    }

    // Rapor Listesini Yenile
    const btnRefHist = document.getElementById('btn-refresh-history');
    if (btnRefHist) btnRefHist.addEventListener('click', loadHistoryData);

    // Ayarları Kaydet Formu
    const formSettings = document.getElementById('settings-form');
    if (formSettings) {
        formSettings.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                conveyor_speed_m_s: document.getElementById('cfg-conveyor-speed').value,
                valve_delay_ms: document.getElementById('cfg-valve-delay').value,
                valve_pulse_ms: document.getElementById('cfg-valve-pulse').value,
                confidence_threshold: document.getElementById('cfg-confidence').value
            };

            try {
                const res = await fetch(`${API_BASE}/api/config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    showToast("💾 Ayarlar başarıyla kaydedildi ve tüm uçlara iletildi.");
                    const miniSpeed = document.getElementById('mini-speed');
                    if (miniSpeed) miniSpeed.innerText = `${payload.conveyor_speed_m_s} m/s`;
                } else {
                    showToast("Ayarlar kaydedilemedi.", true);
                }
            } catch (err) {
                showToast("Sunucu iletişim hatası: " + err.message, true);
            }
        });
    }

    // Acil Durdurma (E-STOP) Butonu
    const btnEstop = document.getElementById('btn-estop');
    if (btnEstop) {
        btnEstop.addEventListener('click', async () => {
            if (confirm("DİKKAT: Konveyör bant ve tüm valfleri acil olarak durdurmak istediğinize emin misiniz?")) {
                try {
                    await fetch(`${API_BASE}/api/e-stop`, { method: 'POST' });
                } catch(e) {
                    showToast("E-STOP gönderilemedi: " + e.message, true);
                }
            }
        });
    }

    // E-STOP Sıfırlama Butonu
    const btnResetEstop = document.getElementById('btn-reset-estop');
    if (btnResetEstop) {
        btnResetEstop.addEventListener('click', async () => {
            try {
                await fetch(`${API_BASE}/api/e-stop/reset`, { method: 'POST' });
            } catch(e) {
                showToast("E-STOP sıfırlanamadı: " + e.message, true);
            }
        });
    }

    // Kamera Yayını Yenile
    const btnRefreshCam = document.getElementById('btn-refresh-cam');
    if (btnRefreshCam) {
        btnRefreshCam.addEventListener('click', () => {
            const camImg = document.getElementById('live-stream-img');
            if (camImg) {
                camImg.src = `${API_BASE}/video_feed?t=${Date.now()}`;
                showToast("📷 Video akışı yeniden başlatıldı.");
            }
        });
    }
}

// Periyodik Donanım Durumu ve İstatistik Polling
setInterval(() => {
    loadSettingsAndHealth();
}, 10000);

// ===================== BAŞLATMA =====================
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCharts();
    initEventHandlers();
    connectWebSocket();
    fetchStatsAndRefreshCharts();
    loadSettingsAndHealth();
});

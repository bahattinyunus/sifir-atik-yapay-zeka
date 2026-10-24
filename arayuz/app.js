/**
 * Sıfır Atık YZ - Akıllı Kontrol Paneli v2.5 by bahattinyunus
 * Gerçek zamanlı WebSocket iletişimi, Chart.js analitiği, ESG çevresel etki hesaplayıcı
 * ve interaktif 2D HTML5 Canvas konveyör bant simülatörü.
 */

// API Temel Adresi
const API_BASE = window.location.origin.includes('8000') 
    ? window.location.origin 
    : 'http://localhost:8000';
const WS_URL = API_BASE.replace('http', 'ws') + '/ws';

// Malzeme ve Polimer Tanımlamaları
const wasteTypesConfig = {
    'PET': { name: 'PET Şişe / Levha', class: 'pet', icon: '🍾', color: '#38bdf8', valveIdx: 1, valveX: 340 },
    'HDPE': { name: 'HDPE Bidon / Kapak', class: 'hdpe', icon: '🧴', color: '#f59e0b', valveIdx: 2, valveX: 460 },
    'Naylon': { name: 'Naylon (Poliamid)', class: 'nylon', icon: '🧵', color: '#c084fc', valveIdx: 3, valveX: 580 },
    'PUR': { name: 'PUR (Poliüretan)', class: 'pur', icon: '🧽', color: '#2dd4bf', valveIdx: 4, valveX: 700 },
    'Metal': { name: 'Alüminyum / Metal', class: 'metal', icon: '🥫', color: '#94a3b8', valveIdx: 5, valveX: 820 },
    'Reject': { name: 'Tanımlanamayan / Diğer', class: 'reject', icon: '🗑️', color: '#ef4444', valveIdx: 0, valveX: 890 }
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
        'tab-sim': 'İnteraktif Konveyör Bant & Valf Simülatörü',
        'tab-analytics': 'Polimer Sınıflandırma ve Veri Analitiği',
        'tab-eco': 'Çevresel Etki Analitiği (ESG & Karbon Tasarrufu)',
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
            if (targetId === 'tab-eco') loadEcoImpactData();
            if (targetId === 'tab-settings') {
                loadSettingsAndHealth();
                loadSystemLogs();
            }
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
        
        // Simülatör açıksa nesne oluştur
        if (simulator) {
            simulator.spawnItem(msg.type, msg.confidence);
        }

        // Valf göstergelerini anlık tetikle
        triggerValvePillAnimation(msg.type);

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

function triggerValvePillAnimation(wasteType) {
    const map = {
        'PET': 'vstatus-pet',
        'HDPE': 'vstatus-hdpe',
        'Naylon': 'vstatus-nylon',
        'PUR': 'vstatus-pur',
        'Metal': 'vstatus-metal'
    };
    const id = map[wasteType];
    if (id) {
        const el = document.getElementById(id);
        if (el) {
            el.innerText = "Ateşlendi! (120ms)";
            el.style.color = "#38bdf8";
            el.style.fontWeight = "bold";
            setTimeout(() => {
                el.innerText = "Hazır";
                el.style.color = "var(--accent)";
                el.style.fontWeight = "600";
            }, 600);
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

// ===================== ÇEVRESEL ETKİ (ESG) =====================
async function loadEcoImpactData() {
    try {
        const res = await fetch(`${API_BASE}/api/environmental-impact`);
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('eco-mass').innerHTML = `${data.total_mass_kg} <span class="unit">kg</span>`;
        document.getElementById('eco-co2').innerHTML = `${data.total_co2_saved_kg} <span class="unit">kg CO₂</span>`;
        document.getElementById('eco-trees').innerHTML = `${data.equivalent_trees_saved} <span class="unit">Ağaç / Yıl</span>`;
        document.getElementById('eco-energy').innerHTML = `${data.total_energy_saved_kwh} <span class="unit">kWh</span>`;
        document.getElementById('eco-water').innerHTML = `${data.total_water_saved_liters} <span class="unit">Litre</span>`;

        const tbody = document.getElementById('eco-table-body');
        if (tbody && data.by_polymer) {
            tbody.innerHTML = Object.entries(data.by_polymer).map(([poly, info]) => {
                const cfg = wasteTypesConfig[poly] || wasteTypesConfig['Reject'];
                return `
                    <tr>
                        <td><span class="badge ${cfg.class}">${cfg.icon} ${poly}</span></td>
                        <td>${info.count.toLocaleString('tr-TR')} adet</td>
                        <td><strong>${info.mass_kg} kg</strong></td>
                        <td style="color:var(--accent)"><strong>-${info.co2_saved_kg} kg CO₂</strong></td>
                        <td>${info.energy_saved_kwh} kWh</td>
                    </tr>
                `;
            }).join('');
        }
    } catch (e) {
        console.warn("Çevresel veri alınamadı:", e);
    }
}

// ===================== SİSTEM LOGLARI =====================
async function loadSystemLogs() {
    const box = document.getElementById('system-logs-box');
    if (!box) return;
    try {
        const res = await fetch(`${API_BASE}/api/logs?limit=25`);
        if (!res.ok) return;
        const logs = await res.json();
        if (logs.length === 0) {
            box.innerHTML = '<div>Henüz sistem logu bulunmuyor.</div>';
            return;
        }
        box.innerHTML = logs.map(l => {
            const color = l.level === 'WARNING' ? '#ef4444' : (l.level === 'CONFIG' ? '#38bdf8' : '#10b981');
            return `<div style="margin-bottom: 0.35rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 0.25rem;">
                <span style="color:var(--text-muted)">[${l.timestamp}]</span>
                <span style="color:${color}; font-weight:bold;">[${l.level}]</span>
                <span>${l.message}</span>
            </div>`;
        }).join('');
    } catch (e) {
        box.innerHTML = `<div style="color:#ef4444">Loglar yüklenemedi: ${e.message}</div>`;
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
                    <td>${item.inference_ms || 2.7} ms</td>
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

            const mCpu = document.getElementById('mini-cpu');
            const mRam = document.getElementById('mini-ram');
            if (mCpu) mCpu.innerText = `%${h.cpu_usage_pct}`;
            if (mRam) mRam.innerText = `${h.ram_available_mb} MB`;
        }
    } catch (e) {
        console.warn("Ayarlar veya donanım durumu alınamadı:", e);
    }
}

// ===================== İNTERAKTİF 2D KONVEYÖR BANT SİMÜLATÖRÜ =====================
class ConveyorSimulator {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.items = [];
        this.particles = [];
        this.speed = 2.4;
        this.autoFlow = false;
        this.autoTimer = null;
        this.beltOffset = 0;

        this.valves = [
            { type: 'PET', name: 'Valf 1 (PET)', x: 340, color: '#38bdf8' },
            { type: 'HDPE', name: 'Valf 2 (HDPE)', x: 460, color: '#f59e0b' },
            { type: 'Naylon', name: 'Valf 3 (Naylon)', x: 580, color: '#c084fc' },
            { type: 'PUR', name: 'Valf 4 (PUR)', x: 700, color: '#2dd4bf' },
            { type: 'Metal', name: 'Valf 5 (Metal)', x: 820, color: '#94a3b8' }
        ];

        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);
    }

    spawnItem(type = 'PET', confidence = 96.5) {
        const item = {
            id: Date.now() + Math.random(),
            type: type,
            confidence: confidence,
            x: 20,
            y: 130,
            width: 38,
            height: 38,
            detected: false,
            falling: false,
            fallVy: 0,
            active: true
        };
        this.items.push(item);
    }

    triggerAirBlast(x, color) {
        for (let i = 0; i < 24; i++) {
            this.particles.push({
                x: x + (Math.random() * 20 - 10),
                y: 100 + Math.random() * 10,
                vx: (Math.random() - 0.5) * 2.5,
                vy: Math.random() * 6 + 4,
                life: 1.0,
                color: color
            });
        }
    }

    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(this.animate);
    }

    update() {
        this.beltOffset = (this.beltOffset + this.speed) % 30;

        for (let item of this.items) {
            if (!item.active) continue;

            if (!item.falling) {
                item.x += this.speed;

                // Kamera Algılama Alanı (x = 180 - 240)
                if (item.x > 180 && !item.detected) {
                    item.detected = true;
                }

                // İlgili Valf Nozulu Kontrolü
                for (let v of this.valves) {
                    if (item.type === v.type && Math.abs(item.x - v.x) < 8) {
                        item.falling = true;
                        this.triggerAirBlast(v.x, v.color);
                        break;
                    }
                }

                // Reject atıklar bant sonundan düşer
                if (item.x > 875) {
                    item.falling = true;
                }
            } else {
                // Aşağı düşme fiziği
                item.fallVy += 0.45;
                item.y += item.fallVy;
                if (item.y > 330) {
                    item.active = false;
                }
            }
        }

        // Parçacık fiziği
        for (let p of this.particles) {
            p.x += p.vx;
            p.y += p.vy;
            p.life -= 0.04;
        }
        this.particles = this.particles.filter(p => p.life > 0);
        this.items = this.items.filter(item => item.active);
    }

    draw() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        ctx.clearRect(0, 0, w, h);

        // 1. Konveyör Bant Çerçevesi
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 115, w, 70);

        // Bant Şeritleri
        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 2;
        for (let x = -30 + this.beltOffset; x < w; x += 30) {
            ctx.beginPath();
            ctx.moveTo(x, 115);
            ctx.lineTo(x + 15, 185);
            ctx.stroke();
        }

        // Bant Kenarlıkları
        ctx.strokeStyle = '#64748b';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, 115); ctx.lineTo(w, 115);
        ctx.moveTo(0, 185); ctx.lineTo(w, 185);
        ctx.stroke();

        // 2. Kamera & AI Algılama Alanı (ROI)
        ctx.strokeStyle = '#10b981';
        ctx.fillStyle = 'rgba(16, 185, 129, 0.08)';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);
        ctx.strokeRect(170, 95, 100, 100);
        ctx.fillRect(170, 95, 100, 100);
        ctx.setLineDash([]);
        ctx.fillStyle = '#10b981';
        ctx.font = '11px Inter, monospace';
        ctx.fillText('📷 AI ZONE (ROI)', 175, 88);

        // 3. Pnömatik Solenoid Valfler ve Nozullar
        for (let v of this.valves) {
            // Nozul başlığı
            ctx.fillStyle = '#475569';
            ctx.fillRect(v.x - 8, 92, 16, 18);
            ctx.fillStyle = v.color;
            ctx.beginPath();
            ctx.arc(v.x, 110, 5, 0, Math.PI * 2);
            ctx.fill();

            // Etiket
            ctx.fillStyle = '#94a3b8';
            ctx.font = '10px Inter';
            ctx.textAlign = 'center';
            ctx.fillText(v.type, v.x, 82);

            // Alt Hazne (Toplama Kutusu)
            ctx.strokeStyle = v.color;
            ctx.fillStyle = 'rgba(255,255,255,0.03)';
            ctx.lineWidth = 1.5;
            ctx.strokeRect(v.x - 22, 230, 44, 80);
            ctx.fillRect(v.x - 22, 230, 44, 80);
            ctx.fillStyle = v.color;
            ctx.fillText('📦 ' + v.type, v.x, 260);
        }

        // Bant Sonu Reject Haznesi
        ctx.textAlign = 'center';
        ctx.strokeStyle = '#ef4444';
        ctx.fillStyle = 'rgba(239, 68, 68, 0.05)';
        ctx.strokeRect(865, 230, 32, 80);
        ctx.fillRect(865, 230, 32, 80);
        ctx.fillStyle = '#ef4444';
        ctx.fillText('🗑️', 881, 260);

        // 4. Parçacıklar (Hava Püskürtme Efekti)
        for (let p of this.particles) {
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalAlpha = 1.0;

        // 5. Atık Nesneleri
        for (let item of this.items) {
            const cfg = wasteTypesConfig[item.type] || wasteTypesConfig['Reject'];
            ctx.fillStyle = cfg.color;
            ctx.fillRect(item.x - 16, item.y - 16, 32, 32);

            // Bounding Box
            if (item.detected && !item.falling) {
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 2;
                ctx.strokeRect(item.x - 20, item.y - 20, 40, 40);
                ctx.fillStyle = '#fff';
                ctx.font = '10px Inter';
                ctx.textAlign = 'center';
                ctx.fillText(`%${item.confidence.toFixed(0)}`, item.x, item.y - 24);
            }

            // İkon
            ctx.font = '16px Inter';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(cfg.icon, item.x, item.y);
        }
        ctx.textBaseline = 'alphabetic';
        ctx.textAlign = 'start';
    }

    toggleAutoFlow(btn) {
        this.autoFlow = !this.autoFlow;
        if (this.autoFlow) {
            btn.innerText = "⏸️ Akışı Durdur";
            btn.style.background = "#f59e0b";
            this.autoTimer = setInterval(() => {
                const types = ['PET', 'HDPE', 'Naylon', 'PUR', 'Metal'];
                const randType = types[Math.floor(Math.random() * types.length)];
                const conf = 88.0 + Math.random() * 11.5;
                this.spawnItem(randType, conf);
            }, 1800);
        } else {
            btn.innerText = "▶️ Otomatik Akışı Başlat";
            btn.style.background = "var(--accent)";
            clearInterval(this.autoTimer);
        }
    }

    clear() {
        this.items = [];
        this.particles = [];
    }
}

let simulator = null;

// ===================== BUTON ETKİLEŞİMLERİ =====================
function initEventHandlers() {
    // Simülatör Tuşları
    const btnFlow = document.getElementById('btn-toggle-sim-flow');
    if (btnFlow && simulator) {
        btnFlow.addEventListener('click', () => simulator.toggleAutoFlow(btnFlow));
    }

    const btnClearSim = document.getElementById('btn-clear-sim');
    if (btnClearSim && simulator) {
        btnClearSim.addEventListener('click', () => simulator.clear());
    }

    document.querySelectorAll('.btn-sim-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.getAttribute('data-drop');
            if (simulator) simulator.spawnItem(type, 97.4);
            showToast(`Bant üzerine ${type} atığı bırakıldı.`);
        });
    });

    // Hızlı Simülasyon (Backend'e)
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

    // Logları Yenile
    const btnRefLogs = document.getElementById('btn-refresh-logs');
    if (btnRefLogs) btnRefLogs.addEventListener('click', loadSystemLogs);

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

// Periyodik Polling
setInterval(() => {
    loadSettingsAndHealth();
}, 10000);

// ===================== BAŞLATMA =====================
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCharts();
    simulator = new ConveyorSimulator('conveyor-canvas');
    initEventHandlers();
    connectWebSocket();
    fetchStatsAndRefreshCharts();
    loadSettingsAndHealth();
    loadEcoImpactData();
});

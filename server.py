from datetime import datetime, timezone
import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "readings.db")

app = Flask(__name__)
CORS(app)

DASHBOARD_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32 Health Monitor</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; font-family: Poppins, sans-serif; color: #fff;
      background: linear-gradient(135deg, #833ab4 0%, #fd1d1d 52%, #fcb045 100%);
      padding: 28px;
    }
    header { max-width: 1200px; margin: 0 auto 24px; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px; }
    h1 { margin:0; font-size:clamp(1.5rem, 4vw, 2.3rem); }
    .sub { opacity:.85; margin-top:6px; }
    .pill { background:#ffffff24; border:1px solid #ffffff55; padding:9px 14px; border-radius:30px; }
    main { max-width:1200px; margin:auto; }
    .devices { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:18px; }
    .card { background:#171326d9; border:1px solid #ffffff30; border-radius:20px; padding:20px; box-shadow:0 12px 32px #1b102533; backdrop-filter:blur(10px); }
    .cardhead { display:flex; align-items:center; justify-content:space-between; gap:10px; margin-bottom:16px; }
    h2 { font-size:1.15rem; margin:0; }
    .status { border-radius:20px; padding:5px 10px; font-size:.75rem; font-weight:600; }
    .online { background:#176b3a; color:#aaffc4; } .offline { background:#6d2830; color:#ffd4d4; }
    .metrics { display:grid; grid-template-columns:repeat(3,1fr); gap:9px; }
    .metric { background:#ffffff0e; border-radius:13px; padding:12px 8px; text-align:center; }
    .label { font-size:.72rem; opacity:.8; } .value { font-size:1.3rem; font-weight:700; margin-top:4px; overflow-wrap:anywhere; }
    .normal { color:#55e88b; } .warning { color:#ffd45c; } .abnormal { color:#ff6868; }
    .chart-card { margin-top:20px; } .chart-wrap { height:280px; }
    .foot { opacity:.82; font-size:.82rem; margin:18px 2px 0; line-height:1.6; }
    @media(max-width:500px){ body{padding:15px;} .metrics{grid-template-columns:1fr;} .metric{display:flex;justify-content:space-between;align-items:center;} .value{margin:0;} }
  </style>
</head>
<body>
<header>
  <div><h1>❤️ Real-Time Health Monitor</h1><div class="sub">Multi-device ESP32 monitoring dashboard</div></div>
  <div class="pill">Last refresh: <span id="lastRefresh">Waiting…</span></div>
</header>
<main>
  <section id="devices" class="devices"></section>
  <section class="card chart-card">
    <div class="cardhead"><h2>Recent readings</h2><span class="pill">Temperature · SpO₂ · Heart rate</span></div>
    <div class="chart-wrap"><canvas id="chart"></canvas></div>
  </section>
  <p class="foot">Educational demonstration only — not a medical device. Readings can be inaccurate and must not be used for diagnosis or treatment. A device is marked offline if no update has arrived for 10 seconds.</p>
</main>
<script>
const ids = [1,2,3];
const history = {};
ids.forEach(id => history[id] = {labels:[], temp:[], spo2:[], hr:[]});
const ctx = document.getElementById('chart');
const chart = new Chart(ctx, {
  type:'line',
  data:{labels:[],datasets:[
    {label:'Temperature (°F)',data:[],borderColor:'#ffb454',backgroundColor:'#ffb45422',tension:.25,yAxisID:'y'},
    {label:'SpO₂ (%)',data:[],borderColor:'#55e88b',backgroundColor:'#55e88b22',tension:.25,yAxisID:'y1'},
    {label:'Heart rate (bpm)',data:[],borderColor:'#72b7ff',backgroundColor:'#72b7ff22',tension:.25,yAxisID:'y1'}
  ]},
  options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    scales:{x:{ticks:{color:'#eee'},grid:{color:'#ffffff16'}},
      y:{position:'left',ticks:{color:'#ffcf91'},grid:{color:'#ffffff16'},title:{display:true,text:'Temperature (°F)',color:'#fff'}},
      y1:{position:'right',min:0,max:150,ticks:{color:'#b9dcff'},grid:{drawOnChartArea:false},title:{display:true,text:'SpO₂ (%) / HR (bpm)',color:'#fff'}}},
    plugins:{legend:{labels:{color:'#fff'}}}}
});
function metricClass(type, value) {
  if (value === null || value === undefined || Number(value) <= 0) return 'warning';
  if (type === 'temp') return (value >= 97 && value <= 100.4) ? 'normal' : 'warning';
  if (type === 'spo2') return value >= 95 ? 'normal' : (value >= 90 ? 'warning' : 'abnormal');
  if (type === 'hr') return (value >= 60 && value <= 100) ? 'normal' : 'warning';
  return 'warning';
}
function fmt(value, suffix) { return value === null || value === undefined ? '--' : `${value}${suffix}`; }
function renderDevices(data) {
  const now = Date.now();
  document.getElementById('devices').innerHTML = ids.map(id => {
    const d = data[id];
    const online = d && d.updated_at && (now - Date.parse(d.updated_at) < 10000);
    const temp = d ? Number(d.temp) : null, spo2 = d ? Number(d.spo2) : null, hr = d ? Number(d.heart_rate) : null;
    return `<article class="card">
      <div class="cardhead"><h2>ESP32 Device ${id}</h2><span class="status ${online?'online':'offline'}">${online?'ONLINE':'OFFLINE'}</span></div>
      <div class="metrics">
        <div class="metric"><span class="label">Temperature</span><span class="value ${metricClass('temp',temp)}">${d?fmt(temp.toFixed(1),' °F'):'--'}</span></div>
        <div class="metric"><span class="label">SpO₂</span><span class="value ${metricClass('spo2',spo2)}">${d?fmt(spo2,'%'):'--'}</span></div>
        <div class="metric"><span class="label">Heart rate</span><span class="value ${metricClass('hr',hr)}">${d?fmt(hr,' bpm'):'--'}</span></div>
      </div><p class="foot">Updated: ${d && d.updated_at ? new Date(d.updated_at).toLocaleTimeString() : 'No data received'}</p>
    </article>`;
  }).join('');
}
async function refresh() {
  try {
    const res = await fetch('/get_data');
    const data = await res.json();
    renderDevices(data);
    const latest = ids.map(id => data[id]).filter(Boolean).sort((a,b)=>Date.parse(a.updated_at)-Date.parse(b.updated_at)).pop();
    if (latest) {
      const label = new Date(latest.updated_at).toLocaleTimeString();
      chart.data.labels.push(label);
      chart.data.datasets[0].data.push(Number(latest.temp));
      chart.data.datasets[1].data.push(Number(latest.spo2));
      chart.data.datasets[2].data.push(Number(latest.heart_rate));
      if (chart.data.labels.length > 20) {
        chart.data.labels.shift(); chart.data.datasets.forEach(ds => ds.data.shift());
      }
      chart.update('none');
    }
    document.getElementById('lastRefresh').textContent = new Date().toLocaleTimeString();
  } catch (e) { document.getElementById('lastRefresh').textContent = 'Server unavailable'; }
}
refresh(); setInterval(refresh, 2000);
</script>
</body>
</html>
"""

def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with connect_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                temp REAL,
                spo2 REAL,
                heart_rate REAL,
                ts TEXT NOT NULL
            )
        """)

# Latest reading in memory for the live dashboard; history is saved in SQLite.
device_data = {}

@app.get("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "ESP32 Health Monitor"})

@app.post("/data")
def receive_data():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected JSON object"}), 400
    try:
        device_id = int(payload["id"])
        if device_id not in (1, 2, 3):
            raise ValueError("id must be 1, 2, or 3")
        temp = float(payload.get("temp", 0))
        spo2 = float(payload.get("spo2", 0))
        heart_rate = float(payload.get("heart_rate", 0))
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": f"Invalid reading: {exc}"}), 400

    timestamp = datetime.now(timezone.utc).isoformat()
    reading = {
        "device_id": device_id,
        "temp": temp,
        "spo2": spo2,
        "heart_rate": heart_rate,
        "updated_at": timestamp,
    }
    device_data[device_id] = reading
    with connect_db() as con:
        con.execute(
            "INSERT INTO readings (device_id, temp, spo2, heart_rate, ts) VALUES (?, ?, ?, ?, ?)",
            (device_id, temp, spo2, heart_rate, timestamp),
        )
    return jsonify({"status": "received", "device_id": device_id}), 200

@app.get("/get_data")
def get_data():
    # JSON object keys are strings; the dashboard uses device IDs 1, 2, and 3.
    return jsonify({str(device_id): reading for device_id, reading in device_data.items()})

@app.get("/history")
def history():
    with connect_db() as con:
        rows = con.execute(
            "SELECT device_id, temp, spo2, heart_rate, ts FROM readings ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(row) for row in rows])

if __name__ == "__main__":
    init_db()
    print("ESP32 Health Monitor server starting.")
    print("Open http://127.0.0.1:5000 on this computer.")
    print("For ESP32 devices, use this computer's local Wi-Fi IP address.")
    app.run(host="0.0.0.0", port=5000, debug=False)

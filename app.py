from flask import Flask, request, jsonify, render_template_string
import requests
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os

app = Flask(__name__)

# ============= CONFIG =============
BOT_NAME = "@BRONX_ULTRA"
THREADS = 50
TIMEOUT = 15
running = False
view_log = []
total_sent = 0
current_proxies = []

# ============= HTML TEMPLATE =============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BRONX ULTRA - Telegram Views</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0a;
            color: #fff;
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            width: 100%;
            background: #111;
            border-radius: 20px;
            border: 1px solid #222;
            padding: 30px;
        }
        .header {
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #222;
        }
        .header h1 {
            font-size: 32px;
            background: linear-gradient(90deg, #bf00ff, #00c8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header .badge {
            color: #888;
            font-size: 14px;
        }
        .section {
            margin: 20px 0;
            padding: 15px;
            background: #1a1a1a;
            border-radius: 12px;
            border: 1px solid #222;
        }
        .section-title {
            color: #bf00ff;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .input-group {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .input-group input, .input-group textarea, .input-group button {
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid #333;
            background: #0a0a0a;
            color: #fff;
            font-size: 14px;
            font-family: inherit;
        }
        .input-group input, .input-group textarea {
            flex: 1;
            min-width: 200px;
        }
        .input-group textarea {
            min-height: 120px;
            resize: vertical;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .input-group input:focus, .input-group textarea:focus {
            border-color: #bf00ff;
            outline: none;
        }
        .input-group button {
            background: linear-gradient(90deg, #bf00ff, #6a00ff);
            border: none;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            min-width: 100px;
        }
        .input-group button:hover {
            transform: scale(1.05);
        }
        .input-group button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .btn-danger { background: #ff0044 !important; }
        .btn-success { background: #00cc66 !important; }
        .btn-warning { background: #ff8800 !important; }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 18px;
            background: #0a0a0a;
            border-radius: 10px;
            margin: 10px 0;
            flex-wrap: wrap;
            gap: 10px;
            border: 1px solid #222;
        }
        .status-bar .status-text { font-size: 15px; }
        .status-bar .status-text .dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .dot.green { background: #00cc66; box-shadow: 0 0 10px #00cc66; }
        .dot.red { background: #ff0044; box-shadow: 0 0 10px #ff0044; }
        .dot.yellow { background: #ffcc00; box-shadow: 0 0 10px #ffcc00; }
        .dot.gray { background: #555; }
        
        .progress-container {
            width: 100%;
            background: #222;
            border-radius: 10px;
            height: 24px;
            margin: 10px 0;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #bf00ff, #00c8ff);
            width: 0%;
            transition: width 0.5s;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin: 10px 0;
        }
        .stats .stat-box {
            background: #0a0a0a;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #222;
        }
        .stats .stat-box .num {
            font-size: 22px;
            font-weight: bold;
            background: linear-gradient(90deg, #bf00ff, #00c8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stats .stat-box .label { color: #666; font-size: 11px; margin-top: 4px; }
        
        .log-container {
            background: #0a0a0a;
            border-radius: 10px;
            padding: 12px;
            height: 250px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            border: 1px solid #222;
            margin-top: 10px;
        }
        .log-container::-webkit-scrollbar { width: 4px; }
        .log-container::-webkit-scrollbar-thumb { background: #bf00ff; border-radius: 10px; }
        .log-entry { padding: 2px 0; border-bottom: 1px solid #111; }
        .log-entry .time { color: #666; margin-right: 10px; }
        .log-entry.success { color: #00cc66; }
        .log-entry.failed { color: #ff0044; }
        .log-entry.info { color: #00c8ff; }
        .log-entry.warning { color: #ff8800; }
        
        .footer {
            text-align: center;
            padding-top: 20px;
            color: #444;
            font-size: 12px;
            border-top: 1px solid #222;
            margin-top: 20px;
        }
        .footer span { color: #bf00ff; }
        .proxy-count { color: #888; font-size: 12px; }
        .example-proxies {
            color: #666;
            font-size: 11px;
            margin-top: 5px;
            font-family: 'Courier New', monospace;
        }
        @media (max-width: 600px) {
            .container { padding: 15px; }
            .input-group { flex-direction: column; }
            .input-group input, .input-group textarea { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 BRONX ULTRA VIEWS</h1>
            <span class="badge">⚡ {{ bot_name }}</span>
        </div>

        <!-- Proxy Input Section -->
        <div class="section">
            <div class="section-title">🌐 Enter Proxies (One per line)</div>
            <div class="input-group">
                <textarea id="proxyInput" placeholder="IP:PORT&#10;Example:&#10;103.21.244.100:80&#10;45.12.30.71:8080&#10;173.245.49.35:3128">103.21.244.100:80
45.12.30.71:8080
173.245.49.35:3128
188.114.96.24:80
141.101.120.98:80
103.137.35.2:80</textarea>
            </div>
            <button onclick="loadProxies()" class="btn-success">📥 Load Proxies</button>
            <span class="proxy-count" id="proxyCountDisplay">Loaded: 0 proxies</span>
            <div class="example-proxies">💡 Format: IP:PORT (e.g., 103.21.244.100:80)</div>
        </div>

        <!-- Link & Count Section -->
        <div class="section">
            <div class="section-title">📤 Telegram Post Link</div>
            <div class="input-group">
                <input type="text" id="linkInput" placeholder="https://t.me/username/123" value="https://t.me/ymmgmhyu/20">
                <input type="number" id="countInput" placeholder="Count" value="50" min="1" max="500" style="max-width:120px;">
                <button id="startBtn" onclick="startTask()">▶️ Start</button>
                <button id="stopBtn" onclick="stopTask()" class="btn-danger" disabled>⏹️ Stop</button>
            </div>
        </div>

        <!-- Status -->
        <div class="status-bar">
            <div class="status-text">
                <span class="dot gray" id="statusDot"></span>
                <span id="statusMessage">⏳ Load proxies first</span>
            </div>
            <span id="proxyInfo">🌐 Proxies: 0</span>
        </div>

        <div class="progress-container">
            <div class="progress-bar" id="progressBar">0%</div>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="num" id="sentCount">0</div>
                <div class="label">📤 Views Sent</div>
            </div>
            <div class="stat-box">
                <div class="num" id="successRate">0%</div>
                <div class="label">📊 Success Rate</div>
            </div>
            <div class="stat-box">
                <div class="num" id="totalProxies">0</div>
                <div class="label">🌐 Proxies Loaded</div>
            </div>
            <div class="stat-box">
                <div class="num" id="failedCount">0</div>
                <div class="label">❌ Failed</div>
            </div>
        </div>

        <div class="log-container" id="logContainer">
            <div class="log-entry info"><span class="time">[INIT]</span> 🔄 Enter proxies and click Load Proxies</div>
        </div>

        <div class="footer">⚡ {{ bot_name }} • Advanced Telegram Views • Proxy Input</div>
    </div>

    <script>
        let isRunning = false;
        let loadedProxies = [];

        // ============= FUNCTIONS =============
        function addLog(message, type = 'info') {
            const log = document.getElementById('logContainer');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.innerHTML = `<span class="time">[${time}]</span> ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }

        function updateStatus(message, color) {
            document.getElementById('statusMessage').textContent = message;
            document.getElementById('statusDot').className = `dot ${color}`;
        }

        function updateProgress(percent, text) {
            const bar = document.getElementById('progressBar');
            bar.style.width = percent + '%';
            bar.textContent = text || percent + '%';
        }

        function loadProxies() {
            const text = document.getElementById('proxyInput').value;
            const lines = text.split('\\n').map(s => s.trim()).filter(s => s && s.includes(':'));
            
            if (lines.length === 0) {
                addLog('❌ No valid proxies found! Use format: IP:PORT', 'failed');
                return;
            }
            
            loadedProxies = lines;
            document.getElementById('totalProxies').textContent = loadedProxies.length;
            document.getElementById('proxyCountDisplay').textContent = `Loaded: ${loadedProxies.length} proxies`;
            document.getElementById('proxyInfo').textContent = `🌐 Proxies: ${loadedProxies.length}`;
            addLog(`✅ Loaded ${loadedProxies.length} proxies`, 'success');
            updateStatus('✅ Proxies loaded', 'green');
            
            // Send to server
            fetch('/api/load-proxies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ proxies: loadedProxies })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    addLog(`✅ ${data.count} proxies sent to server`, 'success');
                }
            })
            .catch(err => addLog(`❌ Error: ${err}`, 'failed'));
        }

        function startTask() {
            const link = document.getElementById('linkInput').value.trim();
            const count = parseInt(document.getElementById('countInput').value) || 50;

            if (!link) {
                addLog('❌ Please enter a Telegram post link', 'failed');
                return;
            }

            if (loadedProxies.length === 0) {
                addLog('❌ Please load proxies first!', 'failed');
                return;
            }

            addLog(`📤 Starting: ${link} (${count} views)`, 'info');
            updateStatus('🔄 Running...', 'yellow');
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            isRunning = true;
            updateProgress(0, 'Starting...');
            
            fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ link, count })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    addLog('✅ Task started successfully', 'success');
                } else {
                    addLog(`❌ ${data.message}`, 'failed');
                    resetUI();
                }
            })
            .catch(err => {
                addLog(`❌ Error: ${err}`, 'failed');
                resetUI();
            });
        }

        function stopTask() {
            addLog('⏹️ Stopping task...', 'warning');
            fetch('/api/stop', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                addLog('⏹️ Stop command sent', 'info');
                resetUI();
            })
            .catch(err => addLog(`❌ Error: ${err}`, 'failed'));
        }

        function resetUI() {
            isRunning = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            updateStatus('✅ Ready', 'green');
        }

        // ============= POLLING FOR STATUS =============
        function fetchStatus() {
            fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                document.getElementById('sentCount').textContent = data.sent || 0;
                document.getElementById('failedCount').textContent = data.failed || 0;
                document.getElementById('totalProxies').textContent = data.total_proxies || loadedProxies.length;
                
                if (data.running) {
                    updateStatus('🔄 Running...', 'yellow');
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    isRunning = true;
                } else if (data.completed) {
                    const rate = data.sent > 0 ? Math.round((data.sent / (data.sent + data.failed)) * 100) : 0;
                    document.getElementById('successRate').textContent = rate + '%';
                    if (data.sent > 0) {
                        updateStatus(`✅ Completed: ${data.sent} views sent`, 'green');
                    } else {
                        updateStatus('⚠️ Completed: 0 views sent', 'yellow');
                    }
                    resetUI();
                }
                
                if (data.progress !== undefined) {
                    updateProgress(data.progress, `${data.progress}% (${data.sent || 0} sent)`);
                }
            })
            .catch(() => {});
        }

        // Fetch logs
        function fetchLogs() {
            fetch('/api/logs')
            .then(res => res.json())
            .then(data => {
                if (data.logs && data.logs.length > 0) {
                    // Only add new logs
                    const container = document.getElementById('logContainer');
                    const currentCount = container.children.length;
                    if (data.logs.length > currentCount - 1) {
                        // Clear and reload
                        container.innerHTML = '';
                        data.logs.forEach(log => {
                            const type = log.includes('✅') ? 'success' : 
                                       log.includes('❌') ? 'failed' : 
                                       log.includes('⚠️') ? 'warning' : 'info';
                            const time = new Date().toLocaleTimeString();
                            const entry = document.createElement('div');
                            entry.className = `log-entry ${type}`;
                            entry.innerHTML = `<span class="time">[${time}]</span> ${log}`;
                            container.appendChild(entry);
                        });
                        container.scrollTop = container.scrollHeight;
                    }
                }
            })
            .catch(() => {});
        }

        // Poll every 1.5 seconds
        setInterval(fetchStatus, 1500);
        setInterval(fetchLogs, 3000);

        // Initial load
        setTimeout(() => {
            loadProxies();
        }, 500);
    </script>
</body>
</html>
"""

# ============= PROXY STORAGE =============
user_proxies = []
running = False
view_log = []
total_sent = 0
total_failed = 0
task_completed = False
progress = 0

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, channel, post_id):
    """Send 1 view using exact proxy:port"""
    try:
        session = requests.Session()
        
        # ✅ Use exact proxy as provided
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        user_agent = random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/119.0.0.0',
        ])
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'close'
        }
        
        # Step 1: Get post page
        url = f"https://t.me/{channel}/{post_id}"
        response = session.get(
            f"{url}?embed=1&mode=tme",
            headers=headers,
            proxies=proxies,
            timeout=15,
            verify=False,
            allow_redirects=True
        )
        
        if response.status_code != 200:
            return False, f"Status: {response.status_code}"
        
        # Step 2: Extract view token
        view_match = re.search(r'data-view="([^"]+)"', response.text)
        if not view_match:
            return False, "No token"
        
        view_token = view_match.group(1)
        cookies = session.cookies.get_dict()
        
        # Step 3: Send view
        view_response = session.get(
            'https://t.me/v/',
            params={'views': view_token},
            cookies={
                'stel_dt': '-240',
                'stel_ssid': cookies.get('stel_ssid', ''),
                'stel_on': cookies.get('stel_on', '')
            },
            headers={
                'Referer': f'https://t.me/{channel}/{post_id}?embed=1&mode=tme',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': user_agent
            },
            proxies=proxies,
            timeout=15,
            verify=False
        )
        
        if view_response.status_code == 200:
            return True, "Success"
        else:
            return False, f"View status: {view_response.status_code}"
        
    except Exception as e:
        return False, str(e)[:40]

def send_views_task(channel, post_id, count):
    """Main task to send views"""
    global running, total_sent, total_failed, view_log, progress, task_completed
    
    running = True
    total_sent = 0
    total_failed = 0
    view_log = []
    progress = 0
    task_completed = False
    
    view_log.append(f"🚀 Started: {count} views to {channel}/{post_id}")
    
    proxies_to_use = user_proxies[:count]
    if not proxies_to_use:
        view_log.append("❌ No proxies available!")
        running = False
        task_completed = True
        return
    
    view_log.append(f"📡 Using {len(proxies_to_use)} proxies")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {
            executor.submit(send_telegram_view, proxy, channel, post_id): proxy
            for proxy in proxies_to_use
        }
        
        completed = 0
        for future in as_completed(futures):
            if not running:
                view_log.append("⏹️ Stopped by user")
                break
            
            proxy = futures[future]
            try:
                success, message = future.result(timeout=20)
                completed += 1
                if success:
                    total_sent += 1
                    view_log.append(f"✅ {proxy} - Success")
                else:
                    total_failed += 1
                    view_log.append(f"❌ {proxy} - {message}")
                
                progress = int((completed / len(proxies_to_use)) * 100)
                
            except Exception as e:
                total_failed += 1
                view_log.append(f"❌ {proxy} - Error")
    
    running = False
    task_completed = True
    view_log.append(f"✅ Completed! Sent {total_sent} views, Failed {total_failed}")

# ============= FLASK ROUTES =============

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, bot_name=BOT_NAME)

@app.route('/api/load-proxies', methods=['POST'])
def load_proxies():
    global user_proxies
    data = request.get_json()
    proxies = data.get('proxies', [])
    user_proxies = list(set([p.strip() for p in proxies if p.strip() and ':' in p]))
    return jsonify({'status': 'success', 'count': len(user_proxies)})

@app.route('/api/start', methods=['POST'])
def start_task():
    global running, user_proxies
    
    if running:
        return jsonify({'status': 'error', 'message': 'Task already running'})
    
    if not user_proxies:
        return jsonify({'status': 'error', 'message': 'No proxies loaded. Add proxies first!'})
    
    data = request.get_json()
    link = data.get('link', '').strip()
    count = int(data.get('count', 50))
    
    if not link:
        return jsonify({'status': 'error', 'message': 'Link required'})
    
    match = re.search(r't\.me/([^/]+)/(\d+)', link)
    if not match:
        return jsonify({'status': 'error', 'message': 'Invalid link format'})
    
    channel, post_id = match.groups()
    
    if count < 1:
        count = 1
    if count > len(user_proxies):
        count = len(user_proxies)
    
    thread = threading.Thread(target=send_views_task, args=(channel, post_id, count))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'success', 'message': 'Task started'})

@app.route('/api/stop', methods=['POST'])
def stop_task():
    global running
    running = False
    return jsonify({'status': 'success', 'message': 'Stopping...'})

@app.route('/api/status', methods=['GET'])
def get_status():
    global running, total_sent, total_failed, progress, task_completed, user_proxies
    return jsonify({
        'running': running,
        'completed': task_completed,
        'sent': total_sent,
        'failed': total_failed,
        'total_proxies': len(user_proxies),
        'progress': progress
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    global view_log
    return jsonify({'logs': view_log[-100:]})

if __name__ == '__main__':
    print("=" * 60)
    print("🔥 BRONX ULTRA Views API - Proxy Input")
    print(f"🤖 Developer: {BOT_NAME}")
    print("=" * 60)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

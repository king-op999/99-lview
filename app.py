from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import requests
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bronx-ultra-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============= CONFIG =============
BOT_NAME = "@BRONX_ULTRA"
THREADS = 50
TIMEOUT = 15
MAX_VIEWS = 500
running = False
current_task = None
view_log = []
total_sent = 0

# ============= PROXY SOURCES =============
SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
    "https://proxyspace.pro/http.txt",
    "https://proxyspace.pro/https.txt",
    "https://openproxylist.xyz/http.txt",
]

IP_REGEX = re.compile(r'(?:^|\D)?((?:(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])):(?:(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])))(?:\D|$)')

proxies_list = []

def scrap_proxies():
    """Scrape proxies from all sources"""
    global proxies_list
    new_proxies = []
    for url in SOURCES:
        try:
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                matches = IP_REGEX.findall(response.text)
                for match in matches:
                    proxy = match[0] if isinstance(match, tuple) else match
                    if proxy and '303.303.303' not in proxy and '0.0.0.0' not in proxy:
                        new_proxies.append(proxy)
        except:
            pass
    proxies_list = list(set(new_proxies))
    socketio.emit('log', {'message': f'✅ Loaded {len(proxies_list)} proxies'})
    return proxies_list

def get_proxies(limit=100):
    """Get proxies from list"""
    global proxies_list
    if not proxies_list:
        scrap_proxies()
    random.shuffle(proxies_list)
    return proxies_list[:limit]

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, channel, post_id):
    """Send 1 view"""
    try:
        session = requests.Session()
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
            timeout=TIMEOUT,
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
            timeout=TIMEOUT,
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
    global running, total_sent, view_log
    
    running = True
    total_sent = 0
    view_log = []
    
    socketio.emit('status', {'status': 'running', 'message': '🔄 Starting...'})
    
    # Scrape proxies
    proxies = get_proxies(count * 2)
    if not proxies:
        socketio.emit('log', {'message': '❌ No proxies available!'})
        running = False
        return
    
    proxies_to_use = proxies[:count]
    socketio.emit('log', {'message': f'📡 Using {len(proxies_to_use)} proxies'})
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {
            executor.submit(send_telegram_view, proxy, channel, post_id): proxy
            for proxy in proxies_to_use
        }
        
        completed = 0
        for future in as_completed(futures):
            if not running:
                socketio.emit('log', {'message': '⏹️ Stopped by user'})
                break
            
            proxy = futures[future]
            try:
                success, message = future.result(timeout=TIMEOUT + 5)
                completed += 1
                if success:
                    total_sent += 1
                    view_log.append(f"✅ {proxy} - Success")
                    socketio.emit('view', {'proxy': proxy, 'status': 'success', 'total': total_sent})
                else:
                    view_log.append(f"❌ {proxy} - {message}")
                    socketio.emit('view', {'proxy': proxy, 'status': 'failed'})
                
                # Update progress
                progress = int((completed / len(proxies_to_use)) * 100)
                socketio.emit('progress', {'progress': progress, 'sent': total_sent, 'total': len(proxies_to_use)})
                
            except Exception as e:
                view_log.append(f"❌ {proxy} - Error")
    
    running = False
    socketio.emit('status', {'status': 'completed', 'message': f'✅ Completed! Sent {total_sent} views'})
    socketio.emit('log', {'message': f'✅ Task completed! Sent {total_sent} views'})

# ============= FLASK ROUTES =============

@app.route('/')
def index():
    """Web interface"""
    return render_template('index.html', bot_name=BOT_NAME)

@app.route('/api/start', methods=['POST'])
def start_task():
    """Start views task"""
    global current_task, running
    
    if running:
        return jsonify({'status': 'error', 'message': 'Task already running'})
    
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
    if count > MAX_VIEWS:
        count = MAX_VIEWS
    
    # Start in background
    thread = threading.Thread(target=send_views_task, args=(channel, post_id, count))
    thread.daemon = True
    thread.start()
    current_task = thread
    
    return jsonify({'status': 'success', 'message': 'Task started'})

@app.route('/api/stop', methods=['POST'])
def stop_task():
    """Stop running task"""
    global running
    running = False
    return jsonify({'status': 'success', 'message': 'Stopping...'})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current status"""
    global running, total_sent
    return jsonify({
        'running': running,
        'sent': total_sent,
        'proxies': len(proxies_list)
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent logs"""
    global view_log
    return jsonify({'logs': view_log[-50:]})

@socketio.on('connect')
def handle_connect():
    emit('log', {'message': '🟢 Connected to server'})
    emit('status', {'status': 'ready', 'message': '✅ Ready'})

@socketio.on('disconnect')
def handle_disconnect():
    pass

if __name__ == '__main__':
    # Initial proxy load
    print("=" * 60)
    print("🔥 BRONX ULTRA Views API + Web Interface")
    print(f"🤖 Developer: {BOT_NAME}")
    print("=" * 60)
    
    # Load proxies in background
    threading.Thread(target=scrap_proxies, daemon=True).start()
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)

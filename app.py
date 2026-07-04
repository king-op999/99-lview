# app.py - BRONX ULTRA Views API (Updated Sources)
from flask import Flask, request, jsonify
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
RETRY_COUNT = 1

# ✅ UPDATED HTTP SOURCES (SOCKS HATAYE)
HTTP_SOURCES = [
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

# Regex to match IP:PORT
IP_REGEX = re.compile(r'(?:^|\D)?((?:(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])):(?:(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])))(?:\D|$)')

# Store proxies
proxies_list = []
proxy_lock = threading.Lock()
last_update = 0
UPDATE_INTERVAL = 600

# ============= PROXY SCRAPER =============

def scrap_proxies():
    """Scrape HTTP proxies only"""
    new_proxies = []
    for url in HTTP_SOURCES:
        try:
            response = requests.get(url, timeout=20, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                matches = IP_REGEX.findall(response.text)
                for match in matches:
                    proxy = match[0] if isinstance(match, tuple) else match
                    if proxy and '303.303.303' not in proxy:
                        new_proxies.append(proxy)
        except Exception as e:
            pass
    
    return list(set(new_proxies))

def update_proxies():
    """Update proxy list"""
    global proxies_list, last_update
    
    print("[PROXY] Starting HTTP proxy update...")
    result = scrap_proxies()
    
    with proxy_lock:
        proxies_list = result
    
    last_update = time.time()
    print(f"[PROXY] Loaded {len(proxies_list)} HTTP proxies")

def get_proxies(limit=100):
    """Get proxies from list"""
    current_time = time.time()
    if current_time - last_update > UPDATE_INTERVAL or not proxies_list:
        threading.Thread(target=update_proxies, daemon=True).start()
        with proxy_lock:
            proxies = proxies_list.copy()
    else:
        with proxy_lock:
            proxies = proxies_list.copy()
    
    random.shuffle(proxies)
    return proxies[:limit]

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, channel, post_id):
    """Send 1 view using 1 proxy"""
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
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
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

def send_views_batch(channel, post_id, count=50):
    """Send 1 view per proxy"""
    results = {"success": 0, "failed": 0, "errors": [], "proxies_used": []}
    
    proxies = get_proxies(count * 2)
    if not proxies:
        return results
    
    proxies_to_use = proxies[:count]
    
    print(f"[VIEWS] Sending {len(proxies_to_use)} unique views...")
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {
            executor.submit(send_telegram_view, proxy, channel, post_id): proxy
            for proxy in proxies_to_use
        }
        
        for future in as_completed(futures):
            proxy = futures[future]
            try:
                success, message = future.result(timeout=TIMEOUT + 5)
                if success:
                    results["success"] += 1
                    results["proxies_used"].append(proxy)
                else:
                    results["failed"] += 1
                    if len(results["errors"]) < 8:
                        results["errors"].append(f"{proxy}: {message}")
            except Exception as e:
                results["failed"] += 1
    
    return results

# ============= FLASK ROUTES =============

@app.route('/')
def home():
    return jsonify({
        "status": "✅ ONLINE",
        "service": "BRONX ULTRA Views API",
        "developer": BOT_NAME,
        "credit": "BRONX ULTRA",
        "total_proxies": len(proxies_list),
        "note": "✅ HTTP only - Updated sources",
        "endpoints": {
            "/api/views": "GET/POST - Send views",
            "/api/proxies": "GET - Get proxy list",
            "/api/stats": "GET - Statistics"
        },
        "example": "/api/views?link=https://t.me/channel/10&count=50"
    })

@app.route('/api/views', methods=['POST', 'GET'])
def api_views():
    """Main API endpoint"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            link = data.get('link', '')
            count = data.get('count', 50)
        else:
            link = request.args.get('link', '')
            count = int(request.args.get('count', 50))
        
        if not link:
            return jsonify({"status": "error", "message": "Post link required", "developer": BOT_NAME}), 400
        
        match = re.search(r't\.me/([^/]+)/(\d+)', link)
        if not match:
            return jsonify({"status": "error", "message": "Invalid link", "developer": BOT_NAME}), 400
        
        channel, post_id = match.groups()
        
        try:
            count = int(count)
            if count < 1: count = 1
            if count > 100: count = 100
        except:
            count = 50
        
        start_time = time.time()
        result = send_views_batch(channel, post_id, count)
        elapsed = round((time.time() - start_time) * 1000, 2)
        
        total = result["success"] + result["failed"]
        success_rate = round((result["success"] / total * 100), 2) if total > 0 else 0
        
        return jsonify({
            "status": "success",
            "developer": BOT_NAME,
            "credit": "BRONX ULTRA",
            "link": link,
            "channel": channel,
            "post_id": post_id,
            "requested": count,
            "success": result["success"],
            "failed": result["failed"],
            "success_rate": f"{success_rate}%",
            "proxies_used": len(result["proxies_used"]),
            "total_proxies": len(proxies_list),
            "errors": result["errors"][:5],
            "execution_time_ms": elapsed,
            "message": f"✅ {result['success']} unique views sent!"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "developer": BOT_NAME}), 500

@app.route('/api/proxies', methods=['GET'])
def api_proxies():
    """Get proxy list"""
    limit = int(request.args.get('limit', 20))
    proxies = get_proxies(limit)
    
    return jsonify({
        "status": "success",
        "developer": BOT_NAME,
        "total_proxies": len(proxies_list),
        "proxies": proxies
    })

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Statistics"""
    return jsonify({
        "status": "success",
        "developer": BOT_NAME,
        "stats": {
            "total_proxies": len(proxies_list),
            "threads": THREADS,
            "timeout": TIMEOUT,
            "last_update": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_update))
        }
    })

if __name__ == '__main__':
    print("=" * 50)
    print(f"🔥 BRONX ULTRA Views API")
    print(f"✅ Updated HTTP Sources")
    print("=" * 50)
    
    threading.Thread(target=update_proxies, daemon=True).start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

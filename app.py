# app.py - BRONX ULTRA Telegram Views API (Fixed)
from flask import Flask, request, jsonify
import requests
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

app = Flask(__name__)

# ============= CONFIG =============
BOT_NAME = "@BRONX_ULTRA"
THREADS = 50  # ✅ Reduced for better success
TIMEOUT = 10
RETRY_COUNT = 2

# ✅ SIRF AAPKI HTTP PROXIES (Yahi use hongi, kuch aur nahi)
WORKING_PROXIES = [
    "84.17.47.150:9002", "84.17.47.149:9002", "84.17.47.148:9002",
    "84.17.47.147:9002", "84.17.47.146:9002", "84.17.47.126:9002",
    "84.17.47.125:9002", "84.17.47.124:9002", "129.151.160.199:443",
    "74.103.66.15:443", "51.38.191.151:443", "128.199.207.200:443",
    "45.114.142.178:443", "138.199.35.215:9002", "138.199.35.214:9002",
    "138.199.35.213:9002", "138.199.35.212:9002", "138.199.35.208:9002",
    "138.199.35.205:9002", "138.199.35.204:9002", "138.199.35.203:9002",
    "138.199.35.201:9002", "138.199.35.200:9002", "138.199.35.198:9002",
    "138.199.35.197:9002", "138.199.35.195:9002", "138.199.35.199:9002",
    "138.199.35.217:9002", "156.146.59.28:9002", "156.146.59.29:9002",
    "156.146.59.50:9002", "84.239.49.164:9002", "156.146.59.8:9002",
    "156.146.59.13:9002", "156.146.59.2:9002", "156.146.59.3:9002",
    "156.146.59.4:9002", "156.146.59.5:9002", "156.146.59.6:9002",
    "156.146.59.7:9002", "156.146.59.9:9002", "156.146.59.10:9002",
    "84.239.49.37:9002", "84.239.49.38:9002", "84.239.49.39:9002",
    "156.146.59.11:9002", "84.239.49.40:9002", "84.239.49.41:9002",
    "84.239.49.43:9002", "84.239.49.44:9002", "84.239.49.45:9002",
    "84.239.49.46:9002", "84.239.49.47:9002", "84.239.49.48:9002",
    "84.239.49.49:9002", "84.239.49.50:9002", "156.146.59.12:9002",
    "84.239.49.51:9002", "156.146.59.14:9002", "156.146.59.15:9002",
    "156.146.59.16:9002", "156.146.59.17:9002", "156.146.59.18:9002",
    "156.146.59.19:9002", "156.146.59.20:9002", "84.239.49.157:9002",
    "84.239.49.161:9002", "84.239.49.169:9002", "84.239.49.200:9002",
    "84.239.49.204:9002", "84.239.49.209:9002", "84.239.49.218:9002",
    "84.239.49.220:9002", "84.239.49.229:9002", "84.239.49.231:9002",
    "84.239.49.244:9002", "84.239.49.246:9002", "84.239.49.247:9002",
    "84.239.49.248:9002", "84.239.49.249:9002", "84.239.49.250:9002",
    "84.239.49.251:9002", "84.239.49.253:9002", "84.239.49.254:9002",
    "84.239.14.160:9002", "84.239.14.146:9002", "84.239.14.147:9002",
    "84.239.14.148:9002", "84.239.14.149:9002", "84.239.14.150:9002",
    "84.239.14.151:9002", "84.239.14.152:9002", "84.239.14.153:9002",
    "84.239.14.154:9002", "84.239.14.155:9002", "84.239.14.156:9002",
    "84.239.14.157:9002", "84.239.14.158:9002", "84.239.14.159:9002",
    "51.79.173.71:443"
]

# ✅ Remove duplicates and invalid
WORKING_PROXIES = list(set([p for p in WORKING_PROXIES if p and ':' in p]))
print(f"[PROXY] Loaded {len(WORKING_PROXIES)} HTTP proxies")

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, channel, post_id, retry=0):
    """Send view using HTTP proxy with retry"""
    try:
        session = requests.Session()
        
        # ✅ HTTP proxy only
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/119.0.0.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'close'
        }
        
        # ✅ Step 1: Get post page
        url = f"https://t.me/{channel}/{post_id}"
        response = session.get(
            f"{url}?embed=1&mode=tme",
            headers=headers,
            proxies=proxies,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            if retry < RETRY_COUNT:
                time.sleep(0.5)
                return send_telegram_view(proxy, channel, post_id, retry + 1)
            return False, f"Status: {response.status_code}"
        
        # ✅ Step 2: Extract view token
        view_match = re.search(r'data-view="([^"]+)"', response.text)
        if not view_match:
            return False, "No token"
        
        view_token = view_match.group(1)
        cookies = session.cookies.get_dict()
        
        # ✅ Step 3: Send view
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
                'User-Agent': headers['User-Agent']
            },
            proxies=proxies,
            timeout=TIMEOUT
        )
        
        if view_response.status_code == 200:
            return True, "Success"
        else:
            if retry < RETRY_COUNT:
                time.sleep(0.5)
                return send_telegram_view(proxy, channel, post_id, retry + 1)
            return False, f"View status: {view_response.status_code}"
        
    except Exception as e:
        if retry < RETRY_COUNT:
            time.sleep(0.5)
            return send_telegram_view(proxy, channel, post_id, retry + 1)
        return False, str(e)[:40]

def send_views_batch(channel, post_id, count=100):
    """Send views using proxies"""
    results = {"success": 0, "failed": 0, "errors": [], "proxies_used": []}
    
    # ✅ Use only working proxies
    proxies_to_use = WORKING_PROXIES.copy()
    random.shuffle(proxies_to_use)
    proxies_to_use = proxies_to_use[:count]
    
    print(f"[VIEWS] Sending {len(proxies_to_use)} views...")
    
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
        "service": "BRONX ULTRA Telegram Views API",
        "developer": BOT_NAME,
        "credit": "BRONX ULTRA",
        "proxies_loaded": len(WORKING_PROXIES),
        "note": "✅ HTTP proxies only - No scraping",
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
            count = data.get('count', 100)
        else:
            link = request.args.get('link', '')
            count = int(request.args.get('count', 100))
        
        if not link:
            return jsonify({"status": "error", "message": "Post link required", "developer": BOT_NAME}), 400
        
        match = re.search(r't\.me/([^/]+)/(\d+)', link)
        if not match:
            return jsonify({"status": "error", "message": "Invalid link", "developer": BOT_NAME}), 400
        
        channel, post_id = match.groups()
        
        try:
            count = int(count)
            if count < 1: count = 1
            if count > 300: count = 300
        except:
            count = 100
        
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
            "total_proxies": len(WORKING_PROXIES),
            "errors": result["errors"][:5],
            "execution_time_ms": elapsed,
            "message": f"✅ {result['success']} views! (Rate: {success_rate}%)"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "developer": BOT_NAME}), 500

@app.route('/api/proxies', methods=['GET'])
def api_proxies():
    """Get working proxies"""
    limit = int(request.args.get('limit', 20))
    proxies = WORKING_PROXIES[:limit]
    
    return jsonify({
        "status": "success",
        "developer": BOT_NAME,
        "total_proxies": len(WORKING_PROXIES),
        "proxies": proxies
    })

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Statistics"""
    return jsonify({
        "status": "success",
        "developer": BOT_NAME,
        "stats": {
            "total_proxies": len(WORKING_PROXIES),
            "threads": THREADS,
            "timeout": TIMEOUT,
            "retry_count": RETRY_COUNT
        }
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🔥 BRONX ULTRA Views API")
    print(f"✅ {len(WORKING_PROXIES)} HTTP Proxies Loaded")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)

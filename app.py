# app.py - BRONX ULTRA Views API (100+ Working Proxies)
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

# ✅ YOUR 100% WORKING PROXIES (Different Countries)
WORKING_PROXIES = [
    "49.51.228.35:81", "45.89.106.12:80", "198.199.86.11:80",
    "18.163.33.4:8282", "13.208.166.217:4956", "209.97.150.167:8080",
    "159.203.61.169:80", "43.203.140.58:23103", "202.28.194.139:31280",
    "51.178.253.98:80", "95.3.69.222:8080", "13.41.196.179:22109",
    "13.51.196.44:15624", "18.60.247.31:43386", "43.200.174.95:8003",
    "3.127.27.51:15795", "80.151.57.81:8080", "159.203.61.169:3128",
    "128.199.202.122:80", "91.107.182.124:82", "18.246.32.243:14106",
    "138.68.60.8:8080", "18.246.32.243:40050", "63.181.83.210:47777",
    "138.68.60.8:3128", "134.209.29.120:3128", "18.162.200.96:15818",
    "43.203.140.58:33007", "81.168.119.85:443", "91.107.182.124:84",
    "16.28.29.244:40287", "139.162.78.109:3128", "134.209.29.120:8080",
    "51.92.173.133:15915", "35.180.75.159:53532", "113.160.132.26:8080",
    "13.245.171.157:55652", "159.203.61.169:8080", "176.111.37.5:39811",
    "139.59.1.14:80", "159.195.49.27:8888", "43.167.245.99:3128",
    "34.43.46.91:80", "159.195.69.220:8888", "134.209.29.120:80",
    "128.199.202.122:3128", "16.26.99.200:29465", "198.199.86.11:3128",
    "56.68.116.64:8080", "51.17.154.141:12190", "52.74.26.202:8080",
    "194.233.86.196:443", "128.199.202.122:8080", "209.97.150.167:80",
    "77.110.113.236:8080", "176.111.37.216:39811", "161.35.70.249:80",
    "217.154.155.115:8080", "35.78.212.217:11703", "13.126.183.60:44018",
    "209.97.150.167:3128", "40.177.99.164:39907", "18.162.200.96:16239",
    "43.203.140.58:6060", "43.205.125.76:8081", "52.47.115.41:36630",
    "138.68.60.8:80", "54.79.125.20:59495"
]

# ✅ Remove duplicates
WORKING_PROXIES = list(set(WORKING_PROXIES))
print(f"[PROXY] Loaded {len(WORKING_PROXIES)} unique proxies")

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
    
    proxies_to_use = WORKING_PROXIES.copy()
    random.shuffle(proxies_to_use)
    proxies_to_use = proxies_to_use[:count]
    
    if not proxies_to_use:
        return results
    
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
        "total_proxies": len(WORKING_PROXIES),
        "note": "✅ 1 view per proxy = unique views",
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
            if count > len(WORKING_PROXIES): count = len(WORKING_PROXIES)
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
            "total_proxies": len(WORKING_PROXIES),
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
            "timeout": TIMEOUT
        }
    })

if __name__ == '__main__':
    print("=" * 50)
    print(f"🔥 BRONX ULTRA Views API")
    print(f"✅ {len(WORKING_PROXIES)} Proxies = Unique Views")
    print("=" * 50)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

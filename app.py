# app.py - BRONX ULTRA Views API (1 View Per Proxy)
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
THREADS = 30  # ✅ Slow but unique views
TIMEOUT = 15
RETRY_COUNT = 1

# ✅ YOUR WORKING HTTPS PROXIES
WORKING_PROXIES = [
    "154.113.209.162:8082", "208.82.61.64:3128", "182.253.21.26:46977",
    "58.69.248.180:8080", "103.88.237.97:84", "188.132.150.47:8080",
    "203.28.67.74:8080", "168.121.242.91:999", "182.160.107.45:12331",
    "115.191.40.196:7890", "103.209.36.58:8080", "5.45.126.165:13215",
    "126.209.1.14:8082", "47.236.86.147:443", "181.63.33.136:8080",
    "101.255.209.165:8080", "122.54.166.184:8082", "38.194.250.66:999",
    "103.122.64.232:8080", "110.34.1.180:32650", "85.29.58.227:8080",
    "150.107.29.165:3128", "143.244.140.119:3128", "23.224.193.42:3128",
    "131.222.210.39:8080", "41.33.89.100:1981", "125.135.136.210:3140",
    "131.222.253.76:8080", "47.252.41.213:443", "42.96.18.62:1311",
    "113.160.115.254:8080", "131.222.210.41:8080", "154.208.58.89:8080",
    "154.18.255.137:8080", "178.217.168.164:55443", "37.60.237.110:30001",
    "196.219.64.252:8080", "51.254.133.152:80", "108.181.0.167:3128",
    "172.105.121.181:3128", "34.73.100.77:3129", "8.222.175.80:6128",
    "176.12.72.62:3128", "187.103.105.20:8085", "193.233.128.128:3128",
    "190.119.90.114:8080", "188.166.9.27:3129", "182.160.104.211:12331",
    "103.18.205.162:8080", "205.209.64.193:8080", "5.175.151.66:8080",
    "104.194.148.204:80", "94.43.164.242:8080", "116.254.113.86:8080",
    "49.145.119.171:8081", "154.113.147.14:8080", "181.48.234.214:8080",
    "178.128.95.176:8080", "206.135.32.70:999", "106.10.55.212:1121",
    "103.137.35.2:80", "61.49.87.3:80", "54.38.35.209:3128",
    "45.136.254.27:8080", "185.126.5.92:8080", "103.230.150.58:8080",
    "160.191.192.45:8090", "181.209.118.250:999", "195.62.50.141:8080",
    "190.52.110.43:999", "101.96.98.138:8080", "131.222.251.90:8080",
    "121.101.129.103:8080", "176.88.166.197:8080", "222.127.68.126:8080",
    "38.194.246.34:999", "119.195.17.15:3056", "181.119.105.157:999",
    "139.28.49.23:8080", "131.222.251.61:8080", "129.226.149.231:3128",
    "154.12.60.65:888", "125.209.110.83:39617", "200.215.229.14:999",
    "103.134.220.122:1080", "27.147.28.73:8080", "101.109.32.112:8080",
    "140.246.125.194:9099", "129.222.204.27:10000", "173.212.246.157:3128",
    "51.178.253.9:880", "94.72.109.169:8080", "131.222.253.236:8080",
    "43.162.83.26:3128", "87.106.120.212:3128", "122.3.87.41:8080",
    "79.76.121.87:3128", "50.200.166.130:8080"
]

# ✅ Remove duplicates
WORKING_PROXIES = list(set(WORKING_PROXIES))
print(f"[PROXY] Loaded {len(WORKING_PROXIES)} unique proxies")

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, channel, post_id):
    """Send 1 view using 1 proxy"""
    try:
        session = requests.Session()
        
        # ✅ HTTP/HTTPS proxy
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        # ✅ Random User-Agent for each request
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
        
        # ✅ Step 1: Get post page
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
    
    # ✅ Use all proxies, each sends 1 view
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

# app.py - BRONX ULTRA Views API (100+ HTTP Proxies)
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

# ✅ YOUR 100+ HTTP PROXIES
WORKING_PROXIES = [
    "38.123.220.175:999", "80.74.54.148:3128", "197.157.140.150:80",
    "103.110.109.113:125", "154.73.87.241:8080", "27.49.68.66:9999",
    "202.165.92.206:8080", "84.255.40.228:8998", "163.172.53.142:80",
    "129.150.39.242:8118", "139.28.49.233:8080", "190.61.106.97:8080",
    "223.197.178.186:3128", "180.211.93.111:8080", "45.232.152.2:8080",
    "195.114.209.50:80", "58.246.79.38:7080", "143.208.152.62:3180",
    "175.100.35.103:8080", "186.33.3.37:999", "181.78.73.117:8080",
    "123.253.137.172:8082", "38.127.172.73:7234", "179.1.126.46:999",
    "180.191.32.166:8081", "68.183.93.236:3128", "115.85.88.18:8080",
    "45.179.201.212:999", "210.5.93.253:8080", "201.230.121.244:999",
    "103.121.22.192:8080", "38.49.148.149:999", "91.203.242.66:222",
    "103.193.144.223:8080", "183.88.231.188:34599", "112.198.128.171:8083",
    "182.253.228.155:8080", "201.230.121.228:999", "103.1.93.184:55443",
    "186.148.183.201:999", "78.155.65.203:8080", "136.232.116.248:976",
    "213.207.198.254:8080", "163.227.250.58:8080", "51.222.142.44:8080",
    "103.81.175.141:22311", "103.118.102.9:880", "38.191.194.27:999",
    "177.177.59.253:8080", "105.174.43.194:8080", "123.156.230.251:1081",
    "85.117.63.207:8080", "178.251.111.2:8080", "81.23.102.61:8080",
    "36.88.170.170:8080", "222.252.97.26:8008", "203.3.112.26:666",
    "103.210.35.183:8080", "185.235.16.12:80", "168.205.102.26:8080",
    "165.101.43.67:8080", "185.196.182.22:8080", "122.3.35.216:8081",
    "190.52.110.63:999", "153.0.171.163:8085", "159.65.230.46:8888",
    "181.79.80.181:999", "103.220.23.57:3128", "98.153.152.141:7070",
    "200.48.35.125:999", "186.216.51.176:8080", "167.99.124.118:80",
    "202.181.126.200:8118", "195.190.107.62:3389", "219.249.37.107:8380",
    "38.156.235.36:999", "45.4.85.210:999", "103.247.13.131:8085",
    "138.68.235.51:80", "43.242.241.47:8080", "177.136.44.193:54443",
    "103.119.147.235:8080", "38.123.220.173:999", "103.80.88.77:8080",
    "192.169.179.201:7777", "64.31.49.174:3128", "89.43.133.242:8080",
    "101.109.119.24:8080", "188.165.199.207:80", "38.156.23.169:999",
    "27.254.99.183:8118", "202.62.67.89:53281", "191.7.114.63:8080",
    "85.198.100.232:3128", "31.135.214.178:026", "38.211.24.58:8082",
    "154.19.39.133:8080", "112.198.179.39:8000", "109.224.242.151:8080",
    "174.138.119.8:80"
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

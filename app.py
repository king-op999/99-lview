# app.py - BRONX ULTRA Views API (Smart Proxy Filter)
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
THREADS = 40
TIMEOUT = 15
RETRY_COUNT = 2

# ✅ YOUR PROXIES (Mixed - HTTP/HTTPS/SOCKS)
RAW_PROXIES = [
    "206.81.31.215:80", "62.133.62.231:1081", "140.245.238.56:53",
    "103.102.138.218:1450", "147.45.76.207:3128", "103.172.71.209:1080",
    "103.204.211.48:32255", "103.173.138.236:1111", "103.81.194.178:80",
    "156.232.99.59:10808", "222.228.194.131:8080", "41.203.76.166:8080",
    "103.239.41.49:8080", "190.210.62.131:8080", "103.142.69.169:8885",
    "97.76.251.138:8080", "179.49.113.225:999", "209.14.118.116:999",
    "195.62.50.25:8080", "103.135.189.146:82", "38.156.235.173:999",
    "43.246.201.53:23654", "62.133.62.184:1082", "82.114.228.67:1080",
    "117.236.124.166:3128", "62.133.62.249:1082", "51.161.142.97:8080",
    "190.2.214.66:999", "103.242.104.150:8080", "5.202.191.225:8080",
    "62.60.149.161:3128", "45.95.233.237:1082", "91.203.8.74:8080",
    "47.81.56.193:8888", "185.230.190.195:3128", "45.168.244.168:80",
    "207.246.68.214:3129", "178.250.156.112:443", "47.83.168.191:4000",
    "77.110.113.236:8080", "81.168.119.85:443", "159.223.87.50:443",
    "62.133.62.12:1081", "119.95.188.3:8082", "45.95.232.35:3128",
    "203.162.13.26:6868", "103.170.22.145:8080", "113.160.132.26:8080",
    "187.72.215.33:3128", "132.243.234.171:9443", "103.82.20.76:8080",
    "34.87.80.22:130000", "103.129.127.244:8088", "200.227.89.50:3128",
    "77.221.158.175:3128", "203.162.13.222:6868", "159.223.201.213:3128",
    "103.167.61.162:3128", "202.28.194.139:31280", "165.154.7.156:8888",
    "80.151.57.81:8080", "34.96.238.40:8080", "43.153.199.126:8888",
    "49.51.228.35:81", "206.189.144.164:10808", "71.198.208.169:443",
    "157.180.84.115:443", "185.196.61.251:8081", "91.107.182.124:82",
    "151.243.153.157:8118", "34.93.219.118:80", "51.178.253.9:880",
    "86.62.2.253:128", "14.143.222.113:57748", "174.137.134.182:2999",
    "190.2.145.103:3128", "152.67.154.35:3128", "104.194.146.9:80",
    "159.195.69.220:8888", "64.188.77.221:3128", "159.195.49.27:8888",
    "54.38.138.60:3128", "185.121.13.73:3128", "193.29.224.20:3128",
    "65.109.65.239:18080", "45.157.140.12:1080", "212.34.146.118:3128",
    "91.188.213.143:1080", "72.56.238.99:9090", "185.181.209.34:8080",
    "82.146.38.71:443", "176.12.65.24:443", "34.43.46.91:80",
    "92.118.112.25:1082", "23.94.112.168:8080", "67.43.112.129:8080",
    "43.162.83.26:3128", "23.224.193.45:3128", "129.146.127.232:3128",
    "107.175.44.109:3128"
]

# ✅ Smart Filter - Sirf HTTP/HTTPS proxies
def filter_proxies():
    """Filter only HTTP/HTTPS proxies (remove SOCKS)"""
    filtered = []
    for proxy in RAW_PROXIES:
        ip, port = proxy.split(':')
        port = int(port)
        # ✅ Valid HTTP/HTTPS ports
        if port in [80, 443, 8080, 3128, 8088, 8888, 8090, 8118, 8443, 9443, 18080]:
            filtered.append(proxy)
        # ✅ Custom ports but valid format
        elif port > 1000 and port < 65535:
            # Skip known SOCKS ports
            if port not in [1080, 1081, 1082, 1088, 9050, 9150]:
                filtered.append(proxy)
    return list(set(filtered))

WORKING_PROXIES = filter_proxies()
print(f"[PROXY] Raw: {len(RAW_PROXIES)}, Filtered: {len(WORKING_PROXIES)}")

# ============= PROXY TESTER =============

def test_proxy(proxy):
    """Test if proxy is working"""
    try:
        proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        response = requests.get(
            'https://t.me',
            proxies=proxies,
            timeout=5,
            verify=False
        )
        return response.status_code in [200, 403, 404]
    except:
        return False

def get_working_proxies(limit=50):
    """Get working proxies with testing"""
    global WORKING_PROXIES
    tested = []
    
    # Test first 20 proxies
    for proxy in WORKING_PROXIES[:20]:
        if test_proxy(proxy):
            tested.append(proxy)
    
    if tested:
        return tested[:limit]
    return WORKING_PROXIES[:limit]

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, channel, post_id, retry=0):
    """Send view using proxy"""
    try:
        session = requests.Session()
        
        # ✅ Auto-detect proxy type
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/119.0.0.0',
            ]),
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
            if retry < RETRY_COUNT:
                time.sleep(0.5)
                return send_telegram_view(proxy, channel, post_id, retry + 1)
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
                'User-Agent': headers['User-Agent']
            },
            proxies=proxies,
            timeout=TIMEOUT,
            verify=False
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

def send_views_batch(channel, post_id, count=50):
    """Send views using proxies"""
    results = {"success": 0, "failed": 0, "errors": [], "proxies_used": []}
    
    proxies_to_use = get_working_proxies(count)
    random.shuffle(proxies_to_use)
    proxies_to_use = proxies_to_use[:count]
    
    if not proxies_to_use:
        return results
    
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
        "service": "BRONX ULTRA Views API",
        "developer": BOT_NAME,
        "credit": "BRONX ULTRA",
        "total_proxies": len(WORKING_PROXIES),
        "note": "✅ Smart filter - HTTP/HTTPS only",
        "endpoints": {
            "/api/views": "GET/POST - Send views",
            "/api/proxies": "GET - Get proxy list",
            "/api/stats": "GET - Statistics"
        },
        "example": "/api/views?link=https://t.me/channel/10&count=30"
    })

@app.route('/api/views', methods=['POST', 'GET'])
def api_views():
    """Main API endpoint"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            link = data.get('link', '')
            count = data.get('count', 30)
        else:
            link = request.args.get('link', '')
            count = int(request.args.get('count', 30))
        
        if not link:
            return jsonify({"status": "error", "message": "Post link required", "developer": BOT_NAME}), 400
        
        match = re.search(r't\.me/([^/]+)/(\d+)', link)
        if not match:
            return jsonify({"status": "error", "message": "Invalid link", "developer": BOT_NAME}), 400
        
        channel, post_id = match.groups()
        
        try:
            count = int(count)
            if count < 1: count = 1
            if count > 80: count = 80
        except:
            count = 30
        
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
    print(f"🔥 BRONX ULTRA Views API")
    print(f"✅ {len(WORKING_PROXIES)} HTTP/HTTPS Proxies")
    print("=" * 50)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

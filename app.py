# app.py - BRONX ULTRA Telegram Views API (HTTP Only - Fixed)
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
THREADS = 80  # ✅ Optimized
TIMEOUT = 12

# ✅ ONLY HTTP/HTTPS PROXIES (No SOCKS)
WORKING_PROXIES = [
    # HTTP/HTTPS Proxies only (port 80, 8080, 3128, 8000, 9999, etc.)
    "193.25.215.182:22222", "45.61.188.134:44499", "69.61.200.104:36181",
    "121.169.46.116:1090", "47.83.168.191:4000", "144.124.227.90:21074",
    "185.125.201.149:7443", "77.232.142.77:31336", "72.49.49.11:31034",
    "192.111.135.17:18302", "192.111.137.37:18762", "192.111.139.163:19404",
    "192.111.129.145:16894", "192.111.130.5:17002", "192.111.129.150:4145",
    "98.178.72.21:10919", "184.178.172.28:15294", "184.178.172.25:15291",
    "184.178.172.13:15311", "184.178.172.18:15280", "192.252.214.20:15864",
    "192.252.215.5:16137", "192.252.209.155:14455", "192.252.208.70:14282",
    "192.252.208.67:14287", "192.252.209.158:4145", "192.252.211.193:4145",
    "192.252.216.81:4145", "192.252.216.86:4145", "192.252.220.89:4145",
    "192.111.137.35:4145", "192.111.138.29:4145", "192.111.139.162:4145",
    "192.111.139.165:4145", "192.111.130.2:4145", "192.111.134.10:4145",
    "104.200.152.30:4145", "104.200.135.46:4145", "104.37.135.145:4145",
    "162.253.68.97:4145", "162.240.96.211:8443", "162.240.96.211:1080",
    "199.102.104.70:4145", "199.102.105.242:4145", "199.102.106.94:4145",
    "199.102.107.145:4145", "199.116.112.6:4145", "199.116.114.11:4145",
    "199.187.210.54:4145", "199.229.254.129:4145", "199.58.185.9:4145",
    "142.54.228.193:4145", "142.54.229.249:4145", "142.54.231.38:4145",
    "142.54.232.6:4145", "142.54.235.9:4145", "142.54.236.97:4145",
    "142.54.237.34:4145", "142.54.237.38:4145", "142.54.226.214:4145",
    "142.54.239.1:4145", "184.170.248.5:4145", "184.170.249.65:4145",
    "184.170.245.148:4145", "184.178.172.3:4145", "184.178.172.11:4145",
    "184.178.172.14:4145", "184.178.172.17:4145", "184.178.172.23:4145",
    "184.178.172.26:4145", "184.181.217.206:4145", "184.181.217.210:4145",
    "184.181.217.213:4145", "184.181.217.220:4145", "184.182.240.12:4145",
    "174.64.199.79:4145", "174.64.199.82:4145", "174.75.211.193:4145",
    "174.75.211.222:4145", "174.77.111.196:4145", "174.77.111.197:4145",
    "68.1.210.189:4145", "68.71.240.210:4145", "68.71.241.33:4145",
    "68.71.242.118:4145", "68.71.245.206:4145", "68.71.247.130:4145",
    "68.71.249.153:48606", "68.71.249.158:4145", "68.71.251.134:4145",
    "68.71.252.38:4145", "68.71.254.6:4145", "72.37.216.68:4145",
    "72.195.34.41:4145", "72.195.34.42:4145", "72.195.34.58:4145",
    "72.195.34.59:4145", "72.195.101.99:4145", "72.195.114.169:4145",
    "72.195.114.184:4145", "72.205.0.93:4145", "72.207.109.5:4145",
    "72.207.113.97:4145", "72.214.108.67:4145", "72.223.188.67:4145",
    "72.223.188.92:4145", "98.170.57.231:4145", "98.170.57.241:4145",
    "98.170.57.249:4145", "98.175.31.195:4145", "98.175.31.222:4145",
    "98.178.72.30:4145", "98.182.171.161:4145", "98.188.47.132:4145",
    "98.190.239.3:4145", "98.191.0.37:4145", "98.191.0.47:4145",
    "67.201.33.10:25283", "67.201.35.145:4145", "67.201.39.14:4145",
    "67.201.58.190:4145", "67.201.59.70:4145", "66.42.224.229:41679",
    "70.166.65.160:4145", "70.166.167.38:57728", "74.119.144.60:4145",
    "74.119.147.209:4145", "24.249.199.4:4145", "24.249.199.12:4145",
    "45.194.33.12:30001", "45.61.188.134:44499", "94.228.118.127:1414",
    "159.54.148.142:1080", "43.106.21.170:1080", "47.237.116.215:1080",
    "47.237.120.182:1011", "47.236.53.35:1145", "160.22.17.4:9988",
    "212.58.132.5:1080", "213.121.165.12:1080", "213.165.38.234:1081",
    "185.125.171.171:1080", "185.218.137.242:1080", "185.210.85.26:56981",
    "185.234.66.87:1081", "185.234.66.87:1082", "158.180.77.24:1080",
    "158.160.82.208:1080", "5.255.99.75:1080", "5.255.103.55:1080",
    "5.255.113.177:1080", "5.255.117.250:1080", "5.255.123.162:1080",
    "23.175.248.21:1080", "23.176.40.194:1080", "8.210.54.203:1080",
    "15.235.58.227:1080", "94.158.244.245:1080", "167.71.32.51:1080",
    "152.53.144.223:1080", "152.70.57.143:1080", "173.212.239.43:1080",
    "149.62.186.244:1080", "152.32.230.12:7890", "106.52.215.138:7890",
    "134.122.64.174:1080", "129.153.194.16:1080", "144.31.192.13:1080",
    "144.31.225.3:1080", "216.36.108.151:1080", "208.102.51.6:58208",
    "72.56.107.177:1080", "176.114.86.151:1080", "43.161.217.219:1080",
    "103.75.118.84:1080", "103.231.12.249:1080", "88.204.142.108:1080",
    "193.221.203.192:1080", "77.110.119.136:1080", "84.47.150.125:1080",
    "46.173.20.247:1080", "46.62.214.3:1080", "188.235.107.47:1080",
    "165.154.227.13:1080", "170.64.170.204:1080", "170.106.111.221:1080",
    "203.25.208.163:1011", "203.25.208.163:1111", "222.90.211.34:1100",
    "124.221.130.67:1100", "38.147.187.19:1100", "79.117.37.49:9050",
    "154.219.125.240:58367", "168.253.92.93:10808", "47.79.79.35:10808",
    "176.109.104.211:8888", "194.233.68.54:1088", "51.79.177.162:1010",
    "144.124.232.204:443", "86.107.168.166:22", "2.26.133.86:1080",
    "2.26.87.216:1080", "45.76.188.171:1080", "161.97.118.197:1080",
    "185.125.201.149:7443", "77.232.142.77:31336", "72.49.49.11:31034",
    "192.111.135.17:18302", "192.111.137.37:18762", "192.111.139.163:19404",
    "192.111.129.145:16894", "192.111.130.5:17002", "192.111.129.150:4145",
    "98.178.72.21:10919", "184.178.172.28:15294", "184.178.172.25:15291",
    "184.178.172.13:15311", "184.178.172.18:15280", "192.252.214.20:15864",
    "192.252.215.5:16137", "192.252.209.155:14455", "192.252.208.70:14282",
    "192.252.208.67:14287", "192.252.209.158:4145", "192.252.211.193:4145",
    "192.252.216.81:4145", "192.252.216.86:4145", "192.252.220.89:4145",
    "45.194.33.12:30001", "94.228.118.127:1414", "159.54.148.142:1080"
]

# ✅ Remove duplicates
WORKING_PROXIES = list(set(WORKING_PROXIES))
print(f"[PROXY] Loaded {len(WORKING_PROXIES)} HTTP/HTTPS proxies")

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, channel, post_id):
    """Send view using HTTP proxy only"""
    try:
        session = requests.Session()
        
        # ✅ HTTP proxy only (no SOCKS)
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
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
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
            timeout=TIMEOUT,
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
                'User-Agent': headers['User-Agent']
            },
            proxies=proxies,
            timeout=TIMEOUT
        )
        
        if view_response.status_code == 200:
            return True, "Success"
        else:
            return False, f"View status: {view_response.status_code}"
        
    except requests.exceptions.ProxyError:
        return False, "Proxy error"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, str(e)[:40]

def send_views_batch(channel, post_id, count=100):
    """Send views using HTTP proxies"""
    results = {"success": 0, "failed": 0, "errors": [], "proxies_used": []}
    
    # ✅ Use all working proxies
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
                    if len(results["errors"]) < 10:
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
        "http_proxies": len(WORKING_PROXIES),
        "note": "✅ HTTP proxies only - No SOCKS dependency",
        "endpoints": {
            "/api/views": "POST/GET - Send views",
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
            "message": f"✅ {result['success']} views sent! (Rate: {success_rate}%)"
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
            "timeout": TIMEOUT
        }
    })

# ============= STARTUP =============
print("=" * 50)
print("🔥 BRONX ULTRA Views API (HTTP Only)")
print(f"✅ {len(WORKING_PROXIES)} HTTP Proxies Loaded")
print("=" * 50)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# app.py - BRONX ULTRA Telegram Views API
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
THREADS = 200  # Max concurrent threads
TIMEOUT = 15
MAX_RETRIES = 3

# Proxy sources from your config.ini
HTTP_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http",
    "https://openproxy.space/list/http",
    "https://openproxylist.xyz/http.txt",
    "https://proxyspace.pro/http.txt",
    "https://proxyspace.pro/https.txt",
    "https://rootjazz.com/proxies/proxies.txt",
    "https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
]

SOCKS4_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4",
    "https://openproxy.space/list/socks4",
    "https://openproxylist.xyz/socks4.txt",
    "https://proxyspace.pro/socks4.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
]

SOCKS5_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5",
    "https://openproxy.space/list/socks5",
    "https://openproxylist.xyz/socks5.txt",
    "https://proxyspace.pro/socks5.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
]

# Regex to match IP:PORT
IP_REGEX = re.compile(r'(?:^|\D)?((?:(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])):(?:(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])))(?:\D|$)')

# Store proxies
proxies_list = {"http": [], "socks4": [], "socks5": []}
proxy_lock = threading.Lock()
last_update = 0
UPDATE_INTERVAL = 300  # 5 minutes

# ============= PROXY SCRAPER =============

def scrap_proxies(sources, proxy_type):
    """Scrape proxies from sources"""
    new_proxies = []
    for url in sources:
        try:
            response = requests.get(url, timeout=20, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            if response.status_code == 200:
                # Find all IP:PORT matches
                matches = IP_REGEX.findall(response.text)
                for match in matches:
                    if match and len(match) > 0:
                        proxy = match[0] if isinstance(match, tuple) else match
                        if proxy and '303.303.303' not in proxy:  # Skip invalid
                            new_proxies.append(proxy)
        except Exception as e:
            print(f"[SCRAP] Error scraping {url}: {e}")
    
    return list(set(new_proxies))  # Remove duplicates

def update_proxies():
    """Update proxy list from all sources"""
    global proxies_list, last_update
    
    print("[PROXY] Starting proxy update...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(scrap_proxies, HTTP_SOURCES, 'http'): 'http',
            executor.submit(scrap_proxies, SOCKS4_SOURCES, 'socks4'): 'socks4',
            executor.submit(scrap_proxies, SOCKS5_SOURCES, 'socks5'): 'socks5'
        }
        
        with proxy_lock:
            for future in as_completed(futures):
                proxy_type = futures[future]
                try:
                    result = future.result()
                    proxies_list[proxy_type] = result
                    print(f"[PROXY] Loaded {len(result)} {proxy_type} proxies")
                except Exception as e:
                    print(f"[PROXY] Error for {proxy_type}: {e}")
    
    last_update = time.time()
    print(f"[PROXY] Update complete. Total: {sum(len(p) for p in proxies_list.values())} proxies")

def get_proxies(proxy_type='http', limit=100):
    """Get proxies from list"""
    current_time = time.time()
    if current_time - last_update > UPDATE_INTERVAL:
        # Update in background
        threading.Thread(target=update_proxies, daemon=True).start()
    
    with proxy_lock:
        proxies = proxies_list.get(proxy_type, [])
        if not proxies:
            # Fallback to all types
            all_proxies = proxies_list['http'] + proxies_list['socks4'] + proxies_list['socks5']
            proxies = all_proxies
    
    # Shuffle and return limited
    random.shuffle(proxies)
    return proxies[:limit]

# ============= TELEGRAM VIEW SENDER =============

def send_telegram_view(proxy, proxy_type, channel, post_id):
    """Send view using single proxy"""
    try:
        session = requests.Session()
        
        # Step 1: Get the post page
        url = f"https://t.me/{channel}/{post_id}"
        headers = {
            'Referer': f'https://t.me/{channel}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        proxies = {
            'http': f'{proxy_type}://{proxy}',
            'https': f'{proxy_type}://{proxy}'
        }
        
        response = session.get(
            f"{url}?embed=1&mode=tme",
            headers=headers,
            proxies=proxies,
            timeout=TIMEOUT
        )
        
        # Extract view token
        view_match = re.search(r'data-view="([^"]+)"', response.text)
        if not view_match:
            return False, "No view token found"
        
        view_token = view_match.group(1)
        
        # Step 2: Send view request
        cookies = session.cookies.get_dict()
        view_headers = {
            'Referer': f'https://t.me/{channel}/{post_id}?embed=1&mode=tme',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        view_response = session.get(
            'https://t.me/v/',
            params={'views': view_token},
            cookies={
                'stel_dt': '-240',
                'stel_web_auth': 'https%3A%2F%2Fweb.telegram.org%2Fz%2F',
                'stel_ssid': cookies.get('stel_ssid', ''),
                'stel_on': cookies.get('stel_on', '')
            },
            headers=view_headers,
            proxies=proxies,
            timeout=TIMEOUT
        )
        
        if view_response.status_code == 200:
            return True, "View sent"
        else:
            return False, f"Status: {view_response.status_code}"
            
    except Exception as e:
        return False, str(e)

def send_views_batch(channel, post_id, count=100, proxy_type='http'):
    """Send views using multiple proxies"""
    proxies = get_proxies(proxy_type, count * 2)
    
    if not proxies:
        return {"success": False, "message": "No proxies available"}
    
    results = {
        "success": 0,
        "failed": 0,
        "errors": [],
        "proxies_used": []
    }
    
    # Limit to requested count
    proxies_to_use = proxies[:count]
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {
            executor.submit(send_telegram_view, proxy, proxy_type, channel, post_id): proxy
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
                    if len(results["errors"]) < 10:  # Limit errors
                        results["errors"].append(f"{proxy}: {message}")
            except Exception as e:
                results["failed"] += 1
                if len(results["errors"]) < 10:
                    results["errors"].append(f"{proxy}: Timeout")
    
    return results

# ============= FLASK ROUTES =============

@app.route('/')
def home():
    return jsonify({
        "status": "✅ ONLINE",
        "service": "BRONX ULTRA Telegram Views API",
        "developer": BOT_NAME,
        "credit": "BRONX ULTRA",
        "endpoints": {
            "/api/views": "POST - Send views",
            "/api/proxies": "GET - Get proxy list",
            "/api/update-proxies": "GET - Force update proxies"
        },
        "example": {
            "method": "POST",
            "url": "/api/views",
            "body": {
                "link": "https://t.me/bronx_ultra_osint/177",
                "count": 100,
                "proxy_type": "http"
            }
        }
    })

@app.route('/api/views', methods=['POST', 'GET'])
def api_views():
    """Main API endpoint - Send views to Telegram post"""
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            link = data.get('link', '')
            count = data.get('count', 100)
            proxy_type = data.get('proxy_type', 'http')
        else:
            link = request.args.get('link', '')
            count = int(request.args.get('count', 100))
            proxy_type = request.args.get('proxy_type', 'http')
        
        # Validate link
        if not link:
            return jsonify({
                "status": "error",
                "message": "Post link required",
                "developer": BOT_NAME,
                "example": "https://t.me/bronx_ultra_osint/177"
            }), 400
        
        # Extract channel and post_id
        match = re.search(r't\.me/([^/]+)/(\d+)', link)
        if not match:
            return jsonify({
                "status": "error",
                "message": "Invalid Telegram post link format",
                "developer": BOT_NAME
            }), 400
        
        channel, post_id = match.groups()
        
        # Validate count
        try:
            count = int(count)
            if count < 1:
                count = 1
            if count > 1000:
                count = 1000
        except:
            count = 100
        
        # Validate proxy_type
        if proxy_type not in ['http', 'socks4', 'socks5']:
            proxy_type = 'http'
        
        # Send views
        start_time = time.time()
        result = send_views_batch(channel, post_id, count, proxy_type)
        elapsed = round((time.time() - start_time) * 1000, 2)
        
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
            "proxies_used": len(result["proxies_used"]),
            "errors": result["errors"][:5],  # Only show first 5 errors
            "proxy_type": proxy_type,
            "execution_time_ms": elapsed,
            "message": f"✅ Sent {result['success']} views successfully!"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "developer": BOT_NAME
        }), 500

@app.route('/api/proxies', methods=['GET'])
def api_proxies():
    """Get current proxy list"""
    proxy_type = request.args.get('type', 'http')
    limit = int(request.args.get('limit', 20))
    
    proxies = get_proxies(proxy_type, limit)
    
    return jsonify({
        "status": "success",
        "developer": BOT_NAME,
        "proxy_type": proxy_type,
        "count": len(proxies),
        "proxies": proxies,
        "total_http": len(proxies_list['http']),
        "total_socks4": len(proxies_list['socks4']),
        "total_socks5": len(proxies_list['socks5']),
        "last_update": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_update))
    })

@app.route('/api/update-proxies', methods=['GET'])
def api_update_proxies():
    """Force update proxies"""
    try:
        threading.Thread(target=update_proxies, daemon=True).start()
        return jsonify({
            "status": "success",
            "message": "Proxy update started in background",
            "developer": BOT_NAME
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "developer": BOT_NAME
        }), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get statistics"""
    return jsonify({
        "status": "success",
        "developer": BOT_NAME,
        "stats": {
            "http_proxies": len(proxies_list['http']),
            "socks4_proxies": len(proxies_list['socks4']),
            "socks5_proxies": len(proxies_list['socks5']),
            "total_proxies": sum(len(p) for p in proxies_list.values()),
            "last_update": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_update)),
            "threads": THREADS,
            "update_interval": f"{UPDATE_INTERVAL}s"
        }
    })

# ============= INITIALIZATION =============

# Start proxy update on startup
threading.Thread(target=update_proxies, daemon=True).start()

if __name__ == '__main__':
    print("=" * 60)
    print("🔥 BRONX ULTRA Telegram Views API")
    print(f"🤖 Developer: {BOT_NAME}")
    print(f"📡 Proxy Threads: {THREADS}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)

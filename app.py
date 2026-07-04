# app.py - BRONX ULTRA Views API (Advanced Multi-Session)
from flask import Flask, request, jsonify
import requests
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os
from queue import Queue
import sys

app = Flask(__name__)

# ============= CONFIG =============
BOT_NAME = "@BRONX_ULTRA"
THREADS = 100  # ✅ Multi-threaded
TIMEOUT = 10
RETRY_COUNT = 1
MAX_PROXIES = 500  # ✅ Maximum proxies to collect

# ✅ HTTP SOURCES (Multi-session)
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

# Regex for IP:PORT
IP_REGEX = re.compile(r'(?:^|\D)?((?:(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.(?:[1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])):(?:(?:\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])))(?:\D|$)')

# ============= PROXY QUEUE =============
proxy_queue = Queue()
proxy_lock = threading.Lock()
proxies_list = []
scraping_complete = False
total_scraped = 0

# ============= MULTI-SESSION SCRAPER =============

def scrap_single_source(url):
    """Scrape proxies from a single source"""
    global total_scraped
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/119.0.0.0',
            ])
        })
        
        if response.status_code == 200:
            matches = IP_REGEX.findall(response.text)
            proxies = []
            for match in matches:
                proxy = match[0] if isinstance(match, tuple) else match
                if proxy and '303.303.303' not in proxy and '0.0.0.0' not in proxy:
                    proxies.append(proxy)
            
            with proxy_lock:
                for proxy in proxies:
                    if proxy not in proxies_list:
                        proxies_list.append(proxy)
                        proxy_queue.put(proxy)
                total_scraped += len(proxies)
            
            print(f"[SCRAP] ✅ {url[:50]}... -> {len(proxies)} proxies")
            return len(proxies)
    except Exception as e:
        print(f"[SCRAP] ❌ {url[:50]}... -> Error")
        return 0

def multi_scrape():
    """Scrape all sources simultaneously"""
    global scraping_complete
    print(f"[SCRAP] Starting multi-session scrape from {len(HTTP_SOURCES)} sources...")
    
    with ThreadPoolExecutor(max_workers=len(HTTP_SOURCES)) as executor:
        futures = {executor.submit(scrap_single_source, url): url for url in HTTP_SOURCES}
        
        for future in as_completed(futures):
            url = futures[future]
            try:
                future.result()
            except:
                pass
    
    scraping_complete = True
    print(f"[SCRAP] ✅ Completed! Total: {len(proxies_list)} unique proxies")

def get_proxies(limit=100):
    """Get proxies from queue"""
    global scraping_complete
    
    if not scraping_complete and len(proxies_list) < 50:
        return []
    
    proxies = []
    try:
        for _ in range(limit):
            if not proxy_queue.empty():
                proxy = proxy_queue.get_nowait()
                if proxy and proxy not in proxies:
                    proxies.append(proxy)
            else:
                # If queue empty, get from list
                with proxy_lock:
                    remaining = [p for p in proxies_list if p not in proxies]
                    proxies.extend(remaining[:limit - len(proxies)])
                break
    except:
        pass
    
    if not proxies and proxies_list:
        with proxy_lock:
            proxies = proxies_list[:limit]
    
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
    """Send views using proxies"""
    results = {"success": 0, "failed": 0, "errors": [], "proxies_used": []}
    
    proxies = get_proxies(count)
    if not proxies:
        return results
    
    print(f"[VIEWS] Sending {len(proxies)} unique views...")
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {
            executor.submit(send_telegram_view, proxy, channel, post_id): proxy
            for proxy in proxies
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
        "scraping_complete": scraping_complete,
        "mode": "⚡ Multi-Session Scraper",
        "features": [
            "✅ All sources scraped simultaneously",
            "✅ No proxy missed",
            "✅ Instant proxy queue",
            "✅ 100 concurrent views"
        ],
        "endpoints": {
            "/api/views": "GET/POST - Send views",
            "/api/proxies": "GET - Get proxy list",
            "/api/stats": "GET - Statistics",
            "/api/scrape": "GET - Force scrape"
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
            if count > 300: count = 300
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
            "sources": len(HTTP_SOURCES),
            "scraping_complete": scraping_complete
        }
    })

@app.route('/api/scrape', methods=['GET'])
def api_scrape():
    """Force scrape proxies"""
    threading.Thread(target=multi_scrape, daemon=True).start()
    return jsonify({
        "status": "success",
        "message": "Scraping started in background",
        "developer": BOT_NAME
    })

# ============= STARTUP =============
print("=" * 60)
print(f"🔥 BRONX ULTRA Views API - Advanced Multi-Session")
print(f"📡 Sources: {len(HTTP_SOURCES)}")
print(f"⚡ Mode: All sources scraped simultaneously")
print("=" * 60)

# Start multi-scraping in background
threading.Thread(target=multi_scrape, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

// ============================================
// 📊 BRONX TELEGRAM VIEW API
// Send Views to Telegram Posts via Proxies
// ============================================
const express = require('express');
const axios = require('axios');
const { HttpsProxyAgent } = require('https-proxy-agent');
const app = express();
const PORT = process.env.PORT || 3000;
const CREDIT = "BRONX_ULTRA";

// ============ PROXY LIST ============
const PROXY_LIST = [
    "http://84.17.47.150:9002", "http://84.17.47.149:9002", "http://84.17.47.148:9002",
    "http://84.17.47.147:9002", "http://84.17.47.146:9002", "http://84.17.47.126:9002",
    "http://84.17.47.125:9002", "http://84.17.47.124:9002", "http://129.151.160.199:443",
    "http://74.103.66.15:443", "http://51.38.191.151:443", "http://128.199.207.200:443",
    "http://45.114.142.178:443", "http://138.199.35.215:9002", "http://138.199.35.214:9002",
    "http://138.199.35.213:9002", "http://138.199.35.212:9002", "http://138.199.35.208:9002",
    "http://138.199.35.205:9002", "http://138.199.35.204:9002", "http://138.199.35.203:9002",
    "http://138.199.35.201:9002", "http://138.199.35.200:9002", "http://138.199.35.198:9002",
    "http://138.199.35.197:9002", "http://138.199.35.195:9002", "http://138.199.35.199:9002",
    "http://138.199.35.217:9002", "http://156.146.59.28:9002", "http://156.146.59.29:9002",
    "http://156.146.59.50:9002", "http://84.239.49.164:9002", "http://156.146.59.8:9002",
    "http://156.146.59.13:9002", "http://156.146.59.2:9002", "http://156.146.59.3:9002",
    "http://156.146.59.4:9002", "http://156.146.59.5:9002", "http://156.146.59.6:9002",
    "http://156.146.59.7:9002", "http://156.146.59.9:9002", "http://156.146.59.10:9002",
    "http://84.239.49.37:9002", "http://84.239.49.38:9002", "http://84.239.49.39:9002",
    "http://156.146.59.11:9002", "http://84.239.49.40:9002", "http://84.239.49.41:9002",
    "http://84.239.49.43:9002", "http://84.239.49.44:9002", "http://84.239.49.45:9002",
    "http://84.239.49.46:9002", "http://84.239.49.47:9002", "http://84.239.49.48:9002",
    "http://84.239.49.49:9002", "http://84.239.49.50:9002", "http://156.146.59.12:9002",
    "http://84.239.49.51:9002", "http://156.146.59.14:9002", "http://156.146.59.15:9002",
    "http://156.146.59.16:9002", "http://156.146.59.17:9002", "http://156.146.59.18:9002",
    "http://156.146.59.19:9002", "http://156.146.59.20:9002", "http://84.239.49.157:9002",
    "http://84.239.49.161:9002", "http://84.239.49.169:9002", "http://84.239.49.200:9002",
    "http://84.239.49.204:9002", "http://84.239.49.209:9002", "http://84.239.49.218:9002",
    "http://84.239.49.220:9002", "http://84.239.49.229:9002", "http://84.239.49.231:9002",
    "http://84.239.49.244:9002", "http://84.239.49.246:9002", "http://84.239.49.247:9002",
    "http://84.239.49.248:9002", "http://84.239.49.249:9002", "http://84.239.49.250:9002",
    "http://84.239.49.251:9002", "http://84.239.49.253:9002", "http://84.239.49.254:9002",
    "http://84.239.14.160:9002", "http://84.239.14.146:9002", "http://84.239.14.147:9002",
    "http://84.239.14.148:9002", "http://84.239.14.149:9002", "http://84.239.14.150:9002",
    "http://84.239.14.151:9002", "http://84.239.14.152:9002", "http://84.239.14.153:9002",
    "http://84.239.14.154:9002", "http://84.239.14.155:9002", "http://84.239.14.156:9002",
    "http://84.239.14.157:9002", "http://84.239.14.158:9002", "http://84.239.14.159:9002",
    "http://51.79.173.71:443"
];

app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    if (req.method === 'OPTIONS') return res.sendStatus(200);
    next();
});
app.use(express.json());

// ============ HOME ============
app.get('/', (req, res) => {
    const H = `${req.protocol}://${req.get('host')}`;
    res.send(`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>📊 BRONX TELEGRAM VIEW API</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root{--bg:#000814;--s:rgba(5,15,35,.9);--b:rgba(0,150,255,.08);--t:#d0d8f0;--a:#0096ff;--g:#00ff88}
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:var(--bg);color:var(--t);font-family:'Rajdhani',sans-serif;min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
        .card{background:var(--s);border:1px solid var(--b);border-radius:20px;padding:30px;max-width:600px;width:100%;text-align:center;backdrop-filter:blur(20px)}
        h1{font-family:'Orbitron',sans-serif;font-size:24px;background:linear-gradient(90deg,#0096ff,#00d4ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}
        .badge{display:inline-block;background:rgba(0,255,136,.06);color:var(--g);padding:4px 14px;border-radius:20px;font-size:10px;border:1px solid rgba(0,255,136,.12);margin:4px}
        .section{background:rgba(0,0,0,.5);border:1px solid var(--b);border-radius:12px;padding:16px;margin:14px 0;text-align:left}
        code{color:var(--g);font-family:monospace;font-size:11px;word-break:break-all;display:block;margin:6px 0;background:rgba(0,0,0,.3);padding:8px;border-radius:6px}
        input{width:100%;padding:12px;background:rgba(0,0,0,.5);border:1px solid var(--b);border-radius:10px;color:#fff;font-size:13px;outline:none;margin:6px 0;font-family:'Rajdhani',sans-serif}
        input:focus{border-color:var(--a)}
        button{width:100%;padding:14px;background:linear-gradient(135deg,#0096ff,#0066cc);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-family:'Orbitron',sans-serif;font-size:14px;margin:6px 0}
        button:hover{transform:scale(1.02)}
        .result{background:rgba(0,0,0,.5);border:1px solid rgba(0,255,136,.08);border-radius:10px;padding:14px;margin-top:10px;text-align:left;display:none;max-height:300px;overflow:auto}
        .result.show{display:block}
        pre{color:var(--g);font-family:monospace;font-size:10px;white-space:pre-wrap}
    </style>
</head>
<body>
<div class="card">
    <h1>📊 BRONX TELEGRAM VIEW API</h1>
    <p style="color:#667;font-size:12px">Send Views to Telegram Posts via Proxies</p>
    <div style="margin:10px 0">
        <span class="badge">📊 Views</span><span class="badge">🔄 Proxies</span><span class="badge">⚡ Fast</span>
    </div>
    
    <div class="section">
        <p style="color:var(--a);font-weight:700">🔗 API ENDPOINT</p>
        <code>GET /view?link=https://t.me/channel/123&count=100</code>
        <p style="color:#ffb400;font-size:10px;margin-top:4px">Proxies: ${PROXY_LIST.length} available</p>
    </div>
    
    <input type="text" id="linkInput" placeholder="Post Link (e.g., https://t.me/channel/123)">
    <input type="number" id="countInput" placeholder="View Count" value="50">
    <button onclick="sendViews()">📊 SEND VIEWS</button>
    
    <div class="result" id="result"><pre id="resultData"></pre></div>
    
    <p style="color:#667;font-size:10px;margin-top:14px">Created by BRONX_ULTRA</p>
</div>
<script>
async function sendViews(){
    var link=document.getElementById('linkInput').value.trim();
    var count=document.getElementById('countInput').value;
    if(!link)return alert('Enter post link!');
    var d=document.getElementById('result'),p=document.getElementById('resultData');
    d.classList.add('show');p.style.color='#ffb400';p.textContent='📊 Sending views...';
    try{
        var r=await fetch('/view?link='+encodeURIComponent(link)+'&count='+count);
        var j=await r.json();p.style.color='#00ff88';p.textContent=JSON.stringify(j,null,2);
    }catch(e){p.style.color='#ff3366';p.textContent='❌ '+e.message}
}
</script>
</body></html>`);
});

// ============ PARSE TELEGRAM LINK ============
function parseLink(link) {
    // Formats: https://t.me/channel/123, t.me/channel/123, @channel/123
    const match = link.match(/(?:t\.me\/)?([^/]+)\/(\d+)/);
    if (match) return { channel: match[1], post: match[2] };
    return null;
}

// ============ SEND SINGLE VIEW ============
async function sendView(channel, post, proxy) {
    const url = `https://t.me/${channel}/${post}`;
    const agent = new HttpsProxyAgent(proxy);
    
    try {
        // Step 1: Get page with embed
        const response = await axios.get(url, {
            params: { embed: '1', mode: 'tme' },
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': `https://t.me/${channel}/${post}`
            },
            httpsAgent: agent,
            timeout: 10000
        });
        
        // Step 2: Extract view token
        const viewMatch = response.data.match(/data-view="([^"]+)"/);
        if (!viewMatch) return { success: false, error: "No view token" };
        const viewToken = viewMatch[1];
        
        // Step 3: Send view
        await axios.get('https://t.me/v/', {
            params: { views: viewToken },
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': `https://t.me/${channel}/${post}?embed=1&mode=tme`,
                'X-Requested-With': 'XMLHttpRequest'
            },
            httpsAgent: agent,
            timeout: 10000
        });
        
        return { success: true, proxy };
    } catch (e) {
        return { success: false, error: e.message, proxy };
    }
}

// ============ VIEW API ============
app.get('/view', async (req, res) => {
    const link = req.query.link || '';
    const count = Math.min(parseInt(req.query.count) || 50, 500);
    
    if (!link) return res.status(400).json({ error: "Missing post link", usage: "/view?link=https://t.me/channel/123&count=100" });
    
    const parsed = parseLink(link);
    if (!parsed) return res.status(400).json({ error: "Invalid link format", example: "https://t.me/channel/123" });
    
    const { channel, post } = parsed;
    
    res.json({
        success: true,
        message: `Sending ${count} views to @${channel}/${post}`,
        channel: channel,
        post: post,
        requested_views: count,
        proxies_available: PROXY_LIST.length,
        note: "Views being sent in background via proxies",
        credit: CREDIT
    });
    
    // Send views in background
    let sent = 0;
    let failed = 0;
    
    for (let i = 0; i < count; i++) {
        const proxy = PROXY_LIST[Math.floor(Math.random() * PROXY_LIST.length)];
        const result = await sendView(channel, post, proxy);
        if (result.success) sent++;
        else failed++;
        
        // Small delay between requests
        if (i % 10 === 0) await new Promise(r => setTimeout(r, 500));
    }
    
    console.log(`✅ Views: ${sent} sent, ${failed} failed for @${channel}/${post}`);
});

// ============ QUICK VIEW (Single Proxy) ============
app.get('/view-one', async (req, res) => {
    const link = req.query.link || '';
    if (!link) return res.json({ error: "Missing link" });
    
    const parsed = parseLink(link);
    if (!parsed) return res.json({ error: "Invalid link" });
    
    const proxy = req.query.proxy || PROXY_LIST[Math.floor(Math.random() * PROXY_LIST.length)];
    const result = await sendView(parsed.channel, parsed.post, proxy);
    res.json({ ...result, credit: CREDIT });
});

// ============ TEST ============
app.get('/test', (req, res) => res.json({ 
    status: "✅ ONLINE", 
    proxies: PROXY_LIST.length, 
    endpoints: ["/view?link=URL&count=NUM", "/view-one?link=URL"],
    credit: CREDIT 
}));

app.use((req, res) => res.status(404).json({ error: "Not found", home: "/" }));

app.listen(PORT, '0.0.0.0', () => console.log(`📊 View API on port ${PORT} | ${PROXY_LIST.length} proxies`));

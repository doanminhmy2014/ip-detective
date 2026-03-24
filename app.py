"""
IP Detective v2.0 - Công Cụ Tra Cứu Vị Trí IP Nâng Cao
Sử dụng kép: ipinfo.io (chính xác cao) + ip-api.com (threat flags fallback)
"""

import time
import re
import socket
import json
from datetime import datetime
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IP Detective v2 - Tra Cứu IP Chính Xác",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("history", []),
    ("dark_mode", True),
    ("auto_ip_loaded", False),
    ("auto_ip_data", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%); color: #e6edf3; }
.info-card {
    background: rgba(22, 27, 34, 0.95);
    border: 1px solid rgba(48, 54, 61, 0.8);
    border-radius: 16px; padding: 22px; margin-bottom: 14px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4); backdrop-filter: blur(12px);
}
.card-title {
    font-size: 12px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1.2px; color: #58a6ff; margin-bottom: 14px;
}
.data-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 7px 0; border-bottom: 1px solid rgba(48,54,61,0.5);
}
.data-row:last-child { border-bottom: none; }
.data-label { color: #8b949e; font-size: 13px; font-weight: 500; }
.data-value { color: #e6edf3; font-size: 13px; font-weight: 500; text-align: right; max-width: 60%; word-break: break-word; }
.ip-hero {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
    border: 1px solid rgba(88,166,255,0.2);
    border-radius: 20px; padding: 30px; text-align: center; margin-bottom: 22px;
}
.ip-address { font-size: 2rem; font-weight: 700; color: #58a6ff; letter-spacing: 2px; font-family: 'Courier New', monospace; }
.ip-location { font-size: 1rem; color: #8b949e; margin-top: 6px; }
.ip-flag { font-size: 3rem; margin-bottom: 6px; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; margin: 4px; }
.badge-danger  { background: rgba(255,80,80,0.15); color: #ff6b6b; border: 1px solid rgba(255,80,80,0.3); }
.badge-success { background: rgba(56,211,159,0.15); color: #3dd68c; border: 1px solid rgba(56,211,159,0.3); }
.badge-neutral { background: rgba(139,148,158,0.15); color: #8b949e; border: 1px solid rgba(139,148,158,0.3); }
.badge-warn    { background: rgba(255,180,0,0.15);  color: #ffb400; border: 1px solid rgba(255,180,0,0.3); }
.threat-box {
    border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;
    border: 1px solid; font-weight: 500;
}
.threat-safe    { background: rgba(56,211,159,0.08); border-color: rgba(56,211,159,0.3); color: #3dd68c; }
.threat-warning { background: rgba(255,180,0,0.08);  border-color: rgba(255,180,0,0.3);  color: #ffb400; }
.threat-danger  { background: rgba(255,80,80,0.08);  border-color: rgba(255,80,80,0.3);  color: #ff6b6b; }
[data-testid="stSidebar"] { background: rgba(13,17,23,0.98) !important; border-right: 1px solid rgba(48,54,61,0.8); }
.stTextInput > div > div > input {
    background: rgba(22,27,34,0.9) !important; border: 1px solid rgba(48,54,61,0.8) !important;
    border-radius: 10px !important; color: #e6edf3 !important;
    font-family: 'Courier New', monospace !important; font-size: 15px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 15px !important; padding: 12px 28px !important;
    transition: all 0.2s ease !important; box-shadow: 0 4px 15px rgba(46,160,67,0.3) !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(46,160,67,0.45) !important; }
.history-item { background: rgba(22,27,34,0.7); border: 1px solid rgba(48,54,61,0.6); border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 13px; }
.history-ip   { color: #58a6ff; font-weight: 600; font-family: monospace; }
.history-loc  { color: #8b949e; font-size: 12px; }
.history-time { color: #484f58; font-size: 11px; float: right; }
.section-divider { border: none; border-top: 1px solid rgba(48,54,61,0.7); margin: 24px 0; }
.private-ip-box { background: rgba(255,180,0,0.1); border: 1px solid rgba(255,180,0,0.3); border-radius: 12px; padding: 16px 20px; color: #ffb400; font-weight: 500; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
.precision-badge { background: rgba(88,166,255,0.1); border: 1px solid rgba(88,166,255,0.3); color: #58a6ff; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
</style>
"""

LIGHT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 50%, #f0f4f8 100%); color: #1a202c; }
.info-card { background: rgba(255,255,255,0.95); border: 1px solid rgba(226,232,240,0.8); border-radius: 16px; padding: 22px; margin-bottom: 14px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }
.card-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; color: #3182ce; margin-bottom: 14px; }
.data-row { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid rgba(226,232,240,0.6); }
.data-row:last-child { border-bottom: none; }
.data-label { color: #718096; font-size: 13px; font-weight: 500; }
.data-value { color: #1a202c; font-size: 13px; font-weight: 500; text-align: right; max-width: 60%; word-break: break-word; }
.ip-hero { background: linear-gradient(135deg, #ebf8ff 0%, #e6f4ff 100%); border: 1px solid rgba(49,130,206,0.2); border-radius: 20px; padding: 30px; text-align: center; margin-bottom: 22px; }
.ip-address { font-size: 2rem; font-weight: 700; color: #2b6cb0; letter-spacing: 2px; font-family: 'Courier New', monospace; }
.ip-location { font-size: 1rem; color: #718096; margin-top: 6px; }
.ip-flag { font-size: 3rem; margin-bottom: 6px; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; margin: 4px; }
.badge-danger  { background: rgba(254,215,215,0.8); color: #c53030; border: 1px solid rgba(254,215,215,1); }
.badge-success { background: rgba(198,246,213,0.8); color: #276749; border: 1px solid rgba(198,246,213,1); }
.badge-neutral { background: rgba(226,232,240,0.8); color: #4a5568; border: 1px solid rgba(226,232,240,1); }
.badge-warn    { background: rgba(255,245,199,0.8); color: #744210; border: 1px solid rgba(255,245,199,1); }
.threat-box { border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; border: 1px solid; font-weight: 500; }
.threat-safe    { background: rgba(198,246,213,0.3); border-color: #68d391; color: #276749; }
.threat-warning { background: rgba(255,245,199,0.5); border-color: #ecc94b; color: #744210; }
.threat-danger  { background: rgba(254,215,215,0.5); border-color: #fc8181; color: #c53030; }
.stTextInput > div > div > input { background: #fff !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; color: #1a202c !important; font-family: 'Courier New', monospace !important; font-size: 15px !important; }
.stButton > button { background: linear-gradient(135deg, #3182ce, #2b6cb0) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 15px !important; padding: 12px 28px !important; }
.history-item { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 13px; }
.history-ip   { color: #2b6cb0; font-weight: 600; font-family: monospace; }
.history-loc  { color: #718096; font-size: 12px; }
.history-time { color: #a0aec0; font-size: 11px; float: right; }
.private-ip-box { background: rgba(255,245,199,0.5); border: 1px solid #ecc94b; border-radius: 12px; padding: 16px 20px; color: #744210; font-weight: 500; }
.precision-badge { background: rgba(49,130,206,0.1); border: 1px solid rgba(49,130,206,0.3); color: #2b6cb0; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Constants & Helpers
# ─────────────────────────────────────────────────────────────────────────────
PRIVATE_RANGES = [
    "10.", "192.168.", "127.", "::1", "0.0.0.0",
    "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.",
    "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.",
    "172.28.", "172.29.", "172.30.", "172.31.", "169.254.", "fc00:", "fd", "fe80:",
]

COUNTRY_NAMES_VI = {
    "VN": "Việt Nam", "US": "Hoa Kỳ", "CN": "Trung Quốc", "JP": "Nhật Bản",
    "KR": "Hàn Quốc", "SG": "Singapore", "TH": "Thái Lan", "GB": "Anh",
    "DE": "Đức", "FR": "Pháp", "AU": "Úc", "CA": "Canada", "IN": "Ấn Độ",
    "RU": "Nga", "BR": "Brazil", "NL": "Hà Lan", "SE": "Thụy Điển",
    "MY": "Malaysia", "ID": "Indonesia", "PH": "Philippines",
}


def get_flag_emoji(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🌐"
    try:
        return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in country_code.upper())
    except Exception:
        return "🌐"


def is_private_ip(ip: str) -> bool:
    stripped = ip.strip().lower()
    return any(stripped.startswith(p) for p in PRIVATE_RANGES)


def is_valid_ip(ip: str) -> bool:
    """Check if string looks like an IP or domain"""
    ip = ip.strip()
    # IPv4
    ipv4 = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
    # IPv6
    ipv6 = re.compile(r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$")
    # Domain
    domain = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")
    return bool(ipv4.match(ip) or ipv6.match(ip) or domain.match(ip))


def reverse_dns(ip: str) -> str:
    """Reverse DNS lookup"""
    try:
        return socket.gethostbyaddr(ip.strip())[0]
    except Exception:
        return "Không có PTR record"


def get_my_ip() -> str | None:
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=6)
        r.raise_for_status()
        return r.json().get("ip")
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Dual-API Lookup
# ─────────────────────────────────────────────────────────────────────────────
def lookup_ipinfo(ip_or_domain: str) -> dict:
    """Primary source: ipinfo.io — mức phường/quận, miễn phí 50k req/tháng"""
    target = "me" if not ip_or_domain.strip() else ip_or_domain.strip()
    url = f"https://ipinfo.io/{target}/json"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "bogon" in data or data.get("status") == "fail":
            return {}
        # Parse tọa độ: ipinfo trả về "lat,lon"
        lat, lon = None, None
        if data.get("loc"):
            parts = data["loc"].split(",")
            if len(parts) == 2:
                try:
                    lat, lon = float(parts[0]), float(parts[1])
                except ValueError:
                    pass
        if not data.get("ip"):
            return {}
        return {
            "source":      "ipinfo.io",
            "query":       data.get("ip", target),
            "country":     data.get("country", "N/A"),
            "country_name": COUNTRY_NAMES_VI.get(data.get("country", ""), data.get("country", "N/A")),
            "region":      data.get("region", "N/A"),
            "city":        data.get("city", "N/A"),
            "postal":      data.get("postal", "N/A"),
            "timezone":    data.get("timezone", "N/A"),
            "org":         data.get("org", "N/A"),
            "hostname":    data.get("hostname", ""),
            "lat":         lat,
            "lon":         lon,
            "precision":   "Phường/Quận cấp (ipinfo.io)",
        }
    except Exception:
        return {}


def lookup_ipapicom(ip_or_domain: str, retries: int = 2) -> dict:
    """Secondary source: ip-api.com — threat/proxy/mobile flags + extra data"""
    fields = (
        "status,message,query,continent,country,countryCode,region,"
        "regionName,city,district,zip,lat,lon,timezone,isp,org,as,"
        "asname,mobile,proxy,hosting"
    )
    target = ip_or_domain.strip()
    url = f"http://ip-api.com/json/{target}?fields={fields}"
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "fail" and "rate" in str(data.get("message", "")).lower():
                if attempt < retries:
                    time.sleep(3)
                    continue
            return data
        except requests.exceptions.RequestException:
            pass
    return {"status": "fail", "message": "Rate limited or connection error"}


def lookup_ip(ip_or_domain: str) -> dict:
    """Merge data from ipinfo (precise coords) + ip-api (threat flags)"""
    target = ip_or_domain.strip()

    # Primary: ipinfo.io
    ipinfo_data = lookup_ipinfo(target)

    # Secondary: ip-api.com (for proxy/mobile/hosting flags and city backup)
    ipapidata = lookup_ipapicom(target)

    if not ipinfo_data and ipapidata.get("status") != "success":
        return {"status": "fail", "message": "Không thể tra cứu IP này từ cả hai nguồn."}

    # Merge: ipinfo is primary, fill gaps from ip-api
    api = ipapidata if ipapidata.get("status") == "success" else {}

    ip_query = ipinfo_data.get("query") or api.get("query", target)
    lat = ipinfo_data.get("lat") or api.get("lat")
    lon = ipinfo_data.get("lon") or api.get("lon")
    country_code = ipinfo_data.get("country") or api.get("countryCode", "")

    return {
        "status":       "success",
        "source":       ipinfo_data.get("source", "ip-api.com"),
        "precision":    ipinfo_data.get("precision", "Thành phố cấp (ip-api.com)"),
        "query":        ip_query,
        # Location (prefer ipinfo)
        "country":      COUNTRY_NAMES_VI.get(country_code, api.get("country", "N/A")) if api else ipinfo_data.get("country_name", "N/A"),
        "countryCode":  country_code,
        "continent":    api.get("continent", "N/A"),
        "region":       ipinfo_data.get("region") or api.get("regionName", "N/A"),
        "city":         ipinfo_data.get("city") or api.get("city", "N/A"),
        "district":     api.get("district", ""),
        "zip":          ipinfo_data.get("postal") or api.get("zip", ""),
        "timezone":     ipinfo_data.get("timezone") or api.get("timezone", "N/A"),
        "lat":          lat,
        "lon":          lon,
        # Network (prefer ip-api for ISP details, ipinfo for org)
        "isp":          api.get("isp") or ipinfo_data.get("org", "N/A"),
        "org":          ipinfo_data.get("org") or api.get("org", "N/A"),
        "asn":          api.get("as") or "",
        "asname":       api.get("asname", ""),
        "hostname":     ipinfo_data.get("hostname", ""),
        # Threat flags from ip-api
        "proxy":        api.get("proxy"),
        "mobile":       api.get("mobile"),
        "hosting":      api.get("hosting"),
    }


def add_to_history(data: dict):
    entry = {
        "ip":           data.get("query", "N/A"),
        "city":         data.get("city", "N/A"),
        "country":      data.get("country", "N/A"),
        "country_code": data.get("countryCode", ""),
        "lat":          data.get("lat"),
        "lon":          data.get("lon"),
        "timestamp":    datetime.now().strftime("%H:%M:%S"),
        "precision":    data.get("precision", ""),
    }
    if st.session_state.history and st.session_state.history[0]["ip"] == entry["ip"]:
        return
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:10]


def badge_html(flag, true_label, false_label, true_class="badge-danger", false_class="badge-success"):
    if flag is None:
        return '<span class="badge badge-neutral">❓ Không rõ</span>'
    return f'<span class="badge {true_class if flag else false_class}">{true_label if flag else false_label}</span>'


def build_folium_map(lat: float, lon: float, popup_text: str, ip_label: str = "") -> folium.Map:
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB dark_matter")
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"📍 {ip_label}" if ip_label else "📍 Nhấp để xem chi tiết",
        icon=folium.Icon(color="blue", icon="globe", prefix="fa"),
    ).add_to(m)
    folium.CircleMarker(
        location=[lat, lon], radius=22, color="#58a6ff",
        fill=True, fill_color="#58a6ff", fill_opacity=0.10, weight=1,
    ).add_to(m)
    return m


# ─────────────────────────────────────────────────────────────────────────────
# Threat Assessment
# ─────────────────────────────────────────────────────────────────────────────
def threat_assessment(data: dict) -> tuple[str, str, str]:
    """Returns (level, css_class, message)"""
    proxy = data.get("proxy")
    hosting = data.get("hosting")
    mobile = data.get("mobile")

    if proxy:
        return "HIGH", "threat-danger", "⚠️ Phát hiện Proxy / VPN / Tor — IP này đang dùng mạng ẩn danh"
    if hosting:
        return "MEDIUM", "threat-warning", "🖥️ Datacenter / Hosting — IP thuộc máy chủ/dịch vụ cloud"
    if mobile:
        return "LOW", "threat-safe", "📱 Mạng di động — IP từ thiết bị di động (3G/4G/5G)"
    return "SAFE", "threat-safe", "✅ Mạng bình thường — Không phát hiện dấu hiệu bất thường"


# ─────────────────────────────────────────────────────────────────────────────
# Render Result
# ─────────────────────────────────────────────────────────────────────────────
def render_result(data: dict):
    flag     = get_flag_emoji(data.get("countryCode", ""))
    ip_query = data.get("query", "N/A")
    city     = data.get("city", "N/A")
    country  = data.get("country", "N/A")
    region   = data.get("region", "N/A")
    lat      = data.get("lat")
    lon      = data.get("lon")
    prec     = data.get("precision", "")

    # ── Hero Banner ─────────────────────────────────────────────────────────
    prec_badge = f'<span class="precision-badge">📡 {prec}</span>' if prec else ""
    st.markdown(f"""
    <div class="ip-hero">
        <div class="ip-flag">{flag}</div>
        <div class="ip-address">{ip_query}</div>
        <div class="ip-location">🌍 {city}, {region}, {country}</div>
        <div style="margin-top:10px;">{prec_badge}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Threat Box ──────────────────────────────────────────────────────────
    level, cls, msg = threat_assessment(data)
    st.markdown(f'<div class="threat-box {cls}">{msg}</div>', unsafe_allow_html=True)

    # ── 3 Columns ───────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3, gap="medium")

    hostname = data.get("hostname", "") or "—"

    with col1:
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">🌍 Vị Trí Địa Lý</div>
            <div class="data-row"><span class="data-label">Quốc gia</span>
                <span class="data-value">{flag} {country} ({data.get('countryCode','N/A')})</span></div>
            <div class="data-row"><span class="data-label">Châu lục</span>
                <span class="data-value">{data.get('continent','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Tỉnh/Vùng</span>
                <span class="data-value">{region}</span></div>
            <div class="data-row"><span class="data-label">Thành phố</span>
                <span class="data-value">{city}</span></div>
            <div class="data-row"><span class="data-label">Quận/Huyện</span>
                <span class="data-value">{data.get('district','') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Mã bưu chính</span>
                <span class="data-value">{data.get('zip','') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Múi giờ</span>
                <span class="data-value">🕐 {data.get('timezone','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Tọa độ</span>
                <span class="data-value">{f'{lat:.4f}, {lon:.4f}' if lat and lon else 'N/A'}</span></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        proxy_badge  = badge_html(data.get("proxy"),   "🔒 Proxy/VPN Có",     "✅ Không có Proxy/VPN")
        mobile_badge = badge_html(data.get("mobile"),  "📱 Mạng di động",     "🖥️ Cáp/Broadband",
                                  true_class="badge-warn", false_class="badge-neutral")
        host_badge   = badge_html(data.get("hosting"), "🖥️ Hosting/Datacenter","🏠 Mạng gia đình",
                                  true_class="badge-warn", false_class="badge-neutral")
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">⚙️ Thông Tin Mạng</div>
            <div class="data-row"><span class="data-label">ISP/Nhà mạng</span>
                <span class="data-value">{data.get('isp','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Tổ chức</span>
                <span class="data-value">{data.get('org','N/A') or '—'}</span></div>
            <div class="data-row"><span class="data-label">ASN</span>
                <span class="data-value" style="font-family:monospace">{data.get('asn','') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Tên AS</span>
                <span class="data-value">{data.get('asname','') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Hostname (rDNS)</span>
                <span class="data-value" style="font-family:monospace;font-size:11px">{hostname}</span></div>
        </div>
        <div class="info-card">
            <div class="card-title">🔍 Cờ Phát Hiện</div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px;">
                {proxy_badge}{mobile_badge}{host_badge}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Reverse DNS lookup thêm
        with st.spinner("Reverse DNS..."):
            rdns = reverse_dns(ip_query)
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">🔄 Reverse DNS & Định Danh</div>
            <div class="data-row"><span class="data-label">IP Query</span>
                <span class="data-value" style="font-family:monospace">{ip_query}</span></div>
            <div class="data-row"><span class="data-label">Reverse DNS</span>
                <span class="data-value" style="font-family:monospace;font-size:11px">{rdns}</span></div>
            <div class="data-row"><span class="data-label">Nguồn dữ liệu</span>
                <span class="data-value">{data.get('source','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Độ chính xác vị trí</span>
                <span class="data-value">{prec}</span></div>
            <div class="data-row"><span class="data-label">Thời gian tra cứu</span>
                <span class="data-value">{datetime.now().strftime('%H:%M:%S')}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # ── Map Section ─────────────────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    has_coords = lat is not None and lon is not None and not (lat == 0.0 and lon == 0.0)

    if not has_coords:
        st.warning("⚠️ Không có tọa độ GPS. API không cung cấp vị trí cho IP này.")
    else:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lon:.6f}"

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2], gap="small")
        with col_btn1:
            st.markdown(
                f'<a href="{maps_url}" target="_blank" style="display:block;padding:10px 16px;'
                f'background:linear-gradient(135deg,#1a73e8,#1557b0);color:#fff;font-weight:700;'
                f'font-size:14px;border-radius:10px;text-decoration:none;text-align:center;">'
                f'🌍 Google Maps<br><span style="font-size:11px;opacity:0.8">{lat:.4f}, {lon:.4f}</span></a>',
                unsafe_allow_html=True)
        with col_btn2:
            osm_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=14"
            st.markdown(
                f'<a href="{osm_url}" target="_blank" style="display:block;padding:10px 16px;'
                f'background:linear-gradient(135deg,#4a90d9,#357abd);color:#fff;font-weight:700;'
                f'font-size:14px;border-radius:10px;text-decoration:none;text-align:center;">'
                f'🗺️ OpenStreetMap<br><span style="font-size:11px;opacity:0.8">{lat:.4f}, {lon:.4f}</span></a>',
                unsafe_allow_html=True)

        tab_folium, tab_google = st.tabs(["🔵 Bản đồ Tương tác (Folium)", "🗺️ Google Maps (Nhúng)"])

        with tab_folium:
            popup_html = (
                f"<b>IP:</b> {ip_query}<br>"
                f"<b>Vị trí:</b> {city}, {region}, {country}<br>"
                f"<b>ISP:</b> {data.get('isp','N/A')}<br>"
                f"<b>Tọa độ:</b> {lat:.6f}, {lon:.6f}<br>"
                f"<b>Độ chính xác:</b> {prec}"
            )
            m = build_folium_map(lat, lon, popup_html, ip_query)
            st_folium(m, width="100%", height=480, returned_objects=[])

        with tab_google:
            ts = int(time.time() * 1000)
            zoom_d = 6_000   # ~zoom 14 phường cấp
            embed_src = (
                f"https://www.google.com/maps/embed?pb="
                f"!1m18!1m12!1m3!1d{zoom_d}!2d{lon:.6f}!3d{lat:.6f}"
                f"!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1"
                f"!3m3!1m2!1s0x0%3A0x0!2z{lat:.4f},{lon:.4f}"
                f"!5e0!3m2!1svi!2svn!4v{ts}!5m2!1svi!2svn"
            )
            iframe_html = f"""
            <div style="border-radius:14px;overflow:hidden;box-shadow:0 6px 28px rgba(0,0,0,0.35);">
                <iframe src="{embed_src}" width="100%" height="480"
                    style="border:0;display:block;" allowfullscreen loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade"></iframe>
            </div>
            <p style="text-align:center;font-size:12px;color:#8b949e;margin-top:6px;">
                Bản đồ không hiển thị? <a href="{maps_url}" target="_blank" style="color:#58a6ff;">Mở Google Maps trực tiếp</a>
            </p>"""
            components.html(iframe_html, height=520, scrolling=False)

    # ── Raw JSON ─────────────────────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    with st.expander("🔬 Dữ liệu JSON gốc (Raw)", expanded=False):
        st.json(data)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🕵️ IP Detective v2")
    st.markdown("---")

    dark = st.toggle("🌙 Chế độ tối", value=st.session_state.dark_mode, key="theme_toggle")
    st.session_state.dark_mode = dark

    st.markdown("---")
    st.markdown("### ℹ️ Về Tool")
    st.markdown(
        "**Nguồn dữ liệu chính:**\n"
        "- 🌐 **[ipinfo.io](https://ipinfo.io)** — vị trí mức **phường/quận**\n"
        "- 🔍 **[ip-api.com](http://ip-api.com)** — Proxy/VPN flags\n\n"
        "⚠️ Không cần API key. Giới hạn ip-api.com: ~45 req/phút."
    )

    st.markdown("---")
    st.markdown("### 🕒 Lịch Sử Tra Cứu")

    if not st.session_state.history:
        st.caption("Chưa có tra cứu nào.")
    else:
        with st.expander(f"Lịch sử ({len(st.session_state.history)} mục)", expanded=True):
            for entry in st.session_state.history:
                flag = get_flag_emoji(entry.get("country_code", ""))
                st.markdown(f"""
                <div class="history-item">
                    <span class="history-time">{entry['timestamp']}</span>
                    <div class="history-ip">{entry['ip']}</div>
                    <div class="history-loc">{flag} {entry['city']}, {entry['country']}</div>
                </div>
                """, unsafe_allow_html=True)
            if st.button("🗑️ Xóa lịch sử", use_container_width=True):
                st.session_state.history = []
                st.rerun()

    st.markdown("---")
    st.caption("IP Detective v2.0 · Powered by ipinfo.io + ip-api.com")

# ─────────────────────────────────────────────────────────────────────────────
# Apply CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(DARK_CSS if st.session_state.dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Auto-detect IP on startup
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.auto_ip_loaded:
    with st.spinner("🔍 Đang tự động phát hiện IP của bạn..."):
        my_ip = get_my_ip()
    if my_ip:
        with st.spinner("📡 Đang tra cứu vị trí..."):
            auto_data = lookup_ip(my_ip)
        if auto_data.get("status") == "success":
            st.session_state.auto_ip_data = auto_data
            add_to_history(auto_data)
    st.session_state.auto_ip_loaded = True

# ─────────────────────────────────────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 🕵️ IP Detective — Tra Cứu Vị Trí IP Chính Xác")
st.markdown("Tra cứu vị trí địa lý mức **phường/quận** cho bất kỳ IPv4, IPv6 hoặc tên miền nào. Phát hiện Proxy/VPN, Reverse DNS, và phân tích bản đồ tương tác.")
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Input ────────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1], gap="small")
with col_input:
    ip_input = st.text_input(
        "Nhập IP hoặc tên miền",
        value="",
        placeholder="Ví dụ: 118.71.192.47  hoặc  google.com  (để trống = IP của bạn)",
        label_visibility="collapsed",
    )
with col_btn:
    lookup_clicked = st.button("🔍 Tra Cứu", use_container_width=True)

# ── Batch Mode ───────────────────────────────────────────────────────────────
batch_mode = st.checkbox("📋 Tra cứu hàng loạt — Nhập nhiều IP, tối đa 15 IP/lần")
batch_input = ""
if batch_mode:
    batch_input = st.text_area(
        "Mỗi IP / tên miền một dòng (tối đa 15):",
        height=160,
        placeholder="118.71.192.47\n113.23.42.57\n171.246.9.81\n...",
    )

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Processing
# ─────────────────────────────────────────────────────────────────────────────
if lookup_clicked:

    # ── Batch Mode ──────────────────────────────────────────────────────────
    if batch_mode:
        lines = [l.strip() for l in batch_input.splitlines() if l.strip()]
        if not lines:
            st.warning("⚠️ Vui lòng nhập ít nhất một IP.")
        else:
            MAX_BATCH = 15
            if len(lines) > MAX_BATCH:
                st.warning(f"⚠️ Giới hạn {MAX_BATCH} IP đầu tiên (bạn nhập {len(lines)}).")
                lines = lines[:MAX_BATCH]

            st.markdown(f"### 📋 Kết Quả Hàng Loạt — {len(lines)} IP")
            progress_bar = st.progress(0, text="Đang bắt đầu...")
            rows = []
            errors = []

            for idx, target in enumerate(lines):
                progress_bar.progress(
                    (idx + 1) / len(lines),
                    text=f"Tra cứu {idx+1}/{len(lines)}: {target}"
                )

                if is_private_ip(target):
                    errors.append({"ip": target, "error": "IP Private / Nội bộ"})
                    rows.append({"IP/Domain": target, "Trạng thái": "⚠️ Private",
                        "Quốc gia": "—", "Thành phố": "—", "ISP": "—",
                        "Proxy/VPN": "—", "Mobile": "—", "Hosting": "—",
                        "Lat": "—", "Lon": "—", "Độ chính xác": "—",
                        "Google Maps": "—"})
                    continue

                data = lookup_ip(target)
                if data.get("status") == "success":
                    add_to_history(data)
                    flag = get_flag_emoji(data.get("countryCode", ""))
                    _lat = data.get("lat")
                    _lon = data.get("lon")
                    maps_link = (
                        f"https://www.google.com/maps/search/?api=1&query={_lat:.6f},{_lon:.6f}"
                        if _lat is not None and _lon is not None else "N/A"
                    )
                    rows.append({
                        "IP/Domain":    data.get("query", target),
                        "Trạng thái":   "✅ Thành công",
                        "Quốc gia":     f"{flag} {data.get('country','N/A')}",
                        "Thành phố":    data.get("city", "N/A"),
                        "ISP":          data.get("isp", "N/A"),
                        "Proxy/VPN":    "🔒 Có" if data.get("proxy") else "✅ Không",
                        "Mobile":       "📱 Có" if data.get("mobile") else "🖥️ Không",
                        "Hosting":      "☁️ Có" if data.get("hosting") else "🏠 Không",
                        "Lat":          round(_lat, 6) if _lat else "N/A",
                        "Lon":          round(_lon, 6) if _lon else "N/A",
                        "Độ chính xác": data.get("precision", "N/A"),
                        "Google Maps":  maps_link,
                    })
                else:
                    errors.append({"ip": target, "error": data.get("message", "Lỗi")})
                    rows.append({"IP/Domain": target, "Trạng thái": "❌ Thất bại",
                        "Quốc gia": "—", "Thành phố": "—", "ISP": data.get("message","Lỗi"),
                        "Proxy/VPN": "—", "Mobile": "—", "Hosting": "—",
                        "Lat": "—", "Lon": "—", "Độ chính xác": "—", "Google Maps": "—"})

                if idx < len(lines) - 1:
                    time.sleep(1.5)

            progress_bar.empty()
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=min(100 + 40 * len(rows), 480))

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Tải xuống CSV",
                data=csv_bytes,
                file_name=f"ip_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            if errors:
                with st.expander("❌ Tra cứu thất bại", expanded=True):
                    for e in errors:
                        st.error(f"**{e['ip']}** — {e['error']}")

    # ── Single IP ────────────────────────────────────────────────────────────
    else:
        target = ip_input.strip()

        if target and is_private_ip(target):
            st.markdown("""
            <div class="private-ip-box">
                ⚠️ <b>IP Private / Nội bộ</b><br>
                IP này thuộc dải địa chỉ nội bộ hoặc loopback. Không có dữ liệu geolocation.
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner("📡 Đang tra cứu từ ipinfo.io + ip-api.com..."):
                data = lookup_ip(target)

            if data.get("status") == "success":
                add_to_history(data)
                render_result(data)
                st.session_state.auto_ip_data = data
            else:
                msg = data.get("message", "Lỗi không xác định")
                st.error(f"❌ **Tra cứu thất bại:** {msg}")
                if "rate" in msg.lower():
                    st.info("💡 Vượt giới hạn API. Chờ 60 giây rồi thử lại.")

# ── Display auto-detected IP on first load ────────────────────────────────────
elif not lookup_clicked and st.session_state.auto_ip_data is not None:
    auto_data = st.session_state.auto_ip_data
    my_ip  = auto_data.get("query", "")
    flag   = get_flag_emoji(auto_data.get("countryCode", ""))
    st.info(
        f"{flag} **IP của bạn:** `{my_ip}` — "
        f"{auto_data.get('city','N/A')}, {auto_data.get('country','N/A')} "
        f"| Độ chính xác: {auto_data.get('precision','')}"
    )
    render_result(auto_data)

"""
IP Detective - Công Cụ Tra Cứu Vị Trí IP Nâng Cao
Ứng dụng web Streamlit chuyên nghiệp để tra cứu geolocation IP.
"""

import time
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
    page_title="IP Detective - Tra Cứu Vị Trí IP",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []          # danh sách dict, tối đa 10 tra cứu gần nhất

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "auto_ip_loaded" not in st.session_state:
    st.session_state.auto_ip_loaded = False

if "auto_ip_data" not in st.session_state:
    st.session_state.auto_ip_data = None

# ─────────────────────────────────────────────────────────────────────────────
# Theme CSS
# ─────────────────────────────────────────────────────────────────────────────
DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #e6edf3;
    }

    .info-card {
        background: rgba(22, 27, 34, 0.95);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        backdrop-filter: blur(12px);
    }

    .card-title {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #58a6ff;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .data-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(48, 54, 61, 0.5);
    }
    .data-row:last-child { border-bottom: none; }

    .data-label {
        color: #8b949e;
        font-size: 13px;
        font-weight: 500;
    }

    .data-value {
        color: #e6edf3;
        font-size: 14px;
        font-weight: 500;
        text-align: right;
    }

    .ip-hero {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .ip-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(88,166,255,0.05) 0%, transparent 70%);
    }
    .ip-address {
        font-size: 2.2rem;
        font-weight: 700;
        color: #58a6ff;
        letter-spacing: 2px;
        font-family: 'Courier New', monospace;
    }
    .ip-location {
        font-size: 1.1rem;
        color: #8b949e;
        margin-top: 8px;
    }
    .ip-flag {
        font-size: 3rem;
        margin-bottom: 8px;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        margin: 4px;
    }
    .badge-danger  { background: rgba(255,80,80,0.15); color: #ff6b6b; border: 1px solid rgba(255,80,80,0.3); }
    .badge-success { background: rgba(56,211,159,0.15); color: #3dd68c; border: 1px solid rgba(56,211,159,0.3); }
    .badge-neutral { background: rgba(139,148,158,0.15); color: #8b949e; border: 1px solid rgba(139,148,158,0.3); }
    .badge-warn    { background: rgba(255,180,0,0.15);  color: #ffb400; border: 1px solid rgba(255,180,0,0.3); }

    [data-testid="stSidebar"] {
        background: rgba(13, 17, 23, 0.98) !important;
        border-right: 1px solid rgba(48,54,61,0.8);
    }

    .stTextInput > div > div > input {
        background: rgba(22,27,34,0.9) !important;
        border: 1px solid rgba(48,54,61,0.8) !important;
        border-radius: 10px !important;
        color: #e6edf3 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 15px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #238636, #2ea043) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 28px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 15px rgba(46,160,67,0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(46,160,67,0.45) !important;
    }

    .history-item {
        background: rgba(22,27,34,0.7);
        border: 1px solid rgba(48,54,61,0.6);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .history-ip   { color: #58a6ff; font-weight: 600; font-family: monospace; }
    .history-loc  { color: #8b949e; font-size: 12px; }
    .history-time { color: #484f58; font-size: 11px; float: right; }

    .section-divider {
        border: none;
        border-top: 1px solid rgba(48,54,61,0.7);
        margin: 28px 0;
    }

    .private-ip-box {
        background: rgba(255,180,0,0.1);
        border: 1px solid rgba(255,180,0,0.3);
        border-radius: 12px;
        padding: 16px 20px;
        color: #ffb400;
        font-weight: 500;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #484f58; }
</style>
"""

LIGHT_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 50%, #f0f4f8 100%);
        color: #1a202c;
    }

    .info-card {
        background: rgba(255,255,255,0.95);
        border: 1px solid rgba(226,232,240,0.8);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }

    .card-title {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #3182ce;
        margin-bottom: 16px;
    }

    .data-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(226,232,240,0.6);
    }
    .data-row:last-child { border-bottom: none; }

    .data-label { color: #718096; font-size: 13px; font-weight: 500; }
    .data-value { color: #1a202c; font-size: 14px; font-weight: 500; text-align: right; }

    .ip-hero {
        background: linear-gradient(135deg, #ebf8ff 0%, #e6f4ff 100%);
        border: 1px solid rgba(49,130,206,0.2);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        margin-bottom: 24px;
    }
    .ip-address { font-size: 2.2rem; font-weight: 700; color: #2b6cb0; letter-spacing: 2px; font-family: 'Courier New', monospace; }
    .ip-location { font-size: 1.1rem; color: #718096; margin-top: 8px; }
    .ip-flag { font-size: 3rem; margin-bottom: 8px; }

    .badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; margin: 4px; }
    .badge-danger  { background: rgba(254,215,215,0.8); color: #c53030; border: 1px solid rgba(254,215,215,1); }
    .badge-success { background: rgba(198,246,213,0.8); color: #276749; border: 1px solid rgba(198,246,213,1); }
    .badge-neutral { background: rgba(226,232,240,0.8); color: #4a5568; border: 1px solid rgba(226,232,240,1); }
    .badge-warn    { background: rgba(255,245,199,0.8); color: #744210; border: 1px solid rgba(255,245,199,1); }

    .stTextInput > div > div > input {
        background: #fff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        color: #1a202c !important;
        font-family: 'Courier New', monospace !important;
        font-size: 15px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #3182ce, #2b6cb0) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 28px !important;
    }

    .history-item { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 13px; }
    .history-ip   { color: #2b6cb0; font-weight: 600; font-family: monospace; }
    .history-loc  { color: #718096; font-size: 12px; }
    .history-time { color: #a0aec0; font-size: 11px; float: right; }

    .private-ip-box { background: rgba(255,245,199,0.5); border: 1px solid #ecc94b; border-radius: 12px; padding: 16px 20px; color: #744210; font-weight: 500; }
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

PRIVATE_RANGES = [
    "10.", "192.168.", "127.", "::1", "0.0.0.0",
    "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.",
    "172.24.", "172.25.", "172.26.", "172.27.",
    "172.28.", "172.29.", "172.30.", "172.31.",
    "169.254.", "fc00:", "fd", "fe80:",
]


def get_flag_emoji(country_code: str) -> str:
    """Chuyển mã quốc gia ISO 3166-1 alpha-2 thành emoji cờ."""
    if not country_code or len(country_code) != 2:
        return "🌐"
    try:
        return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in country_code.upper())
    except Exception:
        return "🌐"


def is_private_ip(ip: str) -> bool:
    """Kiểm tra xem IP có thuộc dải private/reserved không."""
    stripped = ip.strip().lower()
    return any(stripped.startswith(prefix) for prefix in PRIVATE_RANGES)


def get_my_ip() -> str | None:
    """Lấy địa chỉ IP công khai của người dùng qua ipify."""
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=6)
        r.raise_for_status()
        return r.json().get("ip")
    except Exception:
        return None


def lookup_ip(ip_or_domain: str) -> dict:
    """Gọi ip-api.com và trả về dict JSON đã phân tích."""
    fields = (
        "status,message,query,continent,country,countryCode,region,"
        "regionName,city,district,zip,lat,lon,timezone,isp,org,as,"
        "asname,mobile,proxy,hosting"
    )
    url = f"http://ip-api.com/json/{ip_or_domain.strip()}?fields={fields}"
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return {"status": "fail", "message": "Yêu cầu quá thời gian chờ. Vui lòng thử lại."}
    except requests.exceptions.ConnectionError:
        return {"status": "fail", "message": "Lỗi kết nối. Kiểm tra lại đường truyền internet."}
    except requests.exceptions.JSONDecodeError:
        return {"status": "fail", "message": "Phản hồi không hợp lệ từ API (lỗi JSON decode)."}
    except requests.exceptions.RequestException as e:
        return {"status": "fail", "message": f"Lỗi yêu cầu: {str(e)}"}


def add_to_history(data: dict):
    """Lưu kết quả tra cứu vào lịch sử phiên (tối đa 10 mục)."""
    entry = {
        "ip":           data.get("query", "N/A"),
        "city":         data.get("city", "N/A"),
        "country":      data.get("country", "N/A"),
        "country_code": data.get("countryCode", ""),
        "lat":          data.get("lat"),
        "lon":          data.get("lon"),
        "timestamp":    datetime.now().strftime("%H:%M:%S"),
    }
    # Tránh thêm trùng lặp liên tiếp
    if st.session_state.history and st.session_state.history[0]["ip"] == entry["ip"]:
        return
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:10]


def badge_html(flag: bool | None, true_label: str, false_label: str,
               true_class: str = "badge-danger", false_class: str = "badge-success") -> str:
    """Hiển thị badge màu dựa trên giá trị boolean."""
    if flag is None:
        return '<span class="badge badge-neutral">❓ Không rõ</span>'
    if flag:
        return f'<span class="badge {true_class}">{true_label}</span>'
    return f'<span class="badge {false_class}">{false_label}</span>'


def build_folium_map(lat: float, lon: float, popup_text: str) -> folium.Map:
    """Tạo bản đồ Folium dark-theme tại tọa độ lat/lon."""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=10,
        tiles="CartoDB dark_matter",
    )
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_text, max_width=280),
        tooltip="📍 Nhấp để xem chi tiết",
        icon=folium.Icon(color="blue", icon="globe", prefix="fa"),
    ).add_to(m)
    folium.CircleMarker(
        location=[lat, lon],
        radius=18,
        color="#58a6ff",
        fill=True,
        fill_color="#58a6ff",
        fill_opacity=0.12,
        weight=1,
    ).add_to(m)
    return m


# ─────────────────────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_result(data: dict):
    """Hiển thị kết quả tra cứu geolocation thành công."""
    flag      = get_flag_emoji(data.get("countryCode", ""))
    ip_query  = data.get("query", "N/A")
    city      = data.get("city", "N/A")
    country   = data.get("country", "N/A")
    region    = data.get("regionName", "N/A")

    # ── Banner IP ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="ip-hero">
        <div class="ip-flag">{flag}</div>
        <div class="ip-address">{ip_query}</div>
        <div class="ip-location">🌍 {city}, {region}, {country}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hai cột thông tin ────────────────────────────────────────────────────
    col_left, col_right = st.columns(2, gap="medium")

    # Trái: thông tin vị trí
    with col_left:
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">🌍 Thông Tin Vị Trí</div>
            <div class="data-row"><span class="data-label">IP / Query</span>
                <span class="data-value" style="font-family:monospace">{data.get('query','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Châu lục</span>
                <span class="data-value">{data.get('continent','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Quốc gia</span>
                <span class="data-value">{flag} {data.get('country','N/A')} ({data.get('countryCode','N/A')})</span></div>
            <div class="data-row"><span class="data-label">Vùng / Tỉnh</span>
                <span class="data-value">{data.get('regionName','N/A')} ({data.get('region','N/A')})</span></div>
            <div class="data-row"><span class="data-label">Thành phố</span>
                <span class="data-value">{data.get('city','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Quận / Huyện</span>
                <span class="data-value">{data.get('district','N/A') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Mã bưu chính (ZIP)</span>
                <span class="data-value">{data.get('zip','N/A') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Múi giờ (Timezone)</span>
                <span class="data-value">🕐 {data.get('timezone','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Tọa độ</span>
                <span class="data-value">{data.get('lat','N/A')}, {data.get('lon','N/A')}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # Phải: thông tin kỹ thuật / mạng
    with col_right:
        proxy_flag  = data.get("proxy")
        mobile_flag = data.get("mobile")
        host_flag   = data.get("hosting")

        proxy_badge  = badge_html(proxy_flag,  "🔒 Phát hiện Proxy/VPN", "✅ Không có Proxy/VPN")
        mobile_badge = badge_html(mobile_flag, "📱 Mạng di động",        "🖥️ Cáp / Broadband",
                                  true_class="badge-warn", false_class="badge-neutral")
        host_badge   = badge_html(host_flag,   "🖥️ Hosting / Datacenter", "🏠 Mạng gia đình",
                                  true_class="badge-warn", false_class="badge-neutral")

        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">⚙️ Thông Tin Mạng & Kỹ Thuật</div>
            <div class="data-row"><span class="data-label">ISP (Nhà mạng)</span>
                <span class="data-value">{data.get('isp','N/A')}</span></div>
            <div class="data-row"><span class="data-label">Tổ chức (Org)</span>
                <span class="data-value">{data.get('org','N/A') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Số AS (ASN)</span>
                <span class="data-value" style="font-family:monospace">{data.get('as','N/A') or '—'}</span></div>
            <div class="data-row"><span class="data-label">Tên AS</span>
                <span class="data-value">{data.get('asname','N/A') or '—'}</span></div>
        </div>
        <div class="info-card">
            <div class="card-title">🔍 Cờ Phát Hiện (Detection Flags)</div>
            <div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">
                {proxy_badge}
                {mobile_badge}
                {host_badge}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Phần bản đồ ───────────────────────────────────────────────────────────
    lat = data.get("lat")
    lon = data.get("lon")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    has_coords = (
        lat is not None and lon is not None
        and not (lat == 0.0 and lon == 0.0)
    )

    if not has_coords:
        st.warning(
            "⚠️ **Không có tọa độ chính xác.** "
            "API có thể chỉ trả về vị trí xấp xỉ (trung tâm thành phố / quốc gia)."
        )
    else:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

        # Nút mở Google Maps
        st.markdown(
            f"""
            <div style="margin-bottom:18px;">
                <a href="{maps_url}" target="_blank" style="
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    padding: 13px 26px;
                    background: linear-gradient(135deg, #1a73e8, #1557b0);
                    color: #fff;
                    font-weight: 700;
                    font-size: 15px;
                    border-radius: 12px;
                    text-decoration: none;
                    box-shadow: 0 4px 18px rgba(26,115,232,0.35);
                    transition: all 0.2s ease;
                    font-family: Inter, sans-serif;
                ">
                    🌍 Xem vị trí trên Google Maps
                    <span style="font-size:11px;opacity:0.8;">({lat}, {lon})</span>
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Hai tab bản đồ: Google Maps Embed | OpenStreetMap (Folium)
        tab_google, tab_folium = st.tabs(["🗺️ Google Maps (Nhúng)", "🔵 OpenStreetMap (Folium)"])

        with tab_google:
            ts = int(time.time() * 1000)
            if data.get("zip") or data.get("district"):
                zoom_d = 8_000      # phóng to cấp phường/quận (~zoom 14)
            elif data.get("city"):
                zoom_d = 40_000     # cấp thành phố (~zoom 12)
            else:
                zoom_d = 500_000    # cấp quốc gia (~zoom 6)

            embed_src = (
                f"https://www.google.com/maps/embed?pb="
                f"!1m18!1m12!1m3!1d{zoom_d}!2d{lon}!3d{lat}"
                f"!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1"
                f"!3m3!1m2!1s0x0%3A0x0!2z{lat},{lon}"
                f"!5e0!3m2!1svi!2svn!4v{ts}!5m2!1svi!2svn"
            )

            iframe_html = f"""
            <div style="border-radius:14px;overflow:hidden;
                        box-shadow:0 6px 28px rgba(0,0,0,0.35);
                        border:1px solid rgba(88,166,255,0.2);">
                <iframe
                    src="{embed_src}"
                    width="100%"
                    height="500"
                    style="border:0;display:block;"
                    allowfullscreen
                    loading="lazy"
                    referrerpolicy="no-referrer-when-downgrade">
                </iframe>
            </div>
            <p style="text-align:center;font-size:12px;color:#8b949e;margin-top:8px;">
                Bản đồ không hiển thị?
                <a href="{maps_url}" target="_blank"
                   style="color:#58a6ff;">Nhấp vào đây để mở Google Maps trực tiếp</a>.
            </p>
            """
            components.html(iframe_html, height=540, scrolling=False)

        with tab_folium:
            popup_html = (
                f"<b>IP:</b> {ip_query}<br>"
                f"<b>Vị trí:</b> {city}, {country}<br>"
                f"<b>ISP:</b> {data.get('isp','N/A')}<br>"
                f"<b>Tọa độ:</b> {lat}, {lon}"
            )
            m = build_folium_map(lat, lon, popup_html)
            st_folium(m, width="100%", height=460, returned_objects=[])

    # ── Raw JSON ──────────────────────────────────────────────────────────────
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    with st.expander("🔬 Phản hồi JSON gốc (Raw JSON)", expanded=False):
        st.json(data)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🕵️ IP Detective")
    st.markdown("---")

    # Chuyển đổi giao diện sáng/tối
    dark = st.toggle("🌙 Chế độ tối (Dark Mode)", value=st.session_state.dark_mode, key="theme_toggle")
    st.session_state.dark_mode = dark

    st.markdown("---")
    st.markdown("### ℹ️ Giới thiệu")
    st.markdown(
        "Sử dụng **[ip-api.com](http://ip-api.com)** — miễn phí, "
        "không cần API key.\n\n"
        "⚠️ **Giới hạn:** ~45 yêu cầu/phút."
    )

    st.markdown("---")
    st.markdown("### 🕒 Lịch Sử Tra Cứu")

    if not st.session_state.history:
        st.caption("Chưa có tra cứu nào. Hãy thử tra cứu một IP!")
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
    st.caption("IP Detective v1.0 · Xây dựng bằng Streamlit")

# ─────────────────────────────────────────────────────────────────────────────
# Apply Theme CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(DARK_CSS if st.session_state.dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tự động phát hiện IP người dùng khi khởi động lần đầu
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.auto_ip_loaded:
    with st.spinner("🔍 Đang tự động phát hiện địa chỉ IP của bạn..."):
        my_ip = get_my_ip()
    if my_ip:
        with st.spinner("📡 Đang lấy dữ liệu vị trí địa lý..."):
            auto_data = lookup_ip(my_ip)
        if auto_data.get("status") == "success":
            st.session_state.auto_ip_data = auto_data
            add_to_history(auto_data)
    st.session_state.auto_ip_loaded = True

# ─────────────────────────────────────────────────────────────────────────────
# Giao Diện Chính
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 🕵️ Công Cụ Tra Cứu Vị Trí IP")
st.markdown("Khám phá thông tin vị trí địa lý và mạng chi tiết cho bất kỳ địa chỉ IPv4, IPv6 hoặc tên miền nào.")
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── Ô nhập liệu ───────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([4, 1], gap="small")

with col_input:
    ip_input = st.text_input(
        "Nhập địa chỉ IP hoặc tên miền",
        value="",
        placeholder="Ví dụ: 8.8.8.8  hoặc  example.com  (để trống để dùng IP của bạn)",
        label_visibility="collapsed",
    )

with col_btn:
    lookup_clicked = st.button("🔍 Tra Cứu", use_container_width=True)

# ── Chế độ Batch ──────────────────────────────────────────────────────────────
batch_mode = st.checkbox("📋 Chế độ hàng loạt (Batch) — tra cứu nhiều IP cùng lúc, tối đa 10 IP/lần")

batch_input = ""
if batch_mode:
    batch_input = st.text_area(
        "Nhập mỗi IP / tên miền trên một dòng (tối đa 10):",
        height=160,
        placeholder="8.8.8.8\n1.1.1.1\nexample.com\n...",
    )

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Xử Lý Nút Tra Cứu
# ─────────────────────────────────────────────────────────────────────────────
if lookup_clicked:

    # ── Chế độ Batch ──────────────────────────────────────────────────────────
    if batch_mode:
        lines = [l.strip() for l in batch_input.splitlines() if l.strip()]

        if not lines:
            st.warning("⚠️ Vui lòng nhập ít nhất một IP hoặc tên miền vào ô batch.")
        else:
            if len(lines) > 10:
                st.warning(f"⚠️ Giới hạn 10 IP đầu tiên (bạn đã nhập {len(lines)} dòng).")
                lines = lines[:10]

            st.markdown(f"### 📋 Kết Quả Hàng Loạt — {len(lines)} tra cứu")
            progress_bar = st.progress(0, text="Đang bắt đầu tra cứu hàng loạt...")
            rows   = []
            errors = []

            for idx, target in enumerate(lines):
                progress_bar.progress(
                    (idx + 1) / len(lines),
                    text=f"Đang tra cứu {idx+1}/{len(lines)}: {target}"
                )

                if is_private_ip(target):
                    errors.append({"ip": target, "error": "IP Private / Dải địa chỉ nội bộ"})
                    rows.append({
                        "IP/Domain":        target,
                        "Trạng thái":       "⚠️ Private",
                        "Quốc gia":         "—",
                        "Thành phố":        "—",
                        "ISP":              "—",
                        "Proxy/VPN":        "—",
                        "Mobile":           "—",
                        "Lat":              "—",
                        "Lon":              "—",
                        "Google Maps Link": "—",
                    })
                    continue

                data = lookup_ip(target)
                if data.get("status") == "success":
                    add_to_history(data)
                    flag = get_flag_emoji(data.get("countryCode", ""))
                    _lat = data.get("lat")
                    _lon = data.get("lon")
                    _maps_link = (
                        f"https://www.google.com/maps/search/?api=1&query={_lat},{_lon}"
                        if _lat is not None and _lon is not None
                        else "N/A"
                    )
                    rows.append({
                        "IP/Domain":        data.get("query", target),
                        "Trạng thái":       "✅ Thành công",
                        "Quốc gia":         f"{flag} {data.get('country','N/A')}",
                        "Thành phố":        data.get("city", "N/A"),
                        "ISP":              data.get("isp", "N/A"),
                        "Proxy/VPN":        "🔒 Có" if data.get("proxy") else "✅ Không",
                        "Mobile":           "📱 Có" if data.get("mobile") else "🖥️ Không",
                        "Lat":              _lat if _lat is not None else "N/A",
                        "Lon":              _lon if _lon is not None else "N/A",
                        "Google Maps Link": _maps_link,
                    })
                else:
                    errors.append({"ip": target, "error": data.get("message", "Lỗi không xác định")})
                    rows.append({
                        "IP/Domain":        target,
                        "Trạng thái":       "❌ Thất bại",
                        "Quốc gia":         "—",
                        "Thành phố":        "—",
                        "ISP":              data.get("message", "Lỗi"),
                        "Proxy/VPN":        "—",
                        "Mobile":           "—",
                        "Lat":              "—",
                        "Lon":              "—",
                        "Google Maps Link": "—",
                    })

                # Chờ giữa các request để tránh vượt rate limit
                if idx < len(lines) - 1:
                    time.sleep(1.4)

            progress_bar.empty()

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=min(80 + 40 * len(rows), 400))

            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Tải xuống kết quả dạng CSV",
                data=csv_bytes,
                file_name=f"ip_lookup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            if errors:
                with st.expander("❌ Các tra cứu thất bại", expanded=True):
                    for e in errors:
                        st.error(f"**{e['ip']}** — {e['error']}")

    # ── Tra cứu đơn lẻ ───────────────────────────────────────────────────────
    else:
        target = ip_input.strip() or ""

        if target and is_private_ip(target):
            st.markdown("""
            <div class="private-ip-box">
                ⚠️ <b>Phát hiện IP Private / Dải địa chỉ nội bộ</b><br>
                Địa chỉ IP này thuộc dải private hoặc reserved (ví dụ: mạng LAN, loopback).
                Dữ liệu vị trí địa lý không khả dụng cho các IP nội bộ.
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner("📡 Đang lấy dữ liệu vị trí địa lý..."):
                data = lookup_ip(target)  # chuỗi rỗng → ip-api tự phát hiện IP

            if data.get("status") == "success":
                add_to_history(data)
                render_result(data)
                st.session_state.auto_ip_data = data
            else:
                msg = data.get("message", "Lỗi không xác định")
                st.error(f"❌ **Tra cứu thất bại:** {msg}")

                hints = ""
                if "private" in msg.lower():
                    hints = "Đây có vẻ là địa chỉ IP nội bộ (private)."
                elif "reserved" in msg.lower():
                    hints = "IP này thuộc dải reserved và không có dữ liệu vị trí công khai."
                elif "rate" in msg.lower():
                    hints = "Bạn đã vượt giới hạn rate (~45 req/phút). Chờ một chút rồi thử lại."
                if hints:
                    st.info(f"💡 {hints}")

# ─────────────────────────────────────────────────────────────────────────────
# Hiển thị kết quả tự phát hiện khi mới mở (chưa có tra cứu mới)
# ─────────────────────────────────────────────────────────────────────────────
elif not lookup_clicked and st.session_state.auto_ip_data is not None:
    auto_data = st.session_state.auto_ip_data
    my_ip     = auto_data.get("query", "")
    flag      = get_flag_emoji(auto_data.get("countryCode", ""))
    st.info(
        f"{flag} **IP được phát hiện của bạn:** `{my_ip}` — "
        f"{auto_data.get('city','N/A')}, {auto_data.get('country','N/A')}. "
        "Đang hiển thị thông tin vị trí của bạn bên dưới."
    )
    render_result(auto_data)

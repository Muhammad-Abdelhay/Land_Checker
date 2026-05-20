import streamlit as st
from shapely.geometry import Point, Polygon
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
import re

# ─────────────────────────────────────────────
# 1. إعدادات الصفحة وتهيئة المتغيرات
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="الحيز العمراني | نظام الاستعلام",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# تهيئة حالة زر الـ GPS
if "gps_active" not in st.session_state:
    st.session_state.gps_active = False

def toggle_gps():
    st.session_state.gps_active = not st.session_state.gps_active

# ─────────────────────────────────────────────
# 2. التنسيق (CSS) المحسّن
# ─────────────────────────────────────────────
# التنسيق الثابت
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@300;400;500;700;800&display=swap');

:root {
    --bg-deep:      #060d17;
    --bg-mid:       #0c1929;
    --bg-surface:   #101f33;
    --bg-card:      #122036;
    --accent-cyan:  #00d4ff;
    --accent-teal:  #00b89c;
    --accent-gold:  #f0b429;
    --accent-rose:  #ff5c7a;
    --accent-green: #00e5a0;
    --text-primary: #e8f4fd;
    --text-muted:   #7a9ab5;
    --border-glow:  rgba(0, 212, 255, 0.25);
    --border-soft:  rgba(255,255,255,0.06);
    --shadow-card:  0 8px 40px rgba(0,0,0,0.45);
    --radius-lg:    16px;
    --radius-md:    10px;
}

* { font-family: 'Cairo', 'Tajawal', sans-serif !important; direction: rtl; text-align: right; box-sizing: border-box; }

html, body, .stApp {
    background: var(--bg-deep) !important;
    color: var(--text-primary) !important;
}

.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

.hero-header {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #081626 0%, #0c2240 50%, #071520 100%);
    border: 1px solid var(--border-glow);
    border-radius: var(--radius-lg);
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -60%;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 300px;
    background: radial-gradient(ellipse, rgba(0,212,255,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.hero-header::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
}
.hero-badge {
    display: inline-block;
    background: rgba(0,212,255,0.1);
    border: 1px solid rgba(0,212,255,0.3);
    color: var(--accent-cyan);
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    padding: 0.3rem 1rem;
    border-radius: 50px;
    margin-bottom: 1rem;
    text-transform: uppercase;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 900;
    color: #fff;
    margin: 0 0 0.5rem;
    line-height: 1.2;
    text-shadow: 0 0 40px rgba(0,212,255,0.3);
}
.hero-title span { color: var(--accent-cyan); }
.hero-subtitle {
    font-size: 1rem;
    color: var(--text-muted);
    font-weight: 400;
    max-width: 560px;
    margin: 0 auto;
    line-height: 1.7;
}

.panel-card {
    background: var(--bg-card);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-lg);
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: var(--shadow-card);
    transition: border-color 0.3s;
}
.panel-card:hover { border-color: var(--border-glow); }

.panel-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid var(--border-soft);
}
.panel-title .icon {
    width: 34px; height: 34px;
    background: rgba(0,212,255,0.1);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.stat-chip {
    background: var(--bg-card);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-md);
    padding: 1rem;
    text-align: center;
    transition: all 0.3s;
}
.stat-chip:hover { border-color: var(--border-glow); transform: translateY(-2px); }
.stat-chip .stat-val {
    font-size: 1.5rem;
    font-weight: 900;
    color: var(--accent-cyan);
    line-height: 1;
    margin-bottom: 0.3rem;
}
.stat-chip .stat-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
}

.result-wrap {
    border-radius: var(--radius-lg);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    animation: slideDown 0.4s ease;
}
@keyframes slideDown {
    from { opacity: 0; transform: translateY(-16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.result-inside {
    background: linear-gradient(135deg, rgba(0,229,160,0.08), rgba(0,184,156,0.05));
    border: 1px solid rgba(0,229,160,0.35);
    box-shadow: 0 0 30px rgba(0,229,160,0.1), inset 0 1px 0 rgba(0,229,160,0.15);
}
.result-outside {
    background: linear-gradient(135deg, rgba(255,92,122,0.08), rgba(239,68,68,0.05));
    border: 1px solid rgba(255,92,122,0.35);
    box-shadow: 0 0 30px rgba(255,92,122,0.1), inset 0 1px 0 rgba(255,92,122,0.15);
}
.result-icon {
    font-size: 2.5rem;
    flex-shrink: 0;
    filter: drop-shadow(0 0 8px currentColor);
}
.result-text-main {
    font-size: 1.25rem;
    font-weight: 800;
    line-height: 1.3;
}
.result-inside .result-text-main { color: var(--accent-green); }
.result-outside .result-text-main { color: var(--accent-rose); }
.result-text-sub {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
}

.coords-card {
    background: rgba(0,212,255,0.04);
    border: 1px solid rgba(0,212,255,0.15);
    border-radius: var(--radius-md);
    padding: 0.9rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.2rem;
}
.coords-dot {
    width: 10px; height: 10px;
    background: var(--accent-cyan);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--accent-cyan);
    flex-shrink: 0;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { box-shadow: 0 0 5px var(--accent-cyan); }
    50%      { box-shadow: 0 0 14px var(--accent-cyan), 0 0 22px rgba(0,212,255,0.3); }
}
.coords-label { font-size: 0.78rem; color: var(--text-muted); }
.coords-value { font-size: 0.95rem; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }

div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    padding: 0.65rem 1rem !important;
    font-size: 0.95rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
    outline: none !important;
}

div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #0062cc, #00b4d8) !important;
    border: none !important;
    color: #fff !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    padding: 0.75rem !important;
    width: 100% !important;
    box-shadow: 0 4px 20px rgba(0,180,216,0.3) !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.03em !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    box-shadow: 0 6px 28px rgba(0,180,216,0.5) !important;
    transform: translateY(-3px) !important;
    background: linear-gradient(135deg, #0070e0, #00c8f0) !important;
}

div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.3rem !important;
}

div[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left: 3px solid var(--accent-gold) !important;
    background: rgba(240,180,41,0.07) !important;
}

div[data-testid="stSpinner"] p { color: var(--text-muted) !important; }

.placeholder-screen {
    height: 520px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 2px dashed rgba(0,212,255,0.12);
    border-radius: var(--radius-lg);
    background: var(--bg-card);
    transition: all 0.3s;
}
.placeholder-screen:hover { border-color: rgba(0,212,255,0.25); }
.placeholder-icon {
    font-size: 4.5rem;
    margin-bottom: 1rem;
    opacity: 0.4;
    filter: drop-shadow(0 0 12px rgba(0,212,255,0.4));
}
.placeholder-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
}
.placeholder-desc {
    font-size: 0.85rem;
    color: rgba(122,154,181,0.6);
    text-align: center;
    max-width: 280px;
    line-height: 1.7;
}

.divider {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 1.2rem 0;
    color: var(--text-muted);
    font-size: 0.8rem;
}
.divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-soft);
}

.map-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.8rem;
}
.map-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
}
.map-badge {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 50px;
    border: 1px solid;
}
.badge-live {
    color: var(--accent-green);
    border-color: rgba(0,229,160,0.3);
    background: rgba(0,229,160,0.07);
    animation: blinkBadge 2s infinite;
}
@keyframes blinkBadge {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.5; }
}

section[data-testid="stSidebar"] { background: var(--bg-mid) !important; }
</style>
""", unsafe_allow_html=True)

# تنسيق ديناميكي لزر الـ GPS حسب الحالة
if st.session_state.gps_active:
    btn_bg = "rgba(0, 229, 160, 0.15)"
    btn_border = "#00e5a0"
    btn_color = "#00e5a0"
    btn_hover_bg = "rgba(0, 229, 160, 0.25)"
    btn_shadow = "rgba(0, 229, 160, 0.3)"
else:
    btn_bg = "rgba(122, 154, 181, 0.1)"
    btn_border = "#7a9ab5"
    btn_color = "#7a9ab5"
    btn_hover_bg = "rgba(122, 154, 181, 0.2)"
    btn_shadow = "rgba(122, 154, 181, 0.25)"

st.markdown(f"""
<style>
div[data-testid="stButton"] > button {{
    background: {btn_bg} !important;
    border: 1px solid {btn_border} !important;
    color: {btn_color} !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.4rem !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}}
div[data-testid="stButton"] > button:hover {{
    background: {btn_hover_bg} !important;
    border-color: {btn_border} !important;
    box-shadow: 0 4px 16px {btn_shadow} !important;
    transform: translateY(-2px) !important;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. البيانات الأساسية
# ─────────────────────────────────────────────
BOUNDARY_POINTS_1 = [
    (30.722009, 31.295623), (30.721122, 31.295481),
    (30.721285, 31.294259), (30.722031, 31.294366),
    (30.722009, 31.295623)
]

BOUNDARY_POINTS_2 = [
    (30.725045, 31.294755), (30.730050, 31.302733), (30.730125, 31.302278), (30.729349, 31.302003),
    (30.729198, 31.302683), (30.729641, 31.302797), (30.729435, 31.303796), (30.727487, 31.303334),
    (30.727292, 31.304539), (30.726293, 31.304657), (30.726367, 31.304013), (30.725509, 31.303733),
    (30.725668, 31.303050), (30.725328, 31.302976), (30.725102, 31.302035), (30.724626, 31.301933),
    (30.724686, 31.300365), (30.723999, 31.300409), (30.724035, 31.299283), (30.724191, 31.299282),
    (30.724183, 31.299604), (30.724561, 31.299566), (30.724542, 31.298039), (30.724166, 31.298057),
    (30.724177, 31.298978), (30.723874, 31.298982), (30.723883, 31.298796), (30.723563, 31.298763),
    (30.723571, 31.299340), (30.723351, 31.299368), (30.723354, 31.299624), (30.723106, 31.299629),
    (30.723083, 31.299289), (30.722603, 31.299287), (30.722602, 31.299040), (30.722476, 31.298887),
    (30.722474, 31.298885), (30.723228, 31.298330), (30.723236, 31.298163), (30.723105, 31.298165),
    (30.723102, 31.297909), (30.722863, 31.297913), (30.722820, 31.298446), (30.722298, 31.298443),
    (30.722293, 31.296397), (30.724224, 31.296490), (30.724249, 31.295636), (30.723865, 31.295652),
    (30.723869, 31.295506), (30.723698, 31.295505), (30.723700, 31.295325), (30.723546, 31.295320),
    (30.723553, 31.295189), (30.723513, 31.295189), (30.723424, 31.295068), (30.723430, 31.294069),
    (30.722907, 31.294052), (30.722870, 31.295608), (30.722565, 31.295599), (30.722601, 31.295016),
    (30.722308, 31.294998), (30.722413, 31.293531), (30.722103, 31.293463), (30.722123, 31.293295),
    (30.722468, 31.293347), (30.722546, 31.292812), (30.722917, 31.292887), (30.722943, 31.292311),
    (30.722508, 31.292233), (30.722609, 31.291585), (30.722487, 31.291574), (30.722551, 31.291134),
    (30.722271, 31.290978), (30.722376, 31.290487), (30.723197, 31.290470), (30.723447, 31.289850),
    (30.722869, 31.289696), (30.722908, 31.289504), (30.723129, 31.289564), (30.723334, 31.288885),
    (30.722683, 31.288752), (30.722639, 31.288950), (30.722493, 31.288907), (30.722508, 31.288817),
    (30.722267, 31.288766), (30.722300, 31.288589), (30.721931, 31.288531), (30.721987, 31.288171),
    (30.722862, 31.287790), (30.722983, 31.287686), (30.723240, 31.287739), (30.723145, 31.287891),
    (30.724054, 31.288657), (30.724014, 31.288809), (30.723727, 31.288738), (30.723584, 31.289331),
    (30.723976, 31.289488), (30.724065, 31.289078), (30.724422, 31.289217), (30.724606, 31.287618),
    (30.725379, 31.287741), (30.725432, 31.287241), (30.726149, 31.287339), (30.726072, 31.286229),
    (30.726688, 31.288502), (30.726883, 31.286281), (30.726529, 31.286324), (30.726393, 31.285772),
    (30.726885, 31.285764), (30.726763, 31.285263), (30.725981, 31.285181), (30.726013, 31.284693),
    (30.726629, 31.284729), (30.726296, 31.283332), (30.727404, 31.283527), (30.727628, 31.282346),
    (30.727934, 31.282098), (30.727906, 31.282351), (30.728364, 31.282331), (30.728379, 31.282563),
    (30.728533, 31.282559), (30.728550, 31.282847), (30.728771, 31.282858), (30.728783, 31.283372),
    (30.728867, 31.283370), (30.728894, 31.283940), (30.729369, 31.283918), (30.729388, 31.284299),
    (30.729571, 31.284288), (30.729904, 31.285527), (30.730149, 31.285504), (30.730166, 31.285871),
    (30.730870, 31.285854), (30.730911, 31.286129), (30.731057, 31.286175), (30.731075, 31.286738),
    (30.731296, 31.286725), (30.731301, 31.286861), (30.731551, 31.286875), (30.731618, 31.286145),
    (30.732257, 31.286211), (30.732213, 31.286628), (30.732463, 31.286675), (30.733320, 31.287117),
    (30.733914, 31.287269), (30.733991, 31.286705), (30.734372, 31.286789), (30.734334, 31.287032),
    (30.735238, 31.287192), (30.735163, 31.287714), (30.735515, 31.287807), (30.735485, 31.287994),
    (30.735682, 31.288038), (30.736004, 31.288855), (30.735767, 31.288963), (30.736112, 31.290061),
    (30.736201, 31.290607), (30.736611, 31.290530), (30.736718, 31.292075), (30.737504, 31.292097),
    (30.737359, 31.293014), (30.737856, 31.293283), (30.737787, 31.294242), (30.737386, 31.294167),
    (30.736955, 31.295531), (30.736568, 31.295382), (30.736186, 31.296724), (30.735956, 31.296656),
    (30.735666, 31.297535), (30.735786, 31.297608), (30.735754, 31.297701), (30.736233, 31.297994),
    (30.735298, 31.300357), (30.735131, 31.300549), (30.735560, 31.300958), (30.735970, 31.301115),
    (30.735685, 31.302161), (30.735944, 31.302214), (30.735818, 31.302683), (30.735475, 31.301738),
    (30.734499, 31.301261), (30.734008, 31.302902), (30.734462, 31.303135), (30.734278, 31.303673),
    (30.734143, 31.303502), (30.734085, 31.303215), (30.733325, 31.302837), (30.733228, 31.303085),
    (30.733124, 31.303040), (30.732857, 31.304064), (30.732406, 31.303793), (30.732351, 31.304903),
    (30.731808, 31.304799), (30.731905, 31.304481), (30.730897, 31.304118), (30.730894, 31.304281),
    (30.731161, 31.304519), (30.731154, 31.303862), (30.730056, 31.303467), (30.730106, 31.303235),
    (30.729515, 31.303288), (30.725045, 31.294755)
]

# ─────────────────────────────────────────────
# 4. المنطق والدوال
# ─────────────────────────────────────────────
@st.cache_resource
def build_polygons():
    return (
        Polygon([(lon, lat) for lat, lon in BOUNDARY_POINTS_1]),
        Polygon([(lon, lat) for lat, lon in BOUNDARY_POINTS_2])
    )

polygon1, polygon2 = build_polygons()

def parse_dms(text: str):
    parts = re.findall(r"(\d+)[°](\d+)['](\d+\.?\d*)[\"]([NSEW])", text)
    if len(parts) < 2:
        return None
    results = []
    for deg, min_, sec, direction in parts:
        val = float(deg) + float(min_) / 60 + float(sec) / 3600
        if direction in ("S", "W"):
            val = -val
        results.append(val)
    return tuple(results[:2])

def parse_coords(text: str):
    try:
        parts = text.replace(",", " ").split()
        if len(parts) >= 2:
            lat, lon = float(parts[0]), float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
    except ValueError:
        pass
    return parse_dms(text)

@st.cache_data(show_spinner=False)
def build_map(lat: float, lon: float, is_inside: bool):
    m = folium.Map(
        location=[lat, lon],
        zoom_start=16,
        prefer_canvas=True,
        control_scale=True,
        tiles=None
    )

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="🛰️ أقمار صناعية",
        overlay=False
    ).add_to(m)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps",
        name="🗺️ خريطة الشوارع",
        overlay=False
    ).add_to(m)

    poly_kw = dict(color="#00d4ff", weight=2.5, fillColor="#00b4d8", fillOpacity=0.12, dashArray="")
    folium.Polygon(locations=BOUNDARY_POINTS_1, **poly_kw, tooltip="<b>المنطقة الأولى</b>").add_to(m)
    folium.Polygon(locations=BOUNDARY_POINTS_2, **poly_kw, tooltip="<b>المنطقة الثانية</b>").add_to(m)

    color = "#00e5a0" if is_inside else "#ff5c7a"
    status = "✅ داخل الحيز" if is_inside else "⛔ خارج الحيز"

    folium.CircleMarker(
        location=[lat, lon],
        radius=22, color=color, weight=1.5,
        fill=True, fill_color=color, fill_opacity=0.12
    ).add_to(m)
    folium.CircleMarker(
        location=[lat, lon],
        radius=10, color=color, weight=2.5,
        fill=True, fill_color=color, fill_opacity=0.4
    ).add_to(m)

    folium.Marker(
        location=[lat, lon],
        tooltip=folium.Tooltip(
            f"<div style='direction:rtl;text-align:right;font-family:Cairo,sans-serif;min-width:160px'>"
            f"<b style='font-size:14px'>{status}</b><br>"
            f"<span style='color:#888'>خط عرض:</span> {lat:.6f}<br>"
            f"<span style='color:#888'>خط طول:</span> {lon:.6f}"
            f"</div>",
            permanent=False
        ),
        icon=folium.Icon(
            color="green" if is_inside else "red",
            icon="map-marker",
            prefix="fa"
        )
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ─────────────────────────────────────────────
# 5. الواجهة الرئيسية (UI)
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">🏙️ نظام ذكي &nbsp;|&nbsp; إصدار 2.0</div>
    <h1 class="hero-title">الاستعلام عن <span>الحيز العمراني</span></h1>
    <p class="hero-subtitle">
        تحقق فوري من موقع أي قطعة أرض أو مبنى داخل أو خارج النطاق العمراني المعتمد
        باستخدام إحداثياتك الجغرافية الدقيقة
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stats-row">
    <div class="stat-chip">
        <div class="stat-val">2</div>
        <div class="stat-label">نطاق عمراني معتمد</div>
    </div>
    <div class="stat-chip">
        <div class="stat-val" style="color:#00e5a0">GPS</div>
        <div class="stat-label">تحديد تلقائي بالموقع</div>
    </div>
    <div class="stat-chip">
        <div class="stat-val" style="color:#f0b429">DMS</div>
        <div class="stat-label">دعم صيغ متعددة</div>
    </div>
</div>
""", unsafe_allow_html=True)

col_input, col_result = st.columns([1, 2.2], gap="large")

with col_input:
    # ── بطاقة زر الـ GPS المخصصة ──
    st.markdown("""
    <div class="panel-card">
        <div class="panel-title">
            <span class="icon">📡</span>
            تحديد الموقع عبر GPS
        </div>
        <p style="font-size:0.85rem;color:#7a9ab5;margin:0 0 1rem;">
            قم بتفعيل الزر أدناه لالتقاط إحداثياتك الحالية مباشرةً
        </p>
    """, unsafe_allow_html=True)

    # الزر التفاعلي
    st.button(
        "🟢 التقاط الموقع مفعّل (اضغط للإيقاف)" if st.session_state.gps_active else "⚪ تفعيل التقاط الموقع",
        on_click=toggle_gps,
        use_container_width=True
    )
    
    # إغلاق بطاقة الـ GPS
    st.markdown("</div>", unsafe_allow_html=True)

    # تشغيل أمر التقاط الموقع فقط عندما يكون الزر مفعلاً
    if st.session_state.gps_active:
        try:
            loc = get_geolocation(component_key="get_loc")
            if loc and "coords" in loc:
                gps_lat = loc["coords"]["latitude"]
                gps_lon = loc["coords"]["longitude"]
                new_coords = f"{gps_lat:.6f}, {gps_lon:.6f}"
                
                # تحديث حقل الإدخال إذا كانت الإحداثيات جديدة لمنع إعادة التحميل اللانهائية
                if st.session_state.get("coord_input") != new_coords:
                    st.session_state.coord_input = new_coords
                    st.rerun()
                
                st.success(f"✅ تم التقاط الموقع بنجاح!")
        except Exception:
            pass

    st.markdown('<div class="divider">أو أدخل يدوياً</div>', unsafe_allow_html=True)

    # ── بطاقة الإدخال اليدوي ──
    st.markdown("""
    <div class="panel-card">
        <div class="panel-title">
            <span class="icon">✏️</span>
            إدخال الإحداثيات
        </div>
    """, unsafe_allow_html=True)

    with st.form("coord_form", clear_on_submit=False):
        # استخدام key="coord_input" يربط الحقل مباشرة بالجلسة، مما يحفظ الرقم المدخل
        user_input = st.text_input(
            "خط العرض , خط الطول",
            key="coord_input",
            placeholder="مثال:  30.727313, 31.284638",
            help="الصيغة العشرية: 30.727313, 31.284638  |  صيغة DMS: 30°43'38.3\"N 31°17'4.7\"E"
        )
        submitted = st.form_submit_button("🔍  بدء الفحص والاستعلام", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:0.5rem;padding:0.75rem 1rem;background:rgba(240,180,41,0.06);
         border-right:3px solid rgba(240,180,41,0.5);border-radius:8px;">
        <p style="font-size:0.78rem;color:#c9a44a;margin:0;line-height:1.6;">
            <b>💡 تلميح:</b> يمكنك نسخ الإحداثيات مباشرة من خرائط جوجل
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_result:
    if submitted:
        if not user_input.strip():
            st.warning("⚠️ الرجاء إدخال الإحداثيات أولاً قبل الفحص.")
        else:
            parsed = parse_coords(user_input)
            if parsed:
                lat, lon = parsed
                point = Point(lon, lat)
                is_inside = polygon1.contains(point) or polygon2.contains(point)

                if is_inside:
                    st.markdown("""
                    <div class="result-wrap result-inside">
                        <span class="result-icon">✅</span>
                        <div>
                            <div class="result-text-main">الموقع يقع داخل الحيز العمراني المعتمد</div>
                            <div class="result-text-sub">هذا الموقع ضمن النطاق الرسمي المعتمد للتخطيط العمراني</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="result-wrap result-outside">
                        <span class="result-icon">⛔</span>
                        <div>
                            <div class="result-text-main">الموقع يقع خارج الحيز العمراني</div>
                            <div class="result-text-sub">هذا الموقع خارج النطاق العمراني الرسمي المعتمد حالياً</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="coords-card">
                    <span class="coords-dot"></span>
                    <div>
                        <div class="coords-label">الإحداثيات المستخدمة في الفحص</div>
                        <div class="coords-value">
                            {lat:.6f}&nbsp;&nbsp;,&nbsp;&nbsp;{lon:.6f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="map-header">
                    <span class="map-title">🗺️ الخريطة التفاعلية</span>
                    <span class="map-badge badge-live">● مباشر</span>
                </div>
                """, unsafe_allow_html=True)

                with st.spinner("⏳ جارٍ تحميل الخريطة التفاعلية..."):
                    m = build_map(lat, lon, is_inside)
                    st_folium(m, width="100%", height=470, returned_objects=[])

            else:
                st.error("❌ صيغة الإحداثيات غير صحيحة. يرجى التأكد من إدخال الأرقام بالشكل الصحيح مثل: **30.727313, 31.284638**")

    else:
        st.markdown("""
        <div class="placeholder-screen">
            <div class="placeholder-icon">🗺️</div>
            <div class="placeholder-title">الخريطة التفاعلية</div>
            <div class="placeholder-desc">
                أدخل إحداثيات الموقع أو قم بتفعيل التقاط الموقع<br>
                ثم اضغط على "بدء الفحص" لعرض النتيجة
            </div>
        </div>
        """, unsafe_allow_html=True)
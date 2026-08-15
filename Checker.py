import streamlit as st
from shapely.geometry import Point, Polygon
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
import re

# ─────────────────────────────────────────────
# 1. إعدادات الصفحة
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="الحيز العمراني | نظام الاستعلام",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "gps_active" not in st.session_state:
    st.session_state.gps_active = False
if "coord_input" not in st.session_state:
    st.session_state.coord_input = ""
if "last_gps_coords" not in st.session_state:
    st.session_state.last_gps_coords = ""

def toggle_gps():
    st.session_state.gps_active = not st.session_state.gps_active

# ─────────────────────────────────────────────
# 2. CSS الشامل
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@300;400;500;700;800&display=swap');

:root {
    --bg-page:    #f5f7fa;
    --bg-white:   #ffffff;
    --bg-soft:    #eef1f6;
    --bg-card:    #ffffff;
    --gold-500:   #c8950a;
    --gold-400:   #e8a800;
    --gold-300:   #f5c842;
    --gold-100:   #fff8e1;
    --teal-500:   #0d9488;
    --teal-400:   #14b8a6;
    --green-600:  #059669;
    --green-400:  #10b981;
    --green-50:   #ecfdf5;
    --rose-600:   #e11d48;
    --rose-400:   #f43f5e;
    --rose-50:    #fff1f2;
    --ink-900:    #0f172a;
    --ink-700:    #1e293b;
    --ink-500:    #334155;
    --ink-400:    #475569;
    --ink-300:    #64748b;
    --ink-200:    #94a3b8;
    --ink-100:    #cbd5e1;
    --ink-50:     #f1f5f9;
    --border-dim: rgba(0,0,0,0.07);
    --border-med: rgba(0,0,0,0.12);
    --border-gold:rgba(232,168,0,0.35);
    --shadow-sm:  0 1px 4px rgba(0,0,0,0.06);
    --shadow-md:  0 4px 20px rgba(0,0,0,0.08);
    --shadow-lg:  0 12px 40px rgba(0,0,0,0.12);
    --r-xl: 20px;
    --r-lg: 14px;
    --r-md: 10px;
}

*, *::before, *::after {
    font-family: 'Cairo', 'Tajawal', sans-serif !important;
    direction: rtl;
    text-align: right;
    box-sizing: border-box;
}

html, body, .stApp {
    background: var(--bg-page) !important;
    color: var(--ink-900) !important;
    min-height: 100vh;
}

/* Grid background subtle */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px);
    background-size: 72px 72px;
    pointer-events: none;
    z-index: 0;
}

/* Ambient orbs */
.stApp::after {
    content: '';
    position: fixed;
    top: -200px;
    right: -200px;
    width: 700px;
    height: 700px;
    background: radial-gradient(ellipse, rgba(232,168,0,0.07) 0%, transparent 65%);
    pointer-events: none;
    z-index: 0;
    animation: orbFloat 12s ease-in-out infinite;
}

@keyframes orbFloat {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33%       { transform: translate(-40px, 30px) scale(1.05); }
    66%       { transform: translate(20px, -20px) scale(0.97); }
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── HERO ── */
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(145deg, #ffffff 0%, #fefce8 50%, #fff8e1 100%);
    border: 1px solid rgba(232,168,0,0.25);
    border-radius: var(--r-xl);
    padding: 3rem 2.5rem 2.5rem;
    margin-bottom: 1.8rem;
    text-align: center;
    box-shadow: var(--shadow-md);
    animation: heroEntrance 0.7s cubic-bezier(0.22,1,0.36,1) both;
}

@keyframes heroEntrance {
    from { opacity: 0; transform: translateY(-24px); }
    to   { opacity: 1; transform: translateY(0); }
}

.hero-glow {
    position: absolute;
    top: -80px; left: 50%;
    transform: translateX(-50%);
    width: 500px; height: 260px;
    background: radial-gradient(ellipse, rgba(232,168,0,0.12) 0%, transparent 70%);
    pointer-events: none;
}

.hero-line-top {
    position: absolute;
    top: 0; left: 10%; right: 10%;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold-400), transparent);
    animation: scanLine 3s ease-in-out infinite;
}

@keyframes scanLine {
    0%, 100% { opacity: 0.4; transform: scaleX(0.6); }
    50%       { opacity: 1;   transform: scaleX(1); }
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(232,184,75,0.1);
    border: 1px solid rgba(232,184,75,0.35);
    color: var(--gold-400);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    padding: 0.35rem 1.1rem;
    border-radius: 50px;
    margin-bottom: 1.2rem;
    text-transform: uppercase;
    animation: fadeIn 0.5s 0.2s both;
}

.hero-badge .dot {
    width: 6px; height: 6px;
    background: var(--gold-400);
    border-radius: 50%;
    animation: dotPulse 2s infinite;
}

@keyframes dotPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(232,184,75,0.6); }
    50%       { box-shadow: 0 0 0 5px rgba(232,184,75,0); }
}

.hero-title {
    font-size: clamp(2rem, 4vw, 2.8rem);
    font-weight: 900;
    color: var(--ink-900);
    margin: 0 0 0.6rem;
    line-height: 1.2;
    animation: fadeIn 0.5s 0.3s both;
}

.hero-title em {
    font-style: normal;
    background: linear-gradient(135deg, var(--gold-500), var(--gold-400), var(--teal-500));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 0.95rem;
    color: var(--ink-300);
    max-width: 540px;
    margin: 0 auto;
    line-height: 1.8;
    animation: fadeIn 0.5s 0.4s both;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── STATS ROW ── */
.stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.9rem;
    margin-bottom: 1.8rem;
    animation: fadeIn 0.6s 0.5s both;
}

.stat-chip {
    background: var(--bg-white);
    border: 1px solid var(--border-dim);
    border-radius: var(--r-lg);
    padding: 1.1rem 0.8rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s, transform 0.3s, box-shadow 0.3s;
    cursor: default;
    box-shadow: var(--shadow-sm);
}

.stat-chip::before {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold-400), transparent);
    transform: scaleX(0);
    transition: transform 0.4s;
}

.stat-chip:hover { border-color: var(--border-gold); transform: translateY(-3px); box-shadow: var(--shadow-md); }
.stat-chip:hover::before { transform: scaleX(1); }

.stat-val {
    font-size: 1.55rem;
    font-weight: 900;
    color: var(--gold-500);
    line-height: 1;
    margin-bottom: 0.35rem;
}

.stat-label {
    font-size: 0.73rem;
    color: var(--ink-300);
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* ── PANEL CARD ── */
.panel-card {
    background: var(--bg-white);
    border: 1px solid var(--border-dim);
    border-radius: var(--r-xl);
    padding: 1.5rem;
    margin-bottom: 1.1rem;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.35s, box-shadow 0.35s;
    animation: fadeIn 0.5s 0.5s both;
}

.panel-card:hover { border-color: var(--border-gold); box-shadow: var(--shadow-md); }

.panel-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--ink-700);
    margin-bottom: 1rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--border-dim);
}

.panel-icon {
    width: 32px; height: 32px;
    background: var(--gold-100);
    border: 1px solid rgba(232,168,0,0.25);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem;
    flex-shrink: 0;
}

/* ── INPUTS ── */
div[data-testid="stTextInput"] input {
    background: var(--bg-soft) !important;
    border: 1px solid var(--border-med) !important;
    border-radius: var(--r-md) !important;
    color: var(--ink-900) !important;
    padding: 0.7rem 1rem !important;
    font-size: 0.95rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
    pointer-events: auto !important;
    user-select: text !important;
    -webkit-user-select: text !important;
    caret-color: var(--gold-500) !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: var(--gold-400) !important;
    box-shadow: 0 0 0 3px rgba(232,168,0,0.12) !important;
    outline: none !important;
    background: #ffffff !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: var(--ink-200) !important;
}

div[data-testid="stTextInput"] label {
    color: var(--ink-400) !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.4rem !important;
}

/* ── BUTTONS ── */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #b8921e, #e8b84b, #f2cc7a) !important;
    background-size: 200% 200% !important;
    border: none !important;
    color: var(--navy-900) !important;
    border-radius: var(--r-md) !important;
    font-weight: 900 !important;
    font-size: 1rem !important;
    padding: 0.8rem !important;
    width: 100% !important;
    letter-spacing: 0.04em !important;
    transition: all 0.3s ease !important;
    animation: shimmer 3s ease infinite !important;
    box-shadow: 0 4px 20px rgba(232,184,75,0.25) !important;
}

@keyframes shimmer {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 30px rgba(232,184,75,0.45) !important;
}

div[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(-1px) !important;
}

/* ── GPS BUTTON ── */
div[data-testid="stButton"] > button {
    border-radius: var(--r-md) !important;
    font-weight: 700 !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}

/* ── DIVIDER ── */
.divider {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 1rem 0;
    color: var(--ink-200);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
}

.divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border-dim);
}

/* ── RESULT CARDS ── */
.result-card {
    border-radius: var(--r-xl);
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: flex-start;
    gap: 1.2rem;
    animation: resultPop 0.5s cubic-bezier(0.34,1.56,0.64,1) both;
    position: relative;
    overflow: hidden;
}

@keyframes resultPop {
    from { opacity: 0; transform: scale(0.92) translateY(16px); }
    to   { opacity: 1; transform: scale(1) translateY(0); }
}

.result-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: inherit;
    filter: blur(40px);
    z-index: -1;
    opacity: 0.3;
}

.result-inside {
    background: linear-gradient(135deg, #ecfdf5, #f0fdf9);
    border: 1px solid rgba(16,185,129,0.35);
    box-shadow: 0 4px 20px rgba(16,185,129,0.1), inset 0 1px 0 rgba(16,185,129,0.15);
}

.result-outside {
    background: linear-gradient(135deg, #fff1f2, #fef2f2);
    border: 1px solid rgba(244,63,94,0.35);
    box-shadow: 0 4px 20px rgba(244,63,94,0.1), inset 0 1px 0 rgba(244,63,94,0.15);
}

.result-emoji {
    font-size: 2.8rem;
    line-height: 1;
    flex-shrink: 0;
    animation: bounceIn 0.6s 0.2s cubic-bezier(0.34,1.56,0.64,1) both;
}

@keyframes bounceIn {
    from { opacity: 0; transform: scale(0.3) rotate(-15deg); }
    to   { opacity: 1; transform: scale(1) rotate(0deg); }
}

.result-title {
    font-size: 1.15rem;
    font-weight: 800;
    line-height: 1.3;
    margin-bottom: 0.3rem;
}

.result-inside .result-title  { color: var(--green-600); }
.result-outside .result-title { color: var(--rose-600); }

.result-desc {
    font-size: 0.83rem;
    color: var(--ink-400);
    line-height: 1.6;
}

/* ── COORDS DISPLAY ── */
.coords-display {
    background: var(--gold-100);
    border: 1px solid rgba(232,168,0,0.25);
    border-radius: var(--r-lg);
    padding: 1rem 1.3rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.2rem;
    animation: fadeIn 0.4s 0.3s both;
}

.coords-pulse {
    width: 10px; height: 10px;
    background: var(--gold-500);
    border-radius: 50%;
    flex-shrink: 0;
    animation: coordsPulse 2s ease-in-out infinite;
}

@keyframes coordsPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(200,149,10,0.5); }
    50%       { box-shadow: 0 0 0 8px rgba(200,149,10,0); }
}

.coords-lbl { font-size: 0.73rem; color: var(--ink-300); font-weight: 600; letter-spacing: 0.06em; margin-bottom: 0.2rem; }
.coords-val { font-size: 0.97rem; font-weight: 700; color: var(--gold-500); font-variant-numeric: tabular-nums; direction: ltr; text-align: left; }

/* ── MAP HEADER ── */
.map-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
    animation: fadeIn 0.4s 0.4s both;
}

.map-label {
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--ink-700);
    display: flex;
    align-items: center;
    gap: 8px;
}

.live-badge {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--green-600);
    border: 1px solid rgba(5,150,105,0.3);
    background: var(--green-50);
    padding: 0.2rem 0.65rem;
    border-radius: 50px;
    letter-spacing: 0.08em;
    animation: liveBlink 2.5s ease-in-out infinite;
}

@keyframes liveBlink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.45; }
}

/* ── PLACEHOLDER ── */
.placeholder {
    height: 530px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 2px dashed rgba(232,168,0,0.2);
    border-radius: var(--r-xl);
    background: var(--bg-white);
    transition: border-color 0.3s;
    animation: fadeIn 0.5s 0.6s both;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.placeholder::before {
    content: '';
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(232,168,0,0.06) 0%, transparent 65%);
    border-radius: 50%;
    animation: placeholderPulse 4s ease-in-out infinite;
}

@keyframes placeholderPulse {
    0%, 100% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.5; }
    50%       { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
}

.placeholder:hover { border-color: rgba(232,168,0,0.35); }

.placeholder-icon {
    font-size: 4.5rem;
    opacity: 0.2;
    margin-bottom: 1rem;
    filter: drop-shadow(0 0 12px rgba(232,168,0,0.3));
    animation: iconFloat 4s ease-in-out infinite;
}

@keyframes iconFloat {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-10px); }
}

.placeholder-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--ink-200);
    margin-bottom: 0.5rem;
}

.placeholder-desc {
    font-size: 0.82rem;
    color: var(--ink-100);
    text-align: center;
    max-width: 260px;
    line-height: 1.7;
}

/* ── TIP BOX ── */
.tip-box {
    margin-top: 0.8rem;
    padding: 0.8rem 1rem;
    background: var(--gold-100);
    border-right: 3px solid var(--gold-400);
    border-radius: 8px;
    font-size: 0.78rem;
    color: var(--gold-500);
    line-height: 1.6;
}

/* ── GPS STATUS ── */
.gps-success {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--green-50);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.82rem;
    color: var(--green-600);
    margin-top: 0.6rem;
    animation: fadeIn 0.3s both;
}

div[data-testid="stAlert"] {
    border-radius: var(--r-md) !important;
    background: var(--gold-100) !important;
    border: 1px solid rgba(232,168,0,0.3) !important;
    border-left: none !important;
    border-right: 3px solid var(--gold-400) !important;
    color: var(--ink-700) !important;
}

div[data-testid="stSpinner"] p { color: var(--ink-300) !important; font-size: 0.85rem !important; }

section[data-testid="stSidebar"] { background: var(--bg-soft) !important; }

/* Scroll reveal utility */
.reveal { animation: fadeIn 0.5s both; }
</style>
""", unsafe_allow_html=True)

# تنسيق زر GPS حسب الحالة
if st.session_state.gps_active:
    gps_css = """
    <style>
    div[data-testid="stButton"] > button {
        background: #ecfdf5 !important;
        border: 1px solid rgba(5,150,105,0.4) !important;
        color: #059669 !important;
        box-shadow: 0 2px 10px rgba(5,150,105,0.12) !important;
    }
    div[data-testid="stButton"] > button:hover {
        background: #d1fae5 !important;
        box-shadow: 0 4px 16px rgba(5,150,105,0.2) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """
else:
    gps_css = """
    <style>
    div[data-testid="stButton"] > button {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        color: #64748b !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
    }
    div[data-testid="stButton"] > button:hover {
        background: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """
st.markdown(gps_css, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. البيانات
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
# 4. الدوال
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

    # رسم حدود المنطقتين
    poly_style = dict(color="#e8b84b", weight=2.5, fillColor="#e8b84b", fillOpacity=0.08, dashArray="6 4")
    folium.Polygon(locations=BOUNDARY_POINTS_1, **poly_style, tooltip="<b style='font-family:Cairo'>المنطقة الأولى</b>").add_to(m)
    folium.Polygon(locations=BOUNDARY_POINTS_2, **poly_style, tooltip="<b style='font-family:Cairo'>المنطقة الثانية</b>").add_to(m)

    color   = "#34d399" if is_inside else "#fb7185"
    status  = "✅ داخل الحيز" if is_inside else "⛔ خارج الحيز"

    # حلقات نابضة
    for r, op in [(30, 0.06), (16, 0.14), (8, 0.35)]:
        folium.CircleMarker(
            location=[lat, lon],
            radius=r, color=color, weight=1.5,
            fill=True, fill_color=color, fill_opacity=op
        ).add_to(m)

    folium.Marker(
        location=[lat, lon],
        tooltip=folium.Tooltip(
            f"""<div style='direction:rtl;text-align:right;font-family:Cairo,sans-serif;
                min-width:170px;padding:4px'>
                <b style='font-size:14px;color:{"#34d399" if is_inside else "#fb7185"}'>{status}</b><br>
                <span style='color:#64748b;font-size:12px'>خط عرض:</span>
                <span style='font-size:12px'> {lat:.6f}</span><br>
                <span style='color:#64748b;font-size:12px'>خط طول:</span>
                <span style='font-size:12px'> {lon:.6f}</span>
            </div>""",
            permanent=False
        ),
        icon=folium.Icon(color="green" if is_inside else "red", icon="map-marker", prefix="fa")
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ─────────────────────────────────────────────
# 5. الواجهة
# ─────────────────────────────────────────────

# HERO
st.markdown("""
<div class="hero">
    <div class="hero-glow"></div>
    <div class="hero-line-top"></div>
    <h1 class="hero-title">الاستعلام عن <em>الحيز العمراني</em></h1>
    <p class="hero-sub">
        تحقق فوري من موقع أي قطعة أرض أو مبنى داخل أو خارج النطاق العمراني المعتمد
        باستخدام إحداثياتك الجغرافية الدقيقة
    </p>
</div>
""", unsafe_allow_html=True)

# STATS
st.markdown("""
<div class="stats-row">
    <div class="stat-chip">
        <div class="stat-val">2</div>
        <div class="stat-label">نطاق عمراني معتمد</div>
    </div>
    <div class="stat-chip">
        <div class="stat-val" style="font-size:1.2rem;color:var(--green-600)">GPS</div>
        <div class="stat-label">تحديد تلقائي بالموقع</div>
    </div>
    <div class="stat-chip">
        <div class="stat-val" style="font-size:1.2rem;color:var(--teal-500)">DMS</div>
        <div class="stat-label">دعم صيغ متعددة</div>
    </div>
</div>
""", unsafe_allow_html=True)

# COLUMNS
col_input, col_result = st.columns([1, 2.2], gap="large")

with col_input:
    # ── GPS CARD ──
    st.markdown("""
    <div class="panel-card">
        <div class="panel-title">
            <span class="panel-icon">📡</span>
            تحديد الموقع عبر GPS
        </div>
        <p style="font-size:0.82rem;color:var(--slate-500);margin:0 0 0.9rem;line-height:1.6;">
            فعّل الزر لالتقاط إحداثياتك الحالية تلقائياً
        </p>
    """, unsafe_allow_html=True)

    st.button(
        "🟢  التقاط الموقع — مفعّل  (اضغط للإيقاف)" if st.session_state.gps_active
        else "📍  تفعيل التقاط الموقع",
        on_click=toggle_gps,
        use_container_width=True
    )

    if st.session_state.gps_active:
        try:
            loc = get_geolocation(component_key="get_loc")
            if loc and "coords" in loc:
                gps_lat = loc["coords"]["latitude"]
                gps_lon = loc["coords"]["longitude"]
                new_coords = f"{gps_lat:.6f}, {gps_lon:.6f}"
                if st.session_state.get("last_gps_coords") != new_coords:
                    st.session_state.last_gps_coords = new_coords
                    st.session_state.coord_input = new_coords
                    st.rerun()
                st.markdown("""
                <div class="gps-success">
                    <span>●</span> تم التقاط الموقع بنجاح
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

    st.markdown("</div>", unsafe_allow_html=True)

    # DIVIDER
    st.markdown('<div class="divider">أو أدخل يدوياً</div>', unsafe_allow_html=True)

    # ── INPUT CARD ──
    st.markdown("""
    <div class="panel-card">
        <div class="panel-title">
            <span class="panel-icon">✏️</span>
            إدخال الإحداثيات
        </div>
    """, unsafe_allow_html=True)

    with st.form("coord_form", clear_on_submit=False):
        user_input = st.text_input(
            "خط العرض , خط الطول",
            value=st.session_state.coord_input,
            key="coord_input",
            placeholder="مثال:  30.727313 , 31.284638",
            help="الصيغة العشرية: 30.727313, 31.284638  |  DMS: 30°43'38.3\"N 31°17'4.7\"E"
        )
        submitted = st.form_submit_button("🔍  بدء الفحص والاستعلام", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # TIP
    st.markdown("""
    <div class="tip-box">
        💡 <b>تلميح:</b> يمكنك نسخ الإحداثيات مباشرةً من خرائط جوجل ولصقها هنا
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
                    <div class="result-card result-inside">
                        <span class="result-emoji">✅</span>
                        <div>
                            <div class="result-title">الموقع داخل الحيز العمراني المعتمد</div>
                            <div class="result-desc">هذا الموقع ضمن النطاق الرسمي المعتمد للتخطيط العمراني</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="result-card result-outside">
                        <span class="result-emoji">⛔</span>
                        <div>
                            <div class="result-title">الموقع خارج الحيز العمراني</div>
                            <div class="result-desc">هذا الموقع خارج النطاق العمراني الرسمي المعتمد حالياً</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="coords-display">
                    <span class="coords-pulse"></span>
                    <div>
                        <div class="coords-lbl">الإحداثيات المستخدمة في الفحص</div>
                        <div class="coords-val">{lat:.6f} &nbsp;,&nbsp; {lon:.6f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div class="map-header">
                    <span class="map-label">🗺️ الخريطة التفاعلية</span>
                    <span class="live-badge">● مباشر</span>
                </div>
                """, unsafe_allow_html=True)

                with st.spinner("جارٍ تحميل الخريطة…"):
                    m = build_map(lat, lon, is_inside)
                    st_folium(m, width="100%", height=470, returned_objects=[])

            else:
                st.error("❌ صيغة الإحداثيات غير صحيحة — يرجى المحاولة بالشكل: **30.727313, 31.284638**")

    else:
        st.markdown("""
        <div class="placeholder">
            <div class="placeholder-icon">🗺️</div>
            <div class="placeholder-title">الخريطة التفاعلية</div>
            <div class="placeholder-desc">
                أدخل إحداثيات الموقع أو فعّل GPS<br>
                ثم اضغط «بدء الفحص» لعرض النتيجة
            </div>
        </div>
        """, unsafe_allow_html=True)
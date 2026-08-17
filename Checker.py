import streamlit as st
from shapely.geometry import Point, Polygon
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
import re

# ══════════════════════════════════════════════════════════════════
# 1.  إعداد الصفحة
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="الحيز العمراني — نظام الاستعلام",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── حالة الجلسة ──────────────────────────────────────────────────
if "gps_active"      not in st.session_state: st.session_state.gps_active      = False
if "coord_input"     not in st.session_state: st.session_state.coord_input      = ""
if "last_gps_coords" not in st.session_state: st.session_state.last_gps_coords  = ""

def toggle_gps():
    st.session_state.gps_active = not st.session_state.gps_active


# ══════════════════════════════════════════════════════════════════
# 2.  نظام التصميم (CSS)
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');

/* ── TOKEN LAYER ─────────────────────────────────────────── */
:root {
    /* Surfaces */
    --page      : #f4f6f9;
    --white     : #ffffff;
    --surface   : #f8fafc;

    /* Ink scale */
    --ink-900   : #0f172a;
    --ink-700   : #1e293b;
    --ink-500   : #334155;
    --ink-400   : #475569;
    --ink-300   : #64748b;
    --ink-200   : #94a3b8;
    --ink-100   : #e2e8f0;
    --ink-50    : #f1f5f9;

    /* Brand — warm gold */
    --gold      : #b45309;
    --gold-mid  : #d97706;
    --gold-lite : #fef3c7;
    --gold-bdr  : #fde68a;

    /* Semantic — green (inside) */
    --green     : #065f46;
    --green-mid : #059669;
    --green-lite: #ecfdf5;
    --green-bdr : #6ee7b7;

    /* Semantic — red (outside) */
    --red       : #991b1b;
    --red-mid   : #dc2626;
    --red-lite  : #fef2f2;
    --red-bdr   : #fca5a5;

    /* Radii */
    --r-sm  : 8px;
    --r-md  : 12px;
    --r-lg  : 18px;

    /* Shadows */
    --s-xs  : 0 1px 3px rgba(0,0,0,.05);
    --s-sm  : 0 2px 10px rgba(0,0,0,.07);
    --s-md  : 0 6px 24px rgba(0,0,0,.09);
}

/* ── RESET ────────────────────────────────────────────────── */
*, *::before, *::after {
    box-sizing : border-box;
    font-family: 'Cairo', sans-serif !important;
    direction  : rtl;
    text-align : right;
}

html, body, .stApp {
    background: var(--page) !important;
    color     : var(--ink-900) !important;
    min-height: 100vh;
}

/* إخفاء عناصر Streamlit الافتراضية */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stHeader"] { display: none !important; }

section[data-testid="stSidebar"] { background: var(--white) !important; }

/* ── KEYFRAMES ────────────────────────────────────────────── */
@keyframes fadeUp {
    from { opacity:0; transform:translateY(16px); }
    to   { opacity:1; transform:translateY(0);    }
}
@keyframes popIn {
    from { opacity:0; transform:scale(.35) rotate(-8deg); }
    to   { opacity:1; transform:scale(1)   rotate(0);     }
}
@keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0   rgba(217,119,6,.45); }
    50%     { box-shadow: 0 0 0 7px rgba(217,119,6,0);   }
}
@keyframes blink {
    0%,100% { opacity:1;  }
    50%     { opacity:.25;}
}
@keyframes float {
    0%,100% { transform:translateY(0);    }
    50%     { transform:translateY(-9px); }
}
@keyframes scanLine {
    0%,100% { opacity:.4; transform:scaleX(.55); }
    50%     { opacity:1;  transform:scaleX(1);   }
}

/* ── TOPBAR ───────────────────────────────────────────────── */
.topbar {
    display        : flex;
    align-items    : center;
    justify-content: space-between;
    padding-bottom : 1.25rem;
    margin-bottom  : 1.4rem;
    border-bottom  : 1px solid var(--ink-100);
    animation      : fadeUp .45s ease both;
}
.brand {
    display    : flex;
    align-items: center;
    gap        : 10px;
}
.brand-mark {
    width          : 38px;
    height         : 38px;
    background     : var(--ink-900);
    border-radius  : var(--r-sm);
    display        : flex;
    align-items    : center;
    justify-content: center;
    font-size      : 18px;
    flex-shrink    : 0;
}
.brand-name    { font-size:.95rem; font-weight:700; color:var(--ink-900); line-height:1.2; }
.brand-sub     { font-size:.7rem;  font-weight:400; color:var(--ink-300); }
.live-pill {
    display    : flex;
    align-items: center;
    gap        : 6px;
    font-size  : .7rem;
    font-weight: 700;
    color      : var(--green-mid);
    background : var(--green-lite);
    border     : 1px solid var(--green-bdr);
    padding    : 5px 13px;
    border-radius: 50px;
    letter-spacing: .04em;
}
.live-dot {
    width        : 6px;
    height       : 6px;
    background   : var(--green-mid);
    border-radius: 50%;
    animation    : blink 2s ease-in-out infinite;
}

/* ── HERO ─────────────────────────────────────────────────── */
.hero {
    position     : relative;
    overflow     : hidden;
    background   : var(--white);
    border       : 1px solid var(--ink-100);
    border-radius: var(--r-lg);
    padding      : 2.6rem 2rem 2.2rem;
    margin-bottom: 1.4rem;
    text-align   : center;
    box-shadow   : var(--s-sm);
    animation    : fadeUp .5s .05s ease both;
}
/* الخط الذهبي العلوي */
.hero::before {
    content   : '';
    position  : absolute;
    top:0; left:0; right:0;
    height    : 3px;
    background: linear-gradient(90deg, transparent 0%, var(--gold-mid) 40%,
                                       var(--gold-mid) 60%, transparent 100%);
    animation : scanLine 3s ease-in-out infinite;
}
.hero-eye {
    font-size     : .68rem;
    font-weight   : 700;
    letter-spacing: .14em;
    text-transform: uppercase;
    color         : var(--gold-mid);
    margin-bottom : .55rem;
}
.hero h1 {
    font-size  : clamp(1.75rem, 3.5vw, 2.5rem);
    font-weight: 900;
    color      : var(--ink-900);
    line-height: 1.2;
    margin     : 0 0 .65rem;
}
.hero h1 em { font-style:normal; color:var(--gold-mid); }
.hero p {
    font-size : .88rem;
    color     : var(--ink-300);
    line-height: 1.85;
    max-width : 480px;
    margin    : 0 auto;
}

/* ── CARD ─────────────────────────────────────────────────── */
.card {
    background   : var(--white);
    border       : 1px solid var(--ink-100);
    border-radius: var(--r-md);
    padding      : 1.15rem;
    margin-bottom: 1rem;
    box-shadow   : var(--s-xs);
    transition   : border-color .25s, box-shadow .25s;
    animation    : fadeUp .5s .1s ease both;
}
.card:hover { border-color:var(--gold-bdr); box-shadow:var(--s-sm); }

.card-head {
    display      : flex;
    align-items  : center;
    gap          : 9px;
    margin-bottom: .85rem;
    padding-bottom: .7rem;
    border-bottom: 1px solid var(--ink-100);
}
.card-icon {
    width          : 30px;
    height         : 30px;
    background     : var(--gold-lite);
    border         : 1px solid var(--gold-bdr);
    border-radius  : 7px;
    display        : flex;
    align-items    : center;
    justify-content: center;
    font-size      : .82rem;
    flex-shrink    : 0;
}
.card-title { font-size:.83rem; font-weight:700; color:var(--ink-700); }
.card-hint  { font-size:.78rem; color:var(--ink-300); line-height:1.65; margin:0 0 .75rem; }

/* ── OR DIVIDER ───────────────────────────────────────────── */
.or-div {
    display    : flex;
    align-items: center;
    gap        : .7rem;
    margin     : .7rem 0;
    font-size  : .7rem;
    font-weight: 600;
    color      : var(--ink-200);
    letter-spacing: .06em;
}
.or-div::before,.or-div::after { content:''; flex:1; height:1px; background:var(--ink-100); }

/* ── GPS SUCCESS MESSAGE ──────────────────────────────────── */
.gps-ok {
    display    : flex;
    align-items: center;
    gap        : 7px;
    background : var(--green-lite);
    border     : 1px solid var(--green-bdr);
    border-radius: var(--r-sm);
    padding    : .5rem .85rem;
    font-size  : .76rem;
    font-weight: 700;
    color      : var(--green-mid);
    margin-top : .6rem;
    animation  : fadeUp .3s ease both;
}

/* ── TIP ──────────────────────────────────────────────────── */
.tip {
    padding      : .6rem .85rem;
    background   : var(--gold-lite);
    border-right : 3px solid var(--gold-mid);
    border-radius: 0 var(--r-sm) var(--r-sm) 0;
    font-size    : .73rem;
    color        : var(--gold);
    font-weight  : 600;
    line-height  : 1.6;
    margin-top   : .75rem;
}

/* ── STREAMLIT INPUTS ─────────────────────────────────────── */
div[data-testid="stTextInput"] input {
    background   : var(--surface) !important;
    border       : 1px solid var(--ink-100) !important;
    border-radius: var(--r-sm) !important;
    color        : var(--ink-900) !important;
    padding      : .62rem .9rem !important;
    font-size    : .9rem !important;
    pointer-events: auto !important;
    user-select  : text !important;
    -webkit-user-select: text !important;
    caret-color  : var(--gold-mid) !important;
    transition   : border-color .2s, box-shadow .2s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--gold-mid) !important;
    box-shadow  : 0 0 0 3px rgba(217,119,6,.1) !important;
    background  : var(--white) !important;
    outline     : none !important;
}
div[data-testid="stTextInput"] input::placeholder { color:var(--ink-200) !important; }
div[data-testid="stTextInput"] label {
    font-size     : .7rem !important;
    font-weight   : 700 !important;
    color         : var(--ink-300) !important;
    letter-spacing: .07em !important;
    text-transform: uppercase !important;
}

/* ── SUBMIT BUTTON ────────────────────────────────────────── */
div[data-testid="stFormSubmitButton"] > button {
    background   : var(--ink-900) !important;
    border       : none !important;
    color        : #fff !important;
    border-radius: var(--r-sm) !important;
    font-weight  : 800 !important;
    font-size    : .88rem !important;
    padding      : .72rem !important;
    width        : 100% !important;
    letter-spacing: .03em !important;
    box-shadow   : var(--s-xs) !important;
    transition   : background .2s, transform .2s, box-shadow .2s !important;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--ink-700) !important;
    transform : translateY(-2px) !important;
    box-shadow: var(--s-sm) !important;
}
div[data-testid="stFormSubmitButton"] > button:active { transform:translateY(0) !important; }

/* ── GPS TOGGLE BUTTON ────────────────────────────────────── */
div[data-testid="stButton"] > button {
    border-radius: var(--r-sm) !important;
    font-weight  : 700 !important;
    font-size    : .83rem !important;
    padding      : .62rem !important;
    width        : 100% !important;
    transition   : all .2s ease !important;
}

/* ── RESULT PANEL ─────────────────────────────────────────── */
.result-panel {
    background   : var(--white);
    border       : 1px solid var(--ink-100);
    border-radius: var(--r-lg);
    overflow     : hidden;
    box-shadow   : var(--s-sm);
    animation    : fadeUp .4s ease both;
}

/* شريط النتيجة */
.res-bar {
    display    : flex;
    align-items: center;
    gap        : 1rem;
    padding    : 1.1rem 1.5rem;
}
.res-bar-in  { background:var(--green-lite); border-bottom:1px solid var(--green-bdr); }
.res-bar-out { background:var(--red-lite);   border-bottom:1px solid var(--red-bdr);   }

.res-emoji {
    font-size  : 2rem;
    flex-shrink: 0;
    animation  : popIn .45s .1s cubic-bezier(.34,1.56,.64,1) both;
}
.res-title       { font-size:1rem;  font-weight:800; line-height:1.3; }
.res-title-in    { color:var(--green); }
.res-title-out   { color:var(--red);   }
.res-desc        { font-size:.76rem; color:var(--ink-300); margin-top:.2rem; }

/* سطر الإحداثيات */
.coords-row {
    display     : flex;
    align-items : center;
    gap         : .9rem;
    padding     : .85rem 1.5rem;
    background  : var(--surface);
    border-bottom: 1px solid var(--ink-100);
}
.coords-dot {
    width        : 9px;
    height       : 9px;
    background   : var(--gold-mid);
    border-radius: 50%;
    flex-shrink  : 0;
    animation    : pulse 2s ease-in-out infinite;
}
.coords-lbl {
    font-size     : .66rem;
    font-weight   : 700;
    color         : var(--ink-200);
    text-transform: uppercase;
    letter-spacing: .07em;
    margin-bottom : .2rem;
}
.coords-val {
    font-size         : .9rem;
    font-weight       : 700;
    color             : var(--ink-700);
    direction         : ltr;
    text-align        : left;
    font-variant-numeric: tabular-nums;
}

/* رأس الخريطة */
.map-head {
    display        : flex;
    align-items    : center;
    justify-content: space-between;
    padding        : .7rem 1.5rem;
    border-bottom  : 1px solid var(--ink-100);
}
.map-head-title {
    font-size  : .8rem;
    font-weight: 700;
    color      : var(--ink-500);
}
.map-live-badge {
    font-size    : .65rem;
    font-weight  : 700;
    color        : var(--green-mid);
    background   : var(--green-lite);
    border       : 1px solid var(--green-bdr);
    padding      : 3px 9px;
    border-radius: 50px;
    letter-spacing: .05em;
    animation    : blink 2s ease-in-out infinite;
}

/* ── EMPTY / PLACEHOLDER ──────────────────────────────────── */
.placeholder {
    background   : var(--white);
    border       : 2px dashed var(--ink-100);
    border-radius: var(--r-lg);
    height       : 520px;
    display      : flex;
    flex-direction: column;
    align-items  : center;
    justify-content: center;
    text-align   : center;
    transition   : border-color .3s;
    animation    : fadeUp .5s .15s ease both;
}
.placeholder:hover { border-color:var(--gold-bdr); }
.ph-icon  {
    font-size  : 3.5rem;
    opacity    : .16;
    margin-bottom: .85rem;
    animation  : float 4s ease-in-out infinite;
}
.ph-title { font-size:.95rem; font-weight:700; color:var(--ink-200); margin-bottom:.4rem; }
.ph-desc  { font-size:.78rem; color:var(--ink-100); line-height:1.75; }

/* ── ALERTS ───────────────────────────────────────────────── */
div[data-testid="stAlert"] {
    border-radius: var(--r-sm) !important;
    background   : var(--gold-lite) !important;
    border       : 1px solid var(--gold-bdr) !important;
    border-left  : none !important;
    border-right : 3px solid var(--gold-mid) !important;
    color        : var(--ink-700) !important;
}
div[data-testid="stSpinner"] p {
    color    : var(--ink-300) !important;
    font-size: .8rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── زر GPS — تلوين ديناميكي ──────────────────────────────────────
if st.session_state.gps_active:
    st.markdown("""<style>
    div[data-testid="stButton"]>button {
        background:var(--green-lite) !important;
        border:1px solid var(--green-bdr) !important;
        color:var(--green) !important;
    }
    div[data-testid="stButton"]>button:hover {
        background:#d1fae5 !important;
        box-shadow:0 3px 12px rgba(5,150,105,.15) !important;
        transform:translateY(-2px) !important;
    }
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>
    div[data-testid="stButton"]>button {
        background:var(--surface) !important;
        border:1px solid var(--ink-100) !important;
        color:var(--ink-400) !important;
    }
    div[data-testid="stButton"]>button:hover {
        background:var(--gold-lite) !important;
        border-color:var(--gold-bdr) !important;
        color:var(--gold) !important;
        transform:translateY(-2px) !important;
    }
    </style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# 3.  بيانات الحدود
# ══════════════════════════════════════════════════════════════════
BOUNDARY_POINTS_1 = [
    (30.722009, 31.295623), (30.721122, 31.295481),
    (30.721285, 31.294259), (30.722031, 31.294366),
    (30.722009, 31.295623),
]

BOUNDARY_POINTS_2 = [
    (30.725045, 31.294755), (30.730125, 31.302278), (30.729349, 31.302003),
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
    (30.726883, 31.286281), (30.726529, 31.286324), (30.726393, 31.285772),
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
    (30.729515, 31.303288), (30.725045, 31.294755),
]


# ══════════════════════════════════════════════════════════════════
# 4.  المنطق والدوال
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def build_polygons():
    p1 = Polygon([(lon, lat) for lat, lon in BOUNDARY_POINTS_1])
    p2 = Polygon([(lon, lat) for lat, lon in BOUNDARY_POINTS_2])
    return p1, p2

polygon1, polygon2 = build_polygons()


def parse_dms(text: str):
    """تحليل صيغة DMS — مثال: 30°43'38.3\"N 31°17'4.7\"E"""
    parts = re.findall(r"(\d+)[°](\d+)['](\d+\.?\d*)[\"]([NSEW])", text)
    if len(parts) < 2:
        return None
    vals = []
    for d, m, s, direction in parts:
        v = float(d) + float(m) / 60 + float(s) / 3600
        if direction in ("S", "W"):
            v = -v
        vals.append(v)
    return tuple(vals[:2])


def parse_coords(text: str):
    """تحليل الإحداثيات — يقبل الصيغة العشرية و DMS"""
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
    """بناء خريطة Folium مع طبقات Google"""
    m = folium.Map(
        location=[lat, lon],
        zoom_start=16,
        prefer_canvas=True,
        control_scale=True,
        tiles=None,
    )

    # طبقتا خرائط Google
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="🛰️ أقمار صناعية",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps",
        name="🗺️ خريطة الشوارع",
    ).add_to(m)

    # حدود المنطقتين
    poly_style = dict(
        color="#d97706", weight=2.2,
        fillColor="#d97706", fillOpacity=0.07,
        dashArray="7 4",
    )
    folium.Polygon(
        locations=BOUNDARY_POINTS_1, **poly_style,
        tooltip="<b style='font-family:Cairo'>المنطقة الأولى</b>",
    ).add_to(m)
    folium.Polygon(
        locations=BOUNDARY_POINTS_2, **poly_style,
        tooltip="<b style='font-family:Cairo'>المنطقة الثانية</b>",
    ).add_to(m)

    # نقطة الموقع — حلقات متداخلة
    pin_color = "#059669" if is_inside else "#dc2626"
    status_ar = "✅ داخل الحيز" if is_inside else "⛔ خارج الحيز"

    for r, op in [(28, .07), (16, .14), (8, .38)]:
        folium.CircleMarker(
            location=[lat, lon], radius=r,
            color=pin_color, weight=1.5,
            fill=True, fill_color=pin_color, fill_opacity=op,
        ).add_to(m)

    folium.Marker(
        location=[lat, lon],
        tooltip=folium.Tooltip(
            f"""<div style='direction:rtl;text-align:right;
                font-family:Cairo,sans-serif;min-width:160px;padding:4px;'>
                <b style='font-size:13px;color:{pin_color}'>{status_ar}</b><br>
                <span style='color:#64748b;font-size:11px'>خط عرض: </span>
                <span style='font-size:11px'>{lat:.6f}</span><br>
                <span style='color:#64748b;font-size:11px'>خط طول: </span>
                <span style='font-size:11px'>{lon:.6f}</span>
            </div>""",
            permanent=False,
        ),
        icon=folium.Icon(
            color="green" if is_inside else "red",
            icon="map-marker", prefix="fa",
        ),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ══════════════════════════════════════════════════════════════════
# 5.  الواجهة
# ══════════════════════════════════════════════════════════════════

# ── الشريط العلوي ─────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="brand">
        <div class="brand-mark">🏙️</div>
        <div>
            <div class="brand-name">الحيز العمراني</div>
            <div class="brand-sub">نظام الاستعلام الجغرافي</div>
        </div>
    </div>
    <div class="live-pill">
        <span class="live-dot"></span>مباشر
    </div>
</div>
""", unsafe_allow_html=True)

# ── الـ Hero ───────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eye">استعلام جغرافي دقيق</div>
    <h1>الاستعلام عن <em>الحيز العمراني</em></h1>
    <p>
        تحقق فوري من موقع أي قطعة أرض أو مبنى داخل أو خارج
        النطاق العمراني المعتمد باستخدام إحداثياتك الجغرافية الدقيقة
    </p>
</div>
""", unsafe_allow_html=True)

# ── العمودان الرئيسيان ────────────────────────────────────────────
col_side, col_main = st.columns([1, 2.5], gap="medium")

# ════════════════════════════
#  العمود الأيسر — الإدخال
# ════════════════════════════
with col_side:

    # بطاقة GPS
    st.markdown("""
    <div class="card">
        <div class="card-head">
            <span class="card-icon">📡</span>
            <span class="card-title">تحديد الموقع عبر GPS</span>
        </div>
        <p class="card-hint">فعّل الزر لالتقاط إحداثياتك الحالية تلقائياً</p>
    """, unsafe_allow_html=True)

    st.button(
        "🟢  مفعّل — اضغط للإيقاف" if st.session_state.gps_active
        else "📍  تفعيل GPS",
        on_click=toggle_gps,
        use_container_width=True,
    )

    if st.session_state.gps_active:
        try:
            loc = get_geolocation(component_key="gps_loc")
            if loc and "coords" in loc:
                gps_lat = loc["coords"]["latitude"]
                gps_lon = loc["coords"]["longitude"]
                new_coords = f"{gps_lat:.6f}, {gps_lon:.6f}"
                if st.session_state.last_gps_coords != new_coords:
                    st.session_state.last_gps_coords = new_coords
                    st.session_state.coord_input     = new_coords
                    st.rerun()
                st.markdown(
                    '<div class="gps-ok"><span>●</span> تم التقاط الموقع بنجاح</div>',
                    unsafe_allow_html=True,
                )
        except Exception:
            pass

    st.markdown("</div>", unsafe_allow_html=True)

    # الفاصل
    st.markdown('<div class="or-div">أو أدخل يدوياً</div>', unsafe_allow_html=True)

    # بطاقة الإدخال اليدوي
    st.markdown("""
    <div class="card">
        <div class="card-head">
            <span class="card-icon">✏️</span>
            <span class="card-title">إدخال الإحداثيات</span>
        </div>
    """, unsafe_allow_html=True)

    with st.form("coord_form", clear_on_submit=False):
        user_input = st.text_input(
            "خط العرض ، خط الطول",
            value=st.session_state.coord_input,
            key="coord_input",
            placeholder="30.727313 , 31.284638",
            help='الصيغة العشرية: 30.727313, 31.284638  |  DMS: 30°43\'38.3"N 31°17\'4.7"E',
        )
        submitted = st.form_submit_button("🔍  بدء الفحص", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # تلميح
    st.markdown(
        '<div class="tip">💡 انسخ الإحداثيات مباشرةً من خرائط جوجل ولصقها هنا</div>',
        unsafe_allow_html=True,
    )


# ═════════════════════════════
#  العمود الأيمن — النتيجة
# ═════════════════════════════
with col_main:

    if submitted:
        if not user_input.strip():
            st.warning("الرجاء إدخال الإحداثيات أولاً قبل الفحص.")
        else:
            parsed = parse_coords(user_input)
            if parsed:
                lat, lon   = parsed
                pt         = Point(lon, lat)
                is_inside  = polygon1.contains(pt) or polygon2.contains(pt)

                # ── لوحة النتيجة ──
                st.markdown('<div class="result-panel">', unsafe_allow_html=True)

                if is_inside:
                    st.markdown("""
                    <div class="res-bar res-bar-in">
                        <span class="res-emoji">✅</span>
                        <div>
                            <div class="res-title res-title-in">
                                الموقع داخل الحيز العمراني المعتمد
                            </div>
                            <div class="res-desc">
                                ضمن النطاق الرسمي المعتمد للتخطيط العمراني
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="res-bar res-bar-out">
                        <span class="res-emoji">⛔</span>
                        <div>
                            <div class="res-title res-title-out">
                                الموقع خارج الحيز العمراني
                            </div>
                            <div class="res-desc">
                                خارج النطاق العمراني الرسمي المعتمد حالياً
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # ── سطر الإحداثيات ──
                st.markdown(f"""
                <div class="coords-row">
                    <span class="coords-dot"></span>
                    <div>
                        <div class="coords-lbl">الإحداثيات المفحوصة</div>
                        <div class="coords-val">{lat:.6f} &nbsp;,&nbsp; {lon:.6f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ── رأس الخريطة ──
                st.markdown("""
                <div class="map-head">
                    <span class="map-head-title">🗺️ الخريطة التفاعلية</span>
                    <span class="map-live-badge">● مباشر</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # ── الخريطة ──
                with st.spinner("جارٍ تحميل الخريطة…"):
                    folium_map = build_map(lat, lon, is_inside)
                    st_folium(folium_map, width="100%", height=465, returned_objects=[])

            else:
                st.error(
                    "صيغة الإحداثيات غير صحيحة. يرجى إدخالها بالشكل: **30.727313, 31.284638**"
                )

    else:
        # ── حالة الانتظار ──
        st.markdown("""
        <div class="placeholder">
            <div class="ph-icon">🗺️</div>
            <div class="ph-title">الخريطة التفاعلية</div>
            <div class="ph-desc">
                أدخل إحداثيات الموقع أو فعّل GPS<br>
                ثم اضغط «بدء الفحص» لعرض النتيجة
            </div>
        </div>
        """, unsafe_allow_html=True)
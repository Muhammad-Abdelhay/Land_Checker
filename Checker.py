import re
import streamlit as st
from shapely.geometry import Point, Polygon
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# ─────────────────────────────────────────────
# 1. إعدادات الصفحة (يجب أن تكون أول سطر)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="نظام الاستعلام عن الحيز العمراني",
    page_icon="🌍",
    layout="wide", # تحويل العرض ليكون كامل الشاشة
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 2. التنسيق (CSS) - ألوان احترافية وتصميم زجاجي
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

/* الإعدادات العامة بخط تجوال الاحترافي */
* { font-family: 'Tajawal', sans-serif !important; direction: rtl; text-align: right; }

.stApp {
    background: radial-gradient(circle at 50% 0%, #1a2a3a 0%, #0f1923 100%);
}

/* إخفاء القوائم الافتراضية */
#MainMenu, footer, header { display: none !important; }

/* الترويسة الرئيسية */
.main-header {
    background: rgba(0, 180, 216, 0.05);
    border: 1px solid rgba(0, 180, 216, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
.main-header h1 { color: #48cae4; font-size: 2.2rem; font-weight: 800; margin: 0; }
.main-header p { color: #ade8f4; margin: 0; font-size: 1rem; opacity: 0.8; }

/* البطاقات */
.custom-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* نتائج الفحص */
.result-banner {
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    animation: fadeIn 0.5s ease-in-out;
}
.result-inside {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.1));
    border: 1px solid #10b981;
    color: #34d399;
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
}
.result-outside {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1));
    border: 1px solid #ef4444;
    color: #f87171;
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.2);
}

/* الحركات (Animations) */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* تخصيص الأزرار */
div[data-testid="stButton"] > button {
    border-radius: 8px !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #0077b6, #00b4d8) !important;
    color: white !important;
    border: none !important;
    width: 100%;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4) !important;
    transform: translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. البيانات الأساسية (النقاط)
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
# 4. معالجة البيانات والدوال المساعدة
# ─────────────────────────────────────────────
@st.cache_resource
def build_polygons():
    return Polygon([(lon, lat) for lat, lon in BOUNDARY_POINTS_1]), \
           Polygon([(lon, lat) for lat, lon in BOUNDARY_POINTS_2])

polygon1, polygon2 = build_polygons()

def parse_dms(text: str):
    parts = re.findall(r"(\d+)[°](\d+)['](\d+\.?\d*)[\"]([NSEW])", text)
    if len(parts) < 2: return None
    results = []
    for deg, min_, sec, direction in parts:
        val = float(deg) + float(min_) / 60 + float(sec) / 3600
        if direction in ("S", "W"): val = -val
        results.append(val)
    return tuple(results[:2])

def parse_coords(text: str):
    try:
        parts = text.replace(",", " ").split()
        if len(parts) >= 2:
            lat, lon = float(parts[0]), float(parts[1])
            if -90 <= lat <= 90 and -180 <= lon <= 180: return lat, lon
    except ValueError: pass
    return parse_dms(text)

@st.cache_data(show_spinner=False)
def build_map(lat: float, lon: float, is_inside: bool):
    m = folium.Map(location=[lat, lon], zoom_start=16, prefer_canvas=True, control_scale=True)
    
    # إضافة طبقات الخرائط
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google", name="أقمار صناعية (Google)", overlay=False
    ).add_to(m)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google", name="خريطة الشوارع (Google)", overlay=False
    ).add_to(m)

    # تنسيق المضلعات
    poly_style = {"color": "#00b4d8", "weight": 2, "fillColor": "#00b4d8", "fillOpacity": 0.15}
    folium.Polygon(locations=BOUNDARY_POINTS_1, **poly_style, tooltip="المنطقة الأولى").add_to(m)
    folium.Polygon(locations=BOUNDARY_POINTS_2, **poly_style, tooltip="المنطقة الثانية").add_to(m)

    # نقطة الفحص
    status_text = "داخل الحيز" if is_inside else "خارج الحيز"
    color = "green" if is_inside else "red"
    
    # علامة الموقع
    folium.Marker(
        location=[lat, lon],
        tooltip=f"<div style='direction:rtl;text-align:right;'><b>{status_text}</b><br>Lat: {lat:.5f}<br>Lon: {lon:.5f}</div>",
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

    # دائرة حول الموقع لسهولة الرؤية
    folium.CircleMarker(
        location=[lat, lon], radius=15, color=color, fill=True, fill_opacity=0.3
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m

# ─────────────────────────────────────────────
# 5. واجهة المستخدم (UI Layout)
# ─────────────────────────────────────────────
# الترويسة
st.markdown("""
<div class="main-header">
    <div>
        <h1>الاستعلام عن الحيز العمراني</h1>
        <p>نظام ذكي للتحقق من وقوع الأراضي والمباني داخل أو خارج النطاق العمراني المعتمد</p>
    </div>
</div>
""", unsafe_allow_html=True)

# تقسيم الشاشة إلى عمودين (للمدخلات وللنتائج)
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown('### 📡 تحديد الموقع تلقائياً')
    st.write("التقط إحداثياتك الحالية باستخدام GPS جهازك.")
    
    try:
        loc = get_geolocation(component_key="get_loc")
        if loc and "coords" in loc:
            gps_lat, gps_lon = loc["coords"]["latitude"], loc["coords"]["longitude"]
            st.session_state.input_coords = f"{gps_lat:.6f}, {gps_lon:.6f}"
            st.toast(f"تم التقاط الموقع بنجاح!", icon="✅")
    except Exception:
        pass
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.markdown('### ✍️ إدخال الإحداثيات يدوياً')
    
    # استخدام st.form لتنظيم الإدخال ودعم زر Enter
    with st.form("coord_form"):
        user_input = st.text_input(
            "أدخل خط العرض وخط الطول:", 
            value=st.session_state.get("input_coords", ""),
            placeholder="مثال: 30.727313, 31.284638",
            help="يمكنك إدخال الصيغة العشرية أو صيغة الدرجات (DMS)"
        )
        submitted = st.form_submit_button("🔍 بدء الفحص والاستعلام")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    if submitted:
        if not user_input.strip():
            st.warning("⚠️ الرجاء إدخال الإحداثيات أولاً قبل الفحص.")
        else:
            parsed = parse_coords(user_input)
            if parsed:
                lat, lon = parsed
                point = Point(lon, lat)
                
                # المعالجة: التحقق من وجود النقطة في أي من المضلعين
                is_inside = polygon1.contains(point) or polygon2.contains(point)
                
                # عرض النتيجة بشكل بارز
                if is_inside:
                    st.markdown('<div class="result-banner result-inside">✅ الموقع المختار يقع داخل الحيز العمراني المعتمد</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="result-banner result-outside">⛔ الموقع المختار يقع خارج الحيز العمراني</div>', unsafe_allow_html=True)
                
                # عرض الخريطة
                with st.spinner("جارٍ إعداد الخريطة التفاعلية..."):
                    m = build_map(lat, lon, is_inside)
                    st_folium(m, width="100%", height=500, returned_objects=[])
                    
                # عرض تفاصيل الإحداثيات
                st.info(f"📌 الإحداثيات المستخدمة: **{lat:.6f} , {lon:.6f}**")
            else:
                st.error("❌ صيغة الإحداثيات غير صحيحة. يرجى التأكد من الأرقام والفواصل.")
    else:
        # شاشة الترحيب قبل الفحص
        st.markdown("""
        <div style="height: 500px; display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 0.5; border: 2px dashed rgba(255,255,255,0.1); border-radius: 12px;">
            <h1 style="font-size: 4rem; margin-bottom: 0;">🗺️</h1>
            <h3>الخريطة التفاعلية</h3>
            <p>أدخل الإحداثيات في اللوحة الجانبية واضغط على "بدء الفحص" لظهور النتيجة هنا.</p>
        </div>
        """, unsafe_allow_html=True)
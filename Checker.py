import streamlit as st
import xml.etree.ElementTree as ET
from shapely.geometry import Point, Polygon
import os
import folium
from streamlit_folium import st_folium

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="محدد الحيز العمراني المطور", page_icon="🌍")

# --- 2. كود الإخفاء (CSS) ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp > header {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. دوال قراءة ملف KML (كما هي في كودك القديم) ---
KML_FILE_NAME = 'Outer_Boundary_Only.kml'

def load_kml_boundary(file_path):
    """قراءة ملف الخريطة وتحويله إلى شكل هندسي"""
    if not os.path.exists(file_path):
        st.error(f"⚠️ خطأ: ملف الخريطة '{file_path}' غير موجود!")
        return None, None, []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
        coordinates_text = ""
        # البحث عن الإحداثيات داخل ملف KML
        for coord_elem in root.findall('.//kml:coordinates', namespace):
            coordinates_text += coord_elem.text + " "
            
        points = []
        folium_coords = [] 
        
        # معالجة النصوص وتحويلها لأرقام
        for coords in coordinates_text.strip().split():
            try:
                parts = coords.split(',')
                lon = float(parts[0])
                lat = float(parts[1])
                points.append((lon, lat))     # صيغة (X, Y) للمكتبة الهندسية
                folium_coords.append((lat, lon)) # صيغة (Lat, Lon) لرسم الخريطة
            except:
                continue
        
        if len(points) > 2:
            poly = Polygon(points)
            # نرجع المضلع + نقطة المنتصف (لتركيز الخريطة عليها في البداية) + إحداثيات الرسم
            return poly, poly.centroid, folium_coords
        return None, None, []
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
        return None, None, []

# --- 4. تحميل البيانات وإعداد الجلسة (Session State) ---

# تحميل الحدود
boundary_polygon, centroid, boundary_coords_visual = load_kml_boundary(KML_FILE_NAME)

# تحديد نقطة البداية الافتراضية (إما منتصف الحيز أو نقطة عامة)
default_lat = centroid.y if centroid else 30.0
default_lon = centroid.x if centroid else 31.0

# تهيئة الذاكرة للربط بين الخريطة والإدخال اليدوي
if 'lat' not in st.session_state:
    st.session_state.lat = default_lat
if 'lng' not in st.session_state:
    st.session_state.lng = default_lon

# --- 5. واجهة التطبيق ---
st.title("🌍 كشف الحيز العمراني (Hybrid)")
st.write("اضغط على موقع الأرض في الخريطة أو أدخل الإحداثيات يدوياً.")

# خانات الإدخال (مرتبطة بالذاكرة key)
col1, col2 = st.columns(2)
with col1:
    st.number_input("دائرة العرض (Latitude)", value=st.session_state.lat, format="%.6f", key='lat')
with col2:
    st.number_input("خط الطول (Longitude)", value=st.session_state.lng, format="%.6f", key='lng')

# --- 6. إعداد ورسم الخريطة ---

# إنشاء الخريطة بمركزها الحالي
m = folium.Map(location=[st.session_state.lat, st.session_state.lng], zoom_start=17)

# أ) إضافة طبقة Google Satellite Hybrid (أقمار صناعية + شوارع)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google',
    name='Google Satellite',
    overlay=False,
    control=True
).add_to(m)

# ب) رسم حدود الحيز العمراني (الأصفر)
if boundary_coords_visual:
    folium.Polygon(
        locations=boundary_coords_visual,
        color="yellow",
        weight=3,
        fill=True,
        fill_opacity=0.1,
        popup="حدود الحيز العمراني"
    ).add_to(m)

# ج) رسم دبوس الموقع الحالي
folium.Marker(
    [st.session_state.lat, st.session_state.lng],
    popup="الموقع المحدد",
    icon=folium.Icon(color="red", icon="info-sign")
).add_to(m)

# د) إضافة زر التحكم في الطبقات
folium.LayerControl().add_to(m)

# هـ) عرض الخريطة وتفعيل التفاعل
st.write("👇 **الخريطة تفاعلية: اضغط لتغيير الموقع**")
map_data = st_folium(m, width=700, height=500)

# --- 7. منطق التحديث عند الضغط ---
if map_data['last_clicked']:
    clicked_lat = map_data['last_clicked']['lat']
    clicked_lng = map_data['last_clicked']['lng']
    
    # التحقق هل تغير الموقع؟ إذا نعم، نحدث الذاكرة ونعيد التحميل
    # (نستخدم تقريب بسيط لتجنب التحديث اللانهائي بسبب الفواصل العشرية الدقيقة)
    if abs(clicked_lat - st.session_state.lat) > 0.000001 or abs(clicked_lng - st.session_state.lng) > 0.000001:
        st.session_state.lat = clicked_lat
        st.session_state.lng = clicked_lng
        st.rerun()

# --- 8. الفحص وإظهار النتيجة ---
st.markdown("---")

if boundary_polygon:
    # تكوين النقطة من الإحداثيات الحالية
    user_point = Point(st.session_state.lng, st.session_state.lat) # انتبه: Shapely تأخذ (Lon, Lat)
    is_inside = boundary_polygon.contains(user_point)

    if is_inside:
        st.success(f"✅ مبروك! الموقع ({st.session_state.lat:.5f}, {st.session_state.lng:.5f}) يقع **داخل** الحيز العمراني.")
    else:
        st.error(f"❌ الموقع ({st.session_state.lat:.5f}, {st.session_state.lng:.5f}) يقع **خارج** الحيز العمراني.")
else:
    st.warning("⚠️ لم يتم تحميل ملف الحدود، لا يمكن إجراء الفحص.")
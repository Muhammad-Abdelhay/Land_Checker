import streamlit as st
import xml.etree.ElementTree as ET
from shapely.geometry import Point, Polygon
import os
import re
import folium
from streamlit_folium import st_folium
# 1. استدعاء مكتبة تحديد الموقع
from streamlit_js_eval import get_geolocation

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Urban Cordon Checker", page_icon="🌍")

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

# --- 3. تهيئة ذاكرة الجلسة (Session State) ---
if 'search_result' not in st.session_state:
    st.session_state.search_result = None

# تهيئة متغير لتخزين النص المكتوب في الخانة (للربط مع GPS)
if 'input_coords' not in st.session_state:
    st.session_state.input_coords = ""

# --- 4. المتغيرات والدوال ---
KML_FILE_NAME = 'Outer_Boundary_Only.kml'

def convert_dms_to_decimal(dms_string):
    """تحويل الإحداثيات من صيغة الدرجات والدقائق إلى عشري"""
    try:
        parts = re.findall(r"(\d+)[°](\d+)['](\d+\.?\d*)[\"]([NSEW])", dms_string)
        decimals = []
        for part in parts:
            deg = float(part[0])
            min_ = float(part[1])
            sec = float(part[2])
            direction = part[3]
            val = deg + (min_ / 60) + (sec / 3600)
            if direction in ['S', 'W']: val = -val
            decimals.append(val)
        
        if len(decimals) == 2:
            return decimals[0], decimals[1]
        return None
    except:
        return None

def load_kml_boundary(file_path):
    """قراءة ملف الخريطة وتحويله إلى شكل هندسي"""
    if not os.path.exists(file_path):
        st.error(f"⚠️ خطأ: ملف الخريطة '{file_path}' غير موجود!")
        return None, []

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
        coordinates_text = ""
        for coord_elem in root.findall('.//kml:coordinates', namespace):
            coordinates_text += coord_elem.text + " "
            
        points = []
        folium_coords = [] 
        
        for coords in coordinates_text.strip().split():
            try:
                parts = coords.split(',')
                lon = float(parts[0])
                lat = float(parts[1])
                points.append((lon, lat))
                folium_coords.append((lat, lon))
            except:
                continue
        
        if len(points) > 2:
            return Polygon(points), folium_coords
        return None, []
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
        return None, []

# --- 5. واجهة التطبيق ---
st.title("🌍 كشف الحيز العمراني (مشروع كاردون)")
st.write("أدخل إحداثيات قطعة الأرض أو استخدم موقعك الحالي.")

# --- إضافة زر GPS ---
loc = get_geolocation(component_key='get_loc', btn_text='📍 اضغط هنا لتحديد موقعك الحالي')

# إذا تم العثور على الموقع، نقوم بتحديث خانة الكتابة تلقائياً
if loc:
    current_lat = loc['coords']['latitude']
    current_lon = loc['coords']['longitude']
    # تحديث النص في الذاكرة
    st.session_state.input_coords = f"{current_lat}, {current_lon}"

# تحميل الحدود مرة واحدة
boundary_polygon, boundary_coords_visual = load_kml_boundary(KML_FILE_NAME)

if boundary_polygon:
    # خانة الإدخال (تم ربطها بـ session_state لتتحدث مع الـ GPS)
    user_input = st.text_input("📍 الإحداثيات:", key='input_coords', placeholder="مثال: 30.727313, 31.284638")

    # زر الفحص
    if st.button("فحص الموقع ورسم الخريطة"):
        if user_input:
            lat = None
            lon = None
            
            # محاولة قراءة الصيغة العشرية
            try:
                clean_input = user_input.replace(',', ' ').split()
                if len(clean_input) >= 2:
                    lat = float(clean_input[0])
                    lon = float(clean_input[1])
            except:
                pass

            # محاولة قراءة الدرجات والدقائق
            if lat is None:
                dms_result = convert_dms_to_decimal(user_input)
                if dms_result:
                    lat, lon = dms_result

            # تخزين النتيجة في الذاكرة لكي لا تختفي
            if lat is not None and lon is not None:
                point = Point(lon, lat)
                is_inside = boundary_polygon.contains(point)
                
                # حفظ البيانات في Session State
                st.session_state.search_result = {
                    'lat': lat,
                    'lon': lon,
                    'is_inside': is_inside
                }
            else:
                st.warning("❌ لم يتم التعرف على الإحداثيات. تأكد من الأرقام.")
                st.session_state.search_result = None

    # --- عرض النتيجة والخريطة (من الذاكرة) ---
    if st.session_state.search_result is not None:
        result = st.session_state.search_result
        lat = result['lat']
        lon = result['lon']
        is_inside = result['is_inside']

        st.markdown("---") # فاصل خطي

        # 1. عرض النتيجة النصية
        if is_inside:
            st.success("✅ النتيجة: الأرض **داخل** الحيز العمراني (مبروك!) 🏘️")
        else:
            st.error("⛔ النتيجة: الأرض **خارج** الحيز العمراني. 🌾")
        
        st.info(f"الإحداثيات: {lat}, {lon}")

        # 2. رسم الخريطة
        st.write("### 🗺️ الخريطة التوضيحية:")
        
        m = folium.Map(location=[lat, lon], zoom_start=16)

        # رسم الحيز
        folium.Polygon(
            locations=boundary_coords_visual,
            color="yellow",
            weight=4,
            fill=True,
            fill_opacity=0.2,
            popup="حدود الحيز العمراني"
        ).add_to(m)

        # رسم الدبوس
        folium.Marker(
            [lat, lon],
            popup=f"موقع الأرض\n({is_inside and 'داخل الحيز' or 'خارج الحيز'})",
            icon=folium.Icon(color="red" if not is_inside else "green", icon="info-sign")
        ).add_to(m)

        st_folium(m, width=700, height=500)
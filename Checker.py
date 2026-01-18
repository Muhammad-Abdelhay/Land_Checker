import streamlit as st
import xml.etree.ElementTree as ET
from shapely.geometry import Point, Polygon
import os
import re

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Urban Cordon Checker", page_icon="🌍")

# اسم ملف الخريطة
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
            return decimals[0], decimals[1] # Lat, Lon
        return None
    except:
        return None

def load_kml_boundary(file_path):
    """قراءة ملف الخريطة وتحويله إلى شكل هندسي"""
    if not os.path.exists(file_path):
        st.error(f"⚠️ خطأ: ملف الخريطة '{file_path}' غير موجود!")
        return None

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
        coordinates_text = ""
        for coord_elem in root.findall('.//kml:coordinates', namespace):
            coordinates_text += coord_elem.text + " "
            
        points = []
        for coords in coordinates_text.strip().split():
            try:
                parts = coords.split(',')
                lon = float(parts[0])
                lat = float(parts[1])
                points.append((lon, lat))
            except:
                continue
        
        if len(points) > 2:
            return Polygon(points)
        return None
    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
        return None

# --- واجهة التطبيق ---
st.title("🌍 كشف الحيز العمراني (مشروع كاردون)")
st.write("أدخل إحداثيات قطعة الأرض لمعرفة هل هي داخل الحيز العمراني أم لا.")

# تحميل الحدود
boundary = load_kml_boundary(KML_FILE_NAME)

if boundary:
    # خانة إدخال البيانات
    user_input = st.text_input("📍 أدخل الإحداثيات هنا (يقبل الصيغة العشرية أو الدرجات والدقائق):", placeholder="مثال: 30.742, 31.298 أو 30°44'00.5\"N...")

    if st.button("فحص الموقع"):
        if user_input:
            lat = None
            lon = None
            
            # محاولة قراءة الصيغة العشرية المباشرة
            try:
                clean_input = user_input.replace(',', ' ').split()
                if len(clean_input) >= 2:
                    lat = float(clean_input[0])
                    lon = float(clean_input[1])
            except:
                pass

            # إذا فشل العشري، نجرب صيغة الدرجات والدقائق
            if lat is None:
                dms_result = convert_dms_to_decimal(user_input)
                if dms_result:
                    lat, lon = dms_result

            # الفحص النهائي
            if lat is not None and lon is not None:
                # ملاحظة: Shapely تستخدم (x, y) يعني (Longitude, Latitude)
                point = Point(lon, lat)
                
                if boundary.contains(point):
                    st.success("✅ النتيجة: الأرض **داخل** الحيز العمراني (مبروك!) 🏘️")
                    st.balloons()
                else:
                    st.error("⛔ النتيجة: الأرض **خارج** الحيز العمراني. 🌾")
                
                st.info(f"الإحداثيات التي تم فحصها: \n خط العرض: {lat} \n خط الطول: {lon}")
            else:
                st.warning("❌ لم يتم التعرف على الإحداثيات. تأكد من نسخها بشكل صحيح من خرائط جوجل.")
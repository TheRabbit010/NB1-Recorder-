import pandas as pd
import streamlit as st

st.title("📊 สร้างกราฟจากไฟล์ Excel และ CSV")

# 1. ส่วนสำหรับอัปโหลดไฟล์
uploaded_file = st.file_uploader(
    "อัปโหลดไฟล์ของคุณ (CSV หรือ Excel)", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
  # ตรวจสอบนามสกุลไฟล์เพื่ออ่านข้อมูลให้ถูกต้อง
  try:
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)

    st.success("อัปโหลดไฟล์สำเร็จ!")

    # แสดงตัวอย่างข้อมูล
    st.subheader("📋 ตัวอย่างข้อมูลในตาราง")
    st.dataframe(df.head())

    # เลือกคอลัมน์สำหรับทำกราฟ
    st.subheader("📈 ตั้งค่าการสร้างกราฟ")
    columns = df.columns.tolist()

    # เลือกแกน X และแกน Y
    x_axis = st.selectbox("เลือกข้อมูลแกน X", columns)
    y_axis = st.selectbox("เลือกข้อมูลแกน Y", columns)

    # เลือกประเภทของกราฟ
    chart_type = st.radio(
        "เลือกประเภทกราฟ", ["Line Chart", "Bar Chart", "Area Chart"]
    )

    # แสดงกราฟตามประเภทที่ผู้ใช้เลือก
    if chart_type == "Line Chart":
      st.line_chart(df.set_index(x_axis)[y_axis])
    elif chart_type == "Bar Chart":
      st.bar_chart(df.set_index(x_axis)[y_axis])
    elif chart_type == "Area Chart":
      st.area_chart(df.set_index(x_axis)[y_axis])

  except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
else:
    st.info("โปรดอัปโหลดไฟล์ CSV หรือ Excel เพื่อเริ่มต้นใช้งาน")


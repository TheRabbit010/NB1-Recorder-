import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(layout="wide")  # ปรับหน้าจอให้กว้างเพื่อแสดงกราฟได้ชัดเจน
st.title("📊 Industrial Data Viewer (Interactive Graph)")

# 1. ส่วนสำหรับอัปโหลดไฟล์
uploaded_file = st.file_uploader(
    "อัปโหลดไฟล์ของคุณ (CSV, XLSX, XLS)", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
  try:
    # รองรับการอ่านไฟล์ทุกรูปแบบ รวมถึง .xls นามสกุลเก่า
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xls"):
      df = pd.read_excel(uploaded_file, engine="xlrd")
    else:
      df = pd.read_excel(uploaded_file, engine="openpyxl")

    st.success("อัปโหลดและอ่านข้อมูลสำเร็จ!")

    # ค้นหาคอลัมน์ที่เป็นเวลาอัตโนมัติ หรือให้ผู้ใช้เลือก แกน X
    columns = df.columns.tolist()
    st.sidebar.header("⚙️ ตั้งค่าแกนเวลา (X-Axis)")
    x_axis = st.sidebar.selectbox(
        "เลือกคอลัมน์ที่เป็น Date & Time",
        columns,
        index=0 if len(columns) > 0 else 0,
    )

    # แปลงข้อมูลแกน X ให้เป็นรูปแบบ DateTime
    df[x_axis] = pd.to_datetime(df[x_axis], errors="coerce")
    df = df.dropna(subset=[x_axis]).sort_values(by=x_axis)

    # 2. เมนูเลือกกลุ่มกราฟ (5 กลุ่มตามที่ระบุ)
    st.subheader("📈 เลือกกลุ่มข้อมูลที่ต้องการแสดง")
    group_option = st.radio(
        "กลุ่มข้อมูล:",
        [
            "1. Brazing zone Top #1-#7 (400-650°C)",
            "2. Brazing zone Bottom #1-#7 (400-650°C)",
            "3. Dryer #1 & #2 (0-400°C)",
            "4. ppmO2 Entry/Exit & N2 Flow (Dual Y-Axes)",
            "5. Dew point (-100 ถึง 10°Cdp)",
        ],
        horizontal=True,
    )

    # สร้างอินสแตนซ์ของกราฟ Plotly
    fig = go.Figure()

    # ทำฟังก์ชันจับคู่ชื่อคอลัมน์ (ช่วยค้นหาคำใกล้เคียงในไฟล์ Excel ของคุณ)
    def get_matching_cols(keywords):
      return [
          c
          for c in columns
          if any(k.lower() in str(c).lower() for k in keywords)
      ]

    # กำหนดค่าเริ่มต้นของรูปแบบแกน Y
    y_layout = dict(
        title="อุณหภูมิ (°C)",
        gridcolor="rgba(128,128,128,0.2)",
        zeroline=False,
    )
    y_layout_2 = None

    # วาดกราฟตามกลุ่มที่เลือก
    if "1. Brazing zone Top" in group_option:
      # หาคอลัมน์ที่มีคำว่า Top และ Zone หรือ #1-#7
      target_cols = get_matching_cols(["top"])
      if not target_cols:
        target_cols = columns[1:8]  # ถ้าไม่เจอให้เดาว่าเป็นคอลัมน์แรกๆ

      for col in target_cols:
        fig.add_trace(go.Scatter(x=df[x_axis], y=df[col], name=col, mode="lines"))
      y_layout.update(range=[400, 650], title="Temperature Top (°C)")

    elif "2. Brazing zone Bottom" in group_option:
      target_cols = get_matching_cols(["bottom", "bot"])
      if not target_cols:
        target_cols = columns[8:15]

      for col in target_cols:
        fig.add_trace(go.Scatter(x=df[x_axis], y=df[col], name=col, mode="lines"))
      y_layout.update(range=[400, 650], title="Temperature Bottom (°C)")

    elif "3. Dryer" in group_option:
      target_cols = get_matching_cols(["dryer", "dry"])
      if not target_cols:
        target_cols = columns[1:3]

      for col in target_cols:
        fig.add_trace(go.Scatter(x=df[x_axis], y=df[col], name=col, mode="lines"))
      y_layout.update(range=[0, 400], title="Dryer Temperature (°C)")

    elif "4. ppmO2 Entry/Exit" in group_option:
      # ใช้ฟีเจอร์แกน Y 2 ฝั่ง (Dual Y-Axis)
      fig = make_subplots(specs=[[{"secondary_y": True}]])

      # คอลัมน์สำหรับแกน Y ซ้าย (ppmO2)
      o2_cols = get_matching_cols(["o2", "ppm", "oxygen"])
      # คอลัมน์สำหรับแกน Y ขวา (N2 Flow)
      n2_cols = get_matching_cols(["n2", "flow"])

      # หากค้นหาชื่อไม่เจอ จะใช้คอลัมน์จำลองเพื่อไม่ให้โค้ดพัง
      if not o2_cols:
        o2_cols = [c for c in columns if c != x_axis][:2]
      if not n2_cols:
        n2_cols = [c for c in columns if c != x_axis][-1:]

      for col in o2_cols:
        fig.add_trace(
            go.Scatter(x=df[x_axis], y=df[col], name=col, mode="lines"),
            secondary_y=False,
        )
      for col in n2_cols:
        fig.add_trace(
            go.Scatter(x=df[x_axis], y=df[col], name=col, mode="lines"),
            secondary_y=True,
        )

      y_layout.update(range=[0, 200], title="Oxygen Level (ppm)")
      y_layout_2 = dict(
          title="N2 Flow Rate (Free Scale)",
          showgrid=False,
          overlaying="y",
          side="right",
      )

    elif "5. Dew point" in group_option:
      target_cols = get_matching_cols(["dew", "dp", "point"])
      if not target_cols:
        target_cols = [columns[-1]]

      for col in target_cols:
        fig.add_trace(go.Scatter(x=df[x_axis], y=df[col], name=col, mode="lines"))
      # ตั้งสเกลจาก 10 ลงไปหา -100 (ตามโจทย์ระบุ 10 to -100)
      y_layout.update(range=[10, -100], title="Dew Point (°Cdp)")

    # 3. ตกแต่งหน้าตากราฟให้ธีมมืดและดูเป็นเครื่องจักร/อุตสาหกรรมเหมือนรูปตัวอย่าง
    fig.update_layout(
        template="plotly_dark",  # ใช้ธีมสีเข้มเหมือนหน้าจอโรงงาน
        plot_bgcolor="#222222",  # สีพื้นหลังกราฟ
        paper_bgcolor="#111111",  # สีพื้นหลังแดชบอร์ด
        hovermode="x unified",  # แสดงค่าของทุกเส้นพร้อมกันเมื่อเอาเมาส์ไปชี้
        xaxis=dict(
            title="Absolute Time [h:m:s]",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)",
            rangeslider=dict(visible=True),  # แถบสไลด์ด้านล่างสำหรับซูมเวลา
            type="date",
        ),
        yaxis=y_layout,
        height=600,
        margin=dict(l=50, r=50, t=30, b=50),
    )

    if y_layout_2:
      fig.update_layout(yaxis2=y_layout_2)

    # แสดงผลกราฟบนหน้าเว็บ
    st.plotly_chart(fig, use_container_width=True)

    # แสดงตารางข้อมูลดิบด้านล่างกราฟ
    with st.expander("📋 ดูข้อมูลดิบทั้งหมด (Raw Data)"):
      st.dataframe(df)

  except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {e}")
    st.info(
        "คำแนะนำ: ตรวจสอบให้แน่ใจว่าได้เลือกคอลัมน์แกน X เป็นวันที่/เวลา และในไฟล์มีคอลัมน์ชื่อตรงตามกลุ่มข้อมูล"
    )

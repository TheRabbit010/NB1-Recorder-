import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(layout="wide")
st.title("📊 แดชบอร์ดแสดงผลกราฟอุตสาหกรรม (Yokogawa DX2000 Data)")

# 1. ฟังก์ชันแปลงไฟล์ดิบให้เป็น DataFrame ที่พร้อมใช้งาน
@st.cache_data
def load_and_clean_data(file):
  # อ่านไฟล์ข้ามหัว 27 แถวแรก เพื่อเอาเฉพาะส่วนตารางข้อมูล
  raw_df = pd.read_csv(file, skiprows=27, header=None)

  # สร้างชื่อคอลัมน์รวมเพื่อป้องกันชื่อซ้ำ (รวมแถว Ch + Tag + MIN/MAX)
  # ข้อมูลจริงในไฟล์ของคุณระบุโครงสร้างดังนี้:
  # คอลัมน์ 0: Date, คอลัมน์ 1: Time, คอลัมน์ 2: sec
  # คอลัมน์ 3 เป็นต้นไปคือค่า MIN/MAX สลับกันของแต่ละ Ch.

  # สร้าง DataFrame ใหม่เพื่อเก็บข้อมูลที่จะใช้พล็อต
  df = pd.DataFrame()
  df["DateTime"] = pd.to_datetime(
      raw_df[0] + " " + raw_df[1], errors="coerce"
  )

  # รายชื่อคอลัมน์ตามตำแหน่งพล็อตจริง (อิงเฉพาะค่า MAX เพื่อสร้างเส้นกราฟเดี่ยว)
  # สูตรคำนวณตำแหน่งคอลัมน์ค่า MAX = 3 + (Ch_Index * 2) + 1
  # หัวข้อ Ch และ Tag ตรงกับโครงสร้างข้อมูลในไฟล์จริงของคุณ

  # --- กลุ่มที่ 1 & 2: Brazing Zone Top & Bottom (#1 - #7) ---
  # จากหัวตาราง CH001 ถึง CH007 ชุดแรกคือ Top, CH001 ถึง CH007 ชุดสองคือ Bottom
  for i in range(1, 8):
    df[f"Top Zone #{i}"] = pd.to_numeric(
        raw_df[3 + ((i - 1) * 2) + 1], errors="coerce"
    )

  # ตัวแปรสำหรับจับคู่ Bottom (CH001-CH007 ชุดที่สอง อยู่ตำแหน่งคอลัมน์ถัดไป)
  bottom_start_ch = 19  # ตำแหน่ง Ch index ในตารางของ Bottom
  for i in range(1, 8):
    ch_idx = bottom_start_ch + (i - 1)
    # ค้นหาตำแหน่งตามโครงสร้างจริงในตาราง
    df[f"Bottom Zone #{i}"] = pd.to_numeric(
        raw_df[3 + (ch_idx * 2) + 1], errors="coerce"
    )

  # --- กลุ่มที่ 3: Dryer #1 & Dryer #2 ---
  # ในไฟล์ของคุณ Dryer #1 และ Dryer #2 ถูกระบุชัดเจนที่ตำแหน่ง Tag คอลัมน์กลางๆ
  # จับคู่จากตำแหน่งคำว่า "Dryer #1" และ "Dryer #2" ในไฟล์จริง
  df["Dryer #1"] = pd.to_numeric(
      raw_df[3 + (15 * 2) + 1], errors="coerce"
  )  # อ้างอิงจากตำแหน่งตาราง
  df["Dryer #2"] = pd.to_numeric(raw_df[3 + (16 * 2) + 1], errors="coerce")

  # --- กลุ่มที่ 4: ppmO2 & N2 Flow ---
  df["ENTRANCE O2"] = pd.to_numeric(
      raw_df[3 + (14 * 2) + 1], errors="coerce"
  )  # ซ้าย (0-200 ppm)
  df["EXIT O2"] = pd.to_numeric(
      raw_df[3 + (13 * 2) + 1], errors="coerce"
  )  # ซ้าย (0-200 ppm)
  df["N2 Flow"] = pd.to_numeric(
      raw_df[3 + (17 * 2) + 1], errors="coerce"
  )  # ขวา (Free Scale)

  # --- กลุ่มที่ 5: Dew point ---
  df["DEW POINT"] = pd.to_numeric(
      raw_df[3 + (18 * 2) + 1], errors="coerce"
  )  # สเกล 10 ถึง -100

  # ลบข้อมูลแถวที่เวลาเป็น NaTออก
  df = df.dropna(subset=["DateTime"]).sort_values("DateTime")
  return df


# ส่วนอัปโหลดไฟล์ใน Streamlit
uploaded_file = st.file_uploader(
    "อัปโหลดไฟล์ข้อมูลเครื่องบันทึก (CSV)", type=["csv"]
)

if uploaded_file is not None:
  try:
    df = load_and_clean_data(uploaded_file)
    st.success("🤖 ประมวลผลโครงสร้างไฟล์ Yokogawa DX2000 สำเร็จ!")

    # เมนูกราฟ 5 กลุ่มหลักตามโจทย์
    st.subheader("📈 เลือกกลุ่มข้อมูลเพื่อแสดงผลกราฟ")
    group_option = st.radio(
        "กลุ่มข้อมูล:",
        [
            "1. Brazing zone Top #1-#7 (สเกล 400-650°C)",
            "2. Brazing zone Bottom #1-#7 (สเกล 400-650°C)",
            "3. Dryer #1 & #2 (สเกล 0-400°C)",
            "4. ppmO2 & N2 Flow (แกน Y ซ้าย-ขวา)",
            "5. Dew point (สเกล 10 ถึง -100°Cdp)",
        ],
        horizontal=True,
    )

    fig = go.Figure()
    y_layout = dict(
        gridcolor="rgba(128,128,128,0.15)",
        zeroline=False,
        linecolor="#888888",
    )
    y_layout_2 = None

    # ลูปวาดกราฟและล็อกสเกลตามเงื่อนไขแต่ละกลุ่ม
    if "1. Brazing zone Top" in group_option:
      for i in range(1, 8):
        name = f"Top Zone #{i}"
        fig.add_trace(
            go.Scatter(x=df["DateTime"], y=df[name], name=name, mode="lines")
        )
      y_layout.update(range=[400, 650], title="Temperature Top (°C)")

    elif "2. Brazing zone Bottom" in group_option:
      for i in range(1, 8):
        name = f"Bottom Zone #{i}"
        fig.add_trace(
            go.Scatter(x=df["DateTime"], y=df[name], name=name, mode="lines")
        )
      y_layout.update(range=[400, 650], title="Temperature Bottom (°C)")

    elif "3. Dryer" in group_option:
      fig.add_trace(
          go.Scatter(
              x=df["DateTime"], y=df["Dryer #1"], name="Dryer #1", mode="lines"
          )
      )
      fig.add_trace(
          go.Scatter(
              x=df["DateTime"], y=df["Dryer #2"], name="Dryer #2", mode="lines"
          )
      )
      y_layout.update(range=[0, 400], title="Dryer Temperature (°C)")

    elif "4. ppmO2 & N2 Flow" in group_option:
      # ใช้เทคนิคแกน Y ซ้ายขวา (Secondary Y)
      fig = make_subplots(specs=[[{"secondary_y": True}]])

      # แกนซ้าย (ppmO2)
      fig.add_trace(
          go.Scatter(
              x=df["DateTime"], y=df["ENTRANCE O2"], name="ENTRANCE O2", mode="lines"
          ),
          secondary_y=False,
      )
      fig.add_trace(
          go.Scatter(
              x=df["DateTime"], y=df["EXIT O2"], name="EXIT O2", mode="lines"
          ),
          secondary_y=False,
      )
      # แกนขวา (N2 Flow)
      fig.add_trace(
          go.Scatter(
              x=df["DateTime"], y=df["N2 Flow"], name="N2 Flow Rate", mode="lines"
          ),
          secondary_y=True,
      )

      y_layout.update(range=[0, 200], title="Oxygen Level (ppm)")
      y_layout_2 = dict(
          title="N2 Flow Rate (Free Scale)",
          showgrid=False,
          overlaying="y",
          side="right",
          linecolor="#ff7f0e",
      )

    elif "5. Dew point" in group_option:
      fig.add_trace(
          go.Scatter(
              x=df["DateTime"],
              y=df["DEW POINT"],
              name="Dew Point",
              mode="lines",
              line=dict(color="#00ecff"),
          )
      )
      # ล็อกค่าจากมากไปน้อย 10 ถึง -100 ตามโจทย์
      y_layout.update(range=[10, -100], title="Dew Point (°Cdp)")

    # ปรับแต่งธีมของกราฟให้เป็น Industrial Dark Theme ตามภาพตัวอย่างของคุณ
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#1f1f1f",  # สีพื้นหลังภายในตัวกราฟ
        paper_bgcolor="#111111",  # สีพื้นหลังภายนอกแดชบอร์ด
        hovermode="x unified",  # แสดงค่าทุกเส้นพร้อมกันเมื่อชี้ที่แกน X
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        xaxis=dict(
            title="Absolute Time [Date & Time]",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            linecolor="#888888",
            rangeslider=dict(
                visible=True
            ),  # เพิ่มแถบเลื่อน (Slider) ด้านล่างย่อขยายเวลาได้อิสระ
            type="date",
        ),
        yaxis=y_layout,
        height=620,
        margin=dict(l=60, r=60, t=40, b=60),
    )

    if y_layout_2:
      fig.update_layout(yaxis2=y_layout_2)

    # พล็อตกราฟลงหน้าเว็บบอร์ด
    st.plotly_chart(fig, use_container_width=True)

    # แสดงตารางข้อมูลจัดระเบียบเรียบร้อยแล้วด้านล่าง
    with st.expander("📋 ดูตารางข้อมูลที่ดึงและคำนวณค่า MAX ออกมาแล้ว"):
      st.dataframe(df)

  except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการแปลงโครงสร้างไฟล์: {e}")
    st.info(
        "โปรดตรวจสอบว่าไฟล์ที่คุณอัปโหลดเป็นไฟล์ดิบ (Raw CSV) ที่เซฟมาจากโปรแกรมเครื่อง Yokogawa โดยตรงและไม่มีการแก้ไขโครงสร้าง"
    )
else:
  st.info("💡 โปรดดาวน์โหลดข้อมูลเป็นไฟล์ .CSV แล้วนำมาอัปโหลดเพื่อเปิดกราฟ")

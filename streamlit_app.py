import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(layout="wide")
st.title("📊 Industrial Data Viewer (Excel / CSV Reader)")

# 1. ฟังก์ชันจัดการและแปลงข้อมูลไฟล์อุตสาหกรรม (Yokogawa DX2000 Structure)
@st.cache_data
def process_industrial_data(uploaded_file):
    # ตรวจสอบประเภทไฟล์และใช้ตัวอ่านข้อมูลให้ถูกต้อง
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file, skiprows=27, header=None)
    elif file_name.endswith('.xls'):
        raw_df = pd.read_excel(uploaded_file, skiprows=27, header=None, engine='xlrd')
    else:  # .xlsx
        raw_df = pd.read_excel(uploaded_file, skiprows=27, header=None, engine='openpyxl')

    # สร้าง DataFrame ใหม่สำหรับพล็อตกราฟ
    df = pd.DataFrame()
    
    # รวมคอลลัมน์ Date (0) และ Time (1) เข้าด้วยกันเพื่อสร้างแกน X
    df["DateTime"] = pd.to_datetime(raw_df[0].astype(str) + " " + raw_df[1].astype(str), errors="coerce")

    # สูตรสเกลข้อมูลอิงค่า MAX จากโครงสร้าง Yokogawa: คอลัมน์ลำดับที่ = 3 + (Ch_Index * 2) + 1
    # ----------------------------------------------------
    # กลุ่มที่ 1: Brazing Zone Top #1 - #7
    for i in range(1, 8):
        df[f"Top Zone #{i}"] = pd.to_numeric(raw_df[3 + ((i - 1) * 2) + 1], errors="coerce")

    # กลุ่มที่ 2: Brazing Zone Bottom #1 - #7 (เริ่มที่ Ch Index 19)
    bottom_start_ch = 19
    for i in range(1, 8):
        ch_idx = bottom_start_ch + (i - 1)
        df[f"Bottom Zone #{i}"] = pd.to_numeric(raw_df[3 + (ch_idx * 2) + 1], errors="coerce")

    # กลุ่มที่ 3: Dryer #1 & Dryer #2
    df["Dryer #1"] = pd.to_numeric(raw_df[3 + (15 * 2) + 1], errors="coerce")
    df["Dryer #2"] = pd.to_numeric(raw_df[3 + (16 * 2) + 1], errors="coerce")

    # กลุ่มที่ 4: ppmO2 & N2 Flow
    df["ENTRANCE O2"] = pd.to_numeric(raw_df[3 + (14 * 2) + 1], errors="coerce")
    df["EXIT O2"] = pd.to_numeric(raw_df[3 + (13 * 2) + 1], errors="coerce")
    df["N2 Flow"] = pd.to_numeric(raw_df[3 + (17 * 2) + 1], errors="coerce")

    # กลุ่มที่ 5: Dew point
    df["DEW POINT"] = pd.to_numeric(raw_df[3 + (18 * 2) + 1], errors="coerce")

    # ล้างแถวข้อมูลที่เวลาไม่สมบูรณ์และเรียงลำดับเวลา
    df = df.dropna(subset=["DateTime"]).sort_values("DateTime")
    return df

# ส่วนรับไฟล์จากผู้ใช้งาน (รองรับทั้ง CSV และ Excel)
uploaded_file = st.file_uploader(
    "อัปโหลดไฟล์ข้อมูล (CSV, XLSX, XLS)", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        df = process_industrial_data(uploaded_file)
        st.success(f"🤖 ประมวลผลไฟล์ '{uploaded_file.name}' สำเร็จ!")

        # แถบวิทยุสำหรับเลือกกลุ่มกราฟในการตรวจงาน
        st.subheader("📈 เลือกกลุ่มข้อมูลที่ต้องการแสดงผล")
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
        y_layout = dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False, linecolor="#888888")
        y_layout_2 = None

        # ------------------ ตั้งค่าเงื่อนไขการวาดกราฟแต่ละกลุ่ม ------------------
        if "1. Brazing zone Top" in group_option:
            for i in range(1, 8):
                name = f"Top Zone #{i}"
                fig.add_trace(go.Scatter(x=df["DateTime"], y=df[name], name=name, mode="lines"))
            y_layout.update(range=[400, 650], title="Temperature Top (°C)")

        elif "2. Brazing zone Bottom" in group_option:
            for i in range(1, 8):
                name = f"Bottom Zone #{i}"
                fig.add_trace(go.Scatter(x=df["DateTime"], y=df[name], name=name, mode="lines"))
            y_layout.update(range=[400, 650], title="Temperature Bottom (°C)")

        elif "3. Dryer" in group_option:
            fig.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #1"], name="Dryer #1", mode="lines"))
            fig.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #2"], name="Dryer #2", mode="lines"))
            y_layout.update(range=[0, 400], title="Dryer Temperature (°C)")

        elif "4. ppmO2 & N2 Flow" in group_option:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=df["DateTime"], y=df["ENTRANCE O2"], name="ENTRANCE O2 (Y-Left)", mode="lines"), secondary_y=False)
            fig.add_trace(go.Scatter(x=df["DateTime"], y=df["EXIT O2"], name="EXIT O2 (Y-Left)", mode="lines"), secondary_y=False)
            fig.add_trace(go.Scatter(x=df["DateTime"], y=df["N2 Flow"], name="N2 Flow Rate (Y-Right)", mode="lines"), secondary_y=True)
            
            y_layout.update(range=[0, 200], title="Oxygen Level (ppm)")
            y_layout_2 = dict(title="N2 Flow Rate (Free Scale)", showgrid=False, overlaying="y", side="right", linecolor="#ff7f0e")

        elif "5. Dew point" in group_option:
            fig.add_trace(go.Scatter(x=df["DateTime"], y=df["DEW POINT"], name="Dew Point", mode="lines", line=dict(color="#00ecff")))
            y_layout.update(range=[10, -100], title="Dew Point (°Cdp)")

        # ------------------ ตกแต่งหน้าตากราฟให้เหมือนเครื่องจักรโรงงาน ------------------
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="#1f1f1f",
            paper_bgcolor="#111111",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(
                title="Absolute Time [Date & Time]",
                showgrid=True,
                gridcolor="rgba(128,128,128,0.15)",
                linecolor="#888888",
                rangeslider=dict(visible=True),  # แถบสไลเดอร์ย่อขยายด้านล่างกราฟ
                type="date",
            ),
            yaxis=y_layout,
            height=620,
            margin=dict(l=60, r=60, t=40, b=60),
        )

        if y_layout_2:
            fig.update_layout(yaxis2=y_layout_2)

        # พล็อตกราฟเชิงโต้ตอบลงหน้าเว็บ
        st.plotly_chart(fig, use_container_width=True)

        # เมนูซ่อน/แสดงตารางข้อมูลเพื่อตรวจสอบค่า
        with st.expander("📋 ตรวจสอบตารางข้อมูลดิบ (Cleaned Dataframe)"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์ Excel/CSV: {e}")
        st.info("คำแนะนำ: ตรวจสอบให้แน่ใจว่าไฟล์ที่นำมาอัปโหลดเป็นไฟล์ที่เซฟออกมาจากระบบ Yokogawa โดยไม่ได้ปรับแต่งแถวใดๆ")
else:
    st.info("💡 โปรดนำไฟล์ Excel (.xlsx, .xls) หรือ CSV จากตู้บันทึกข้อมูลมาอัปโหลดเพื่อเปิดแดชบอร์ด")

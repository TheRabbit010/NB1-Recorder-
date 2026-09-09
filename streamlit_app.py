import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(layout="wide", page_title="Industrial Furnace Monitor")
st.title("🏭 Real-Time Industrial Furnace Monitor (Interactive 5 Groups)")

# 1. ฟังก์ชันจัดการและแปลงข้อมูลไฟล์อุตสาหกรรม (Yokogawa DX2000 Structure)
@st.cache_data
def process_industrial_data(uploaded_file):
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file, skiprows=27, header=None)
    elif file_name.endswith('.xls'):
        raw_df = pd.read_excel(uploaded_file, skiprows=27, header=None, engine='xlrd')
    else:  # .xlsx
        raw_df = pd.read_excel(uploaded_file, skiprows=27, header=None, engine='openpyxl')

    df = pd.DataFrame()
    
    # รวมคอลลัมน์ Date (0) และ Time (1) เข้าด้วยกันเพื่อสร้างแกน X
    df["DateTime"] = pd.to_datetime(raw_df[0].astype(str) + " " + raw_df[1].astype(str), errors="coerce")

    # ดึงค่า MAX จากโครงสร้าง Yokogawa: คอลัมน์ลำดับที่ = 3 + (Ch_Index * 2) + 1
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

    df = df.dropna(subset=["DateTime"]).sort_values("DateTime")
    return df

# ฟังก์ชันตกแต่งสไตล์กราฟ
def apply_industrial_style(fig, y_title, y_range=None, is_dual_axis=False):
    layout_args = dict(
        template="plotly_dark",
        plot_bgcolor="#1f1f1f",
        paper_bgcolor="#111111",
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="#444444",
            borderwidth=1
        ),
        xaxis=dict(
            title="Absolute Time [Date & Time]",
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            linecolor="#888888",
            type="date",
        ),
        yaxis=dict(
            title=y_title,
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
            linecolor="#888888",
        ),
        height=400,
        margin=dict(l=60, r=160, t=30, b=40),
    )
    if y_range and not is_dual_axis:
        layout_args["yaxis"]["range"] = y_range
        
    fig.update_layout(**layout_args)

# ส่วนอัปโหลดไฟล์
uploaded_file = st.file_uploader(
    "อัปโหลดไฟล์ข้อมูล Excel หรือ CSV", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        raw_df = process_industrial_data(uploaded_file)
        
        # --- Sidebar Interactive Controls ---
        st.sidebar.header("🎛️ Dynamic Controls")
        
        # 1. Filter ช่วงเวลา (Time Range Slider)
        min_time = raw_df["DateTime"].min().to_pydatetime()
        max_time = raw_df["DateTime"].max().to_pydatetime()
        
        selected_time = st.sidebar.slider(
            "⏱️ เลือกช่วงเวลา (Time Filter):",
            min_value=min_time,
            max_value=max_time,
            value=(min_time, max_time),
            format="MM-DD HH:mm"
        )
        
        # กรองข้อมูลตามเวลา
        df = raw_df[(raw_df["DateTime"] >= selected_time[0]) & (raw_df["DateTime"] <= selected_time[1])].copy()

        # 2. Filter เลือกแสดง/ซ่อน กราฟแต่ละกลุ่ม
        st.sidebar.subheader("📊 เลือกกลุ่มกราฟที่ต้องการแสดง")
        show_g1 = st.sidebar.checkbox("1. Brazing Top Zone", value=True)
        show_g2 = st.sidebar.checkbox("2. Brazing Bottom Zone", value=True)
        show_g3 = st.sidebar.checkbox("3. Dryer #1 & #2", value=True)
        show_g4 = st.sidebar.checkbox("4. O2 & N2 Flow Rate", value=True)
        show_g5 = st.sidebar.checkbox("5. Dew Point", value=True)

        # 3. Interactive Y-Axis Range Overrides
        st.sidebar.subheader("📐 ปรับสเกลแกน Y")
        top_y_max = st.sidebar.number_input("Top/Bottom Temp Max (°C)", value=650)
        o2_y_max = st.sidebar.number_input("O2 Max Level (ppm)", value=200)

        # --- KPI Display Section ---
        if not df.empty:
            latest_row = df.iloc[-1]
            st.markdown("### 📌 ค่าล่าสุดในระบบ (Latest Real-Time Readings)")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Top Zone #1", f"{latest_row['Top Zone #1']:.1f} °C")
            col2.metric("Bottom Zone #1", f"{latest_row['Bottom Zone #1']:.1f} °C")
            col3.metric("Dryer #1", f"{latest_row['Dryer #1']:.1f} °C")
            col4.metric("Exit O2", f"{latest_row['EXIT O2']:.1f} ppm")
            col5.metric("Dew Point", f"{latest_row['DEW POINT']:.1f} °Cdp")
            st.divider()

        # --- กราฟที่ 1: Brazing zone Top #1-#7 ---
        if show_g1:
            st.subheader("1. Brazing zone Top #1-#7")
            fig1 = go.Figure()
            for i in range(1, 8):
                fig1.add_trace(go.Scatter(x=df["DateTime"], y=df[f"Top Zone #{i}"], name=f"Top Z#{i}", mode="lines"))
            apply_industrial_style(fig1, "Temperature (°C)", y_range=[300, top_y_max])
            st.plotly_chart(fig1, use_container_width=True)

        # --- กราฟที่ 2: Brazing zone Bottom #1-#7 ---
        if show_g2:
            st.subheader("2. Brazing zone Bottom #1-#7")
            fig2 = go.Figure()
            for i in range(1, 8):
                fig2.add_trace(go.Scatter(x=df["DateTime"], y=df[f"Bottom Zone #{i}"], name=f"Bottom Z#{i}", mode="lines"))
            apply_industrial_style(fig2, "Temperature (°C)", y_range=[300, top_y_max])
            st.plotly_chart(fig2, use_container_width=True)

        # --- กราฟที่ 3: Dryer #1 & #2 ---
        if show_g3:
            st.subheader("3. Dryer #1 & #2")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #1"], name="Dryer #1", mode="lines"))
            fig3.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #2"], name="Dryer #2", mode="lines"))
            apply_industrial_style(fig3, "Temperature (°C)", y_range=[0, 400])
            st.plotly_chart(fig3, use_container_width=True)

        # --- กราฟที่ 4: ppmO2 Entry&Exit + N2 Flow (Dual Y-Axes) ---
        if show_g4:
            st.subheader("4. ppmO2 Entry/Exit & N2 Flow")
            fig4 = make_subplots(specs=[[{"secondary_y": True}]])
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["ENTRANCE O2"], name="ENTRANCE O2", mode="lines"), secondary_y=False)
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["EXIT O2"], name="EXIT O2", mode="lines"), secondary_y=False)
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["N2 Flow"], name="N2 Flow Rate", mode="lines", line=dict(color="#ff7f0e")), secondary_y=True)
            
            apply_industrial_style(fig4, "Oxygen Level (ppm)", is_dual_axis=True)
            fig4.update_layout(
                yaxis=dict(range=[0, o2_y_max], title="Oxygen Level (ppm)", showgrid=True, gridcolor="rgba(128,128,128,0.15)"),
                yaxis2=dict(title="N2 Flow Rate (Free Scale)", showgrid=False, overlaying="y", side="right", linecolor="#ff7f0e")
            )
            st.plotly_chart(fig4, use_container_width=True)

        # --- กราฟที่ 5: Dew point ---
        if show_g5:
            st.subheader("5. Dew point 'Cdp")
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(x=df["DateTime"], y=df["DEW POINT"], name="Dew Point", mode="lines", line=dict(color="#00ecff")))
            apply_industrial_style(fig5, "Dew Point (°Cdp)", y_range=[10, -100])
            st.plotly_chart(fig5, use_container_width=True)

        # ตารางข้อมูล และ ปุ่มดาวน์โหลด
        with st.expander("📋 ตรวจสอบและดาวน์โหลดตารางข้อมูลดิบ"):
            st.dataframe(df)
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 ดาวน์โหลดข้อมูลเป็น CSV",
                data=csv_data,
                file_name="processed_furnace_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการแสดงผล: {e}")
else:
    st.info("💡 โปรดอัปโหลดไฟล์ Excel (.xlsx, .xls) หรือ CSV เพื่อแสดงกราฟทั้ง 5 กลุ่มพร้อมกัน")

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 1. ตั้งค่า Page Config และฉีด CSS บังคับ Dark Mode + ตกแต่ง UI
st.set_page_config(
    page_title="Industrial Furnace Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# บังคับพื้นหลังแอปทั้งหมดเป็น Dark Theme ถาวร
st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22;
        }
        .uploadedFile {
            background-color: #21262d;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 Real-Time Industrial Furnace Monitor")

# 2. ฟังก์ชันจัดการข้อมูล (Yokogawa DX2000)
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
    df["DateTime"] = pd.to_datetime(raw_df[0].astype(str) + " " + raw_df[1].astype(str), errors="coerce")

    # Top Zone #1 - #7
    for i in range(1, 8):
        df[f"Top Zone #{i}"] = pd.to_numeric(raw_df[3 + ((i - 1) * 2) + 1], errors="coerce")

    # Bottom Zone #1 - #7 (Ch Index 19)
    bottom_start_ch = 19
    for i in range(1, 8):
        ch_idx = bottom_start_ch + (i - 1)
        df[f"Bottom Zone #{i}"] = pd.to_numeric(raw_df[3 + (ch_idx * 2) + 1], errors="coerce")

    # Dryer #1 & Dryer #2
    df["Dryer #1"] = pd.to_numeric(raw_df[3 + (15 * 2) + 1], errors="coerce")
    df["Dryer #2"] = pd.to_numeric(raw_df[3 + (16 * 2) + 1], errors="coerce")

    # ppmO2 & N2 Flow
    df["ENTRANCE O2"] = pd.to_numeric(raw_df[3 + (14 * 2) + 1], errors="coerce")
    df["EXIT O2"] = pd.to_numeric(raw_df[3 + (13 * 2) + 1], errors="coerce")
    df["N2 Flow"] = pd.to_numeric(raw_df[3 + (17 * 2) + 1], errors="coerce")

    # Dew point
    df["DEW POINT"] = pd.to_numeric(raw_df[3 + (18 * 2) + 1], errors="coerce")

    df = df.dropna(subset=["DateTime"]).sort_values("DateTime")
    return df

# 3. ฟังก์ชันตกแต่งสไตล์กราฟ (Legend สว่าง ชัดเจน)
def apply_industrial_style(fig, y_title, y_range=None, is_dual_axis=False):
    layout_args = dict(
        template="plotly_dark",
        plot_bgcolor="#161b22",
        paper_bgcolor="#0e1117",
        hovermode="x unified",
        showlegend=True,
        # Legend ชัดเจน สีตัวอักษรขาว กรอบสว่าง
        legend=dict(
            font=dict(color="#FFFFFF", size=12, family="Arial Bold"),
            bgcolor="rgba(27, 31, 36, 0.95)",
            bordercolor="#F0B90B",
            borderwidth=1.5,
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        xaxis=dict(
            title=dict(text="Absolute Time [Date & Time]", font=dict(color="#FFFFFF", size=12)),
            tickfont=dict(color="#CCCCCC", size=10),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            linecolor="#555555",
            type="date",
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color="#FFFFFF", size=12)),
            tickfont=dict(color="#CCCCCC", size=10),
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
            linecolor="#555555",
        ),
        height=420,
        margin=dict(l=60, r=180, t=30, b=40),
    )
    if y_range and not is_dual_axis:
        layout_args["yaxis"]["range"] = y_range
        
    fig.update_layout(**layout_args)

# ส่วน Sidebar สำหรับอัปโหลดไฟล์
st.sidebar.header("📁 เมนูอัปโหลดข้อมูล")
uploaded_file = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ Yokogawa (.csv, .xlsx, .xls)", type=["csv", "xlsx", "xls"]
)

# 4. ส่วนแสดงผลหลัก
if uploaded_file is not None:
    try:
        raw_df = process_industrial_data(uploaded_file)
        
        st.sidebar.markdown("---")
        st.sidebar.header("🎛️ Dynamic Controls")
        
        # Filter ช่วงเวลา
        min_time = raw_df["DateTime"].min().to_pydatetime()
        max_time = raw_df["DateTime"].max().to_pydatetime()
        
        selected_time = st.sidebar.slider(
            "⏱️ ช่วงเวลา:",
            min_value=min_time,
            max_value=max_time,
            value=(min_time, max_time),
            format="MM-DD HH:mm"
        )
        
        df = raw_df[(raw_df["DateTime"] >= selected_time[0]) & (raw_df["DateTime"] <= selected_time[1])].copy()

        # Checkboxes เลือกแสดงกราฟ
        st.sidebar.subheader("📊 เลือกกลุ่มกราฟ")
        show_g1 = st.sidebar.checkbox("1. Top Zone Temp", value=True)
        show_g2 = st.sidebar.checkbox("2. Bottom Zone Temp", value=True)
        show_g3 = st.sidebar.checkbox("3. Dryer Temp", value=True)
        show_g4 = st.sidebar.checkbox("4. O2 & N2 Flow Rate", value=True)
        show_g5 = st.sidebar.checkbox("5. Dew Point", value=True)

        # KPI Summary Cards
        if not df.empty:
            latest = df.iloc[-1]
            st.markdown("### 📌 ค่าล่าสุดในระบบ (Latest Readings)")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Top Zone #1", f"{latest['Top Zone #1']:.1f} °C")
            col2.metric("Bottom Zone #1", f"{latest['Bottom Zone #1']:.1f} °C")
            col3.metric("Dryer #1", f"{latest['Dryer #1']:.1f} °C")
            col4.metric("Exit O2", f"{latest['EXIT O2']:.1f} ppm")
            col5.metric("Dew Point", f"{latest['DEW POINT']:.1f} °Cdp")
            st.markdown("---")

        # 1. Top Zone
        if show_g1:
            st.subheader("1. Brazing zone Top #1-#7")
            fig1 = go.Figure()
            for i in range(1, 8):
                fig1.add_trace(go.Scatter(x=df["DateTime"], y=df[f"Top Zone #{i}"], name=f"Top Z#{i}", mode="lines", line=dict(width=2)))
            apply_industrial_style(fig1, "Temperature (°C)", y_range=[300, 650])
            st.plotly_chart(fig1, use_container_width=True)

        # 2. Bottom Zone
        if show_g2:
            st.subheader("2. Brazing zone Bottom #1-#7")
            fig2 = go.Figure()
            for i in range(1, 8):
                fig2.add_trace(go.Scatter(x=df["DateTime"], y=df[f"Bottom Zone #{i}"], name=f"Bottom Z#{i}", mode="lines", line=dict(width=2)))
            apply_industrial_style(fig2, "Temperature (°C)", y_range=[300, 650])
            st.plotly_chart(fig2, use_container_width=True)

        # 3. Dryer
        if show_g3:
            st.subheader("3. Dryer #1 & #2")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #1"], name="Dryer #1", mode="lines", line=dict(width=2)))
            fig3.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #2"], name="Dryer #2", mode="lines", line=dict(width=2)))
            apply_industrial_style(fig3, "Temperature (°C)", y_range=[0, 400])
            st.plotly_chart(fig3, use_container_width=True)

        # 4. O2 & N2
        if show_g4:
            st.subheader("4. ppmO2 Entry/Exit & N2 Flow")
            fig4 = make_subplots(specs=[[{"secondary_y": True}]])
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["ENTRANCE O2"], name="ENTRANCE O2", mode="lines", line=dict(width=2)), secondary_y=False)
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["EXIT O2"], name="EXIT O2", mode="lines", line=dict(width=2)), secondary_y=False)
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["N2 Flow"], name="N2 Flow Rate", mode="lines", line=dict(color="#ff7f0e", width=2)), secondary_y=True)
            
            apply_industrial_style(fig4, "Oxygen Level (ppm)", is_dual_axis=True)
            fig4.update_layout(
                yaxis=dict(range=[0, 200], title="Oxygen Level (ppm)", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
                yaxis2=dict(title="N2 Flow Rate (Free Scale)", showgrid=False, overlaying="y", side="right", linecolor="#ff7f0e")
            )
            st.plotly_chart(fig4, use_container_width=True)

        # 5. Dew Point
        if show_g5:
            st.subheader("5. Dew point 'Cdp")
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(x=df["DateTime"], y=df["DEW POINT"], name="Dew Point", mode="lines", line=dict(color="#00ecff", width=2)))
            apply_industrial_style(fig5, "Dew Point (°Cdp)", y_range=[10, -100])
            st.plotly_chart(fig5, use_container_width=True)

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")

else:
    # หน้า Welcome Screen มืดสวยงาม ป้องกันหน้าขาวว่าง
    st.info("👈 กรุณาอัปโหลดไฟล์ข้อมูลอุตสาหกรรม (.csv หรือ .xlsx) ที่เมนูด้านซ้ายเพื่อเริ่มการทำงาน")
    
    st.markdown("""
        <div style="background-color: #161b22; padding: 25px; border-radius: 10px; border: 1px solid #30363d;">
            <h3>📌 คำแนะนำการใช้งาน</h3>
            <ul>
                <li>รองรับไฟล์รายงานข้อมูลเตาอบอุตสาหกรรมประเภท Yokogawa DX2000 (.csv, .xlsx, .xls)</li>
                <li>ระบบจะดึงข้อมูลอัตโนมัติออกเป็น <b>5 กลุ่มหลัก</b> (Top/Bottom Temp, Dryer, O2/N2 Flow, Dew Point)</li>
                <li>เมื่ออัปโหลดแล้ว สามารถปรับซูมเวลา หรือเลือกซ่อน/แสดงกลุ่มข้อมูลได้ที่แถบเมนูด้านซ้าย</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

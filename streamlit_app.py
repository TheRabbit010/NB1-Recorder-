import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 1. ตั้งค่า Page Config และบังคับธีม Dark Mode ผ่าน CSS ทันทีที่โหลดสคริปต์
st.set_page_config(
    page_title="Industrial Furnace Monitor",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* บังคับพื้นหลังแอปทั้งหมดเป็น Dark Mode ถาวร */
        .stApp {
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
        }
        .stMarkdown, h1, h2, h3, p, span {
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

# แสดง Header เสมอ เพื่อไม่ให้หน้าจอว่างเปล่า
st.title("🏭 Real-Time Industrial Furnace Monitor")

# ฟังก์ชันคำนวณตำแหน่งคอลัมน์ค่า MAX ของแต่ละ Channel จากไฟล์ Excel Yokogawa DX2000
def get_ch_max_col_idx(ch_number):
    return 3 + (ch_number * 2) - 1

# 2. ฟังก์ชันประมวลผลไฟล์เดี่ยว
def parse_single_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file, skiprows=27, header=None)
    elif file_name.endswith('.xls'):
        raw_df = pd.read_excel(uploaded_file, skiprows=27, header=None, engine='xlrd')
    else:  # .xlsx
        raw_df = pd.read_excel(uploaded_file, skiprows=27, header=None, engine='openpyxl')

    df = pd.DataFrame()
    # รวมคอลัมน์ Date (0) และ Time (1)
    df["DateTime"] = pd.to_datetime(raw_df[0].astype(str) + " " + raw_df[1].astype(str), errors="coerce")

    # CH001 - CH007: Top Zone #1 - #7
    for i in range(1, 8):
        df[f"Top Zone #{i}"] = pd.to_numeric(raw_df[get_ch_max_col_idx(i)], errors="coerce")

    # CH008 - CH014: Bottom Zone #1 - #7
    for i in range(1, 8):
        ch_num = 7 + i
        df[f"Bottom Zone #{i}"] = pd.to_numeric(raw_df[get_ch_max_col_idx(ch_num)], errors="coerce")

    # CH015: EXIT O2
    df["EXIT O2"] = pd.to_numeric(raw_df[get_ch_max_col_idx(15)], errors="coerce")

    # CH016: Dryer #1 & CH017: Dryer #2 (อ่านค่าจากคอลัมน์ MAX ตรงตาม Excel)
    df["Dryer #1"] = pd.to_numeric(raw_df[get_ch_max_col_idx(16)], errors="coerce")
    df["Dryer #2"] = pd.to_numeric(raw_df[get_ch_max_col_idx(17)], errors="coerce")

    # CH018: N2 Flow Rate
    df["N2 Flow"] = pd.to_numeric(raw_df[get_ch_max_col_idx(18)], errors="coerce")

    # CH019: ENTRANCE O2
    df["ENTRANCE O2"] = pd.to_numeric(raw_df[get_ch_max_col_idx(19)], errors="coerce")

    # CH020: DEW POINT
    df["DEW POINT"] = pd.to_numeric(raw_df[get_ch_max_col_idx(20)], errors="coerce")

    return df.dropna(subset=["DateTime"])

# ฟังก์ชันประมวลผลหลายไฟล์พร้อมกัน
@st.cache_data
def process_multiple_files(uploaded_files):
    combined_dfs = []
    for file in uploaded_files:
        single_df = parse_single_file(file)
        combined_dfs.append(single_df)
    
    full_df = pd.concat(combined_dfs, ignore_index=True)
    full_df = full_df.drop_duplicates(subset=["DateTime"]).sort_values("DateTime").reset_index(drop=True)
    return full_df

# 3. ฟังก์ชันตกแต่งสไตล์กราฟ
def apply_industrial_style(fig, y_title, y_range=None, is_dual_axis=False):
    layout_args = dict(
        template="plotly_dark",
        plot_bgcolor="#161b22",
        paper_bgcolor="#0e1117",
        hovermode="x unified",
        showlegend=True,
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

# ส่วน Sidebar อัปโหลดไฟล์
st.sidebar.header("📁 เมนูอัปโหลดข้อมูล")
uploaded_files = st.sidebar.file_uploader(
    "อัปโหลดไฟล์ Yokogawa (.csv, .xlsx, .xls) ได้มากกว่า 1 ไฟล์", 
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True
)

# 4. ส่วนแสดงผลหลัก
if uploaded_files:
    try:
        raw_df = process_multiple_files(uploaded_files)
        st.sidebar.success(f"รวมข้อมูลสำเร็จ {len(uploaded_files)} ไฟล์ ({len(raw_df)} แถว)")

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
        show_g1 = st.sidebar.checkbox("1. Top Zone Temp (CH1-7)", value=True)
        show_g2 = st.sidebar.checkbox("2. Bottom Zone Temp (CH8-14)", value=True)
        show_g3 = st.sidebar.checkbox("3. Dryer Temp (CH16-17)", value=True)
        show_g4 = st.sidebar.checkbox("4. O2 & N2 Flow (CH15, CH18, CH19)", value=True)
        show_g5 = st.sidebar.checkbox("5. Dew Point (CH20)", value=True)

        # KPI Summary Cards
        if not df.empty:
            latest = df.iloc[-1]
            st.markdown("### 📌 ค่าล่าสุดในระบบ (Latest Readings)")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Top Zone #1", f"{latest['Top Zone #1']:.1f} °C")
            col2.metric("Bottom Zone #1", f"{latest['Bottom Zone #1']:.1f} °C")
            col3.metric("Dryer #1", f"{latest['Dryer #1']:.1f} °C")
            col4.metric("Exit O2 (CH15)", f"{latest['EXIT O2']:.1f} ppm")
            col5.metric("Dew Point (CH20)", f"{latest['DEW POINT']:.1f} °Cdp")
            st.markdown("---")

        # 1. Top Zone (CH001 - CH007)
        if show_g1:
            st.subheader("1. Brazing zone Top #1-#7 (CH001-CH007)")
            fig1 = go.Figure()
            for i in range(1, 8):
                fig1.add_trace(go.Scatter(x=df["DateTime"], y=df[f"Top Zone #{i}"], name=f"Top Z#{i} (CH{i:03d})", mode="lines", line=dict(width=2)))
            apply_industrial_style(fig1, "Temperature (°C)", y_range=[300, 650])
            st.plotly_chart(fig1, use_container_width=True)

        # 2. Bottom Zone (CH008 - CH014)
        if show_g2:
            st.subheader("2. Brazing zone Bottom #1-#7 (CH008-CH014)")
            fig2 = go.Figure()
            for i in range(1, 8):
                ch_num = 7 + i
                fig2.add_trace(go.Scatter(x=df["DateTime"], y=df[f"Bottom Zone #{i}"], name=f"Bottom Z#{i} (CH{ch_num:03d})", mode="lines", line=dict(width=2)))
            apply_industrial_style(fig2, "Temperature (°C)", y_range=[300, 650])
            st.plotly_chart(fig2, use_container_width=True)

        # 3. Dryer (CH016 & CH017)
        if show_g3:
            st.subheader("3. Dryer #1 & #2 (CH016 & CH017)")
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #1"], name="Dryer #1 (CH016)", mode="lines", line=dict(width=2)))
            fig3.add_trace(go.Scatter(x=df["DateTime"], y=df["Dryer #2"], name="Dryer #2 (CH017)", mode="lines", line=dict(width=2)))
            apply_industrial_style(fig3, "Temperature (°C)", y_range=[0, 400])
            st.plotly_chart(fig3, use_container_width=True)

        # 4. O2 & N2 Flow Rate (CH015, CH018, CH019)
        if show_g4:
            st.subheader("4. ppmO2 Entry/Exit & N2 Flow (CH015, CH018, CH019)")
            fig4 = make_subplots(specs=[[{"secondary_y": True}]])
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["ENTRANCE O2"], name="ENTRANCE O2 (CH019)", mode="lines", line=dict(width=2)), secondary_y=False)
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["EXIT O2"], name="EXIT O2 (CH015)", mode="lines", line=dict(width=2)), secondary_y=False)
            fig4.add_trace(go.Scatter(x=df["DateTime"], y=df["N2 Flow"], name="N2 Flow (CH018)", mode="lines", line=dict(color="#ff7f0e", width=2)), secondary_y=True)
            
            apply_industrial_style(fig4, "Oxygen Level (ppm)", is_dual_axis=True)
            fig4.update_layout(
                yaxis=dict(range=[0, 200], title="Oxygen Level (ppm) [0-200]", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
                yaxis2=dict(title="N2 Flow Rate (Free Scale)", showgrid=False, overlaying="y", side="right", linecolor="#ff7f0e")
            )
            st.plotly_chart(fig4, use_container_width=True)

        # 5. Dew Point (CH020)
        if show_g5:
            st.subheader("5. Dew point 'Cdp (CH020)")
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(x=df["DateTime"], y=df["DEW POINT"], name="Dew Point (CH020)", mode="lines", line=dict(color="#00ecff", width=2)))
            apply_industrial_style(fig5, "Dew Point (°Cdp)", y_range=[10, -100])
            st.plotly_chart(fig5, use_container_width=True)

        # ตารางข้อมูลและปุ่มดาวน์โหลด
        with st.expander("📋 ตรวจสอบและดาวน์โหลดตารางข้อมูลรวมเรียงตามเวลา"):
            st.dataframe(df)
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 ดาวน์โหลดข้อมูลที่รวมกันแล้วเป็น CSV",
                data=csv_data,
                file_name="combined_furnace_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")

else:
    # แสดงการแนะนำการใช้งานในหน้าหลักทันที เพื่อป้องกันหน้าจอขาวว่างเปล่า
    st.info("👈 กรุณาเลือกอัปโหลดไฟล์ (.csv หรือ .xlsx) ที่เมนูด้านซ้าย สามารถเลือกอัปโหลดได้มากกว่า 1 ไฟล์")
    
    st.markdown("""
        <div style="background-color: #161b22; padding: 25px; border-radius: 10px; border: 1px solid #30363d;">
            <h3 style="color: #F0B90B !important;">📌 โครงสร้าง Channel ที่เปิดใช้งาน:</h3>
            <ul>
                <li><b>CH001 - CH007:</b> Top Zone Temp #1 - #7</li>
                <li><b>CH008 - CH014:</b> Bottom Zone Temp #1 - #7</li>
                <li><b>CH015:</b> EXIT O2 (แกนซ้าย Scale 0-200 ppm)</li>
                <li><b>CH016 - CH017:</b> Dryer #1 & Dryer #2</li>
                <li><b>CH018:</b> N2 Flow Rate (แกนขวา Free scale อยู่กราฟเดียวกับ O2)</li>
                <li><b>CH019:</b> ENTRANCE O2 (แกนซ้าย Scale 0-200 ppm)</li>
                <li><b>CH020:</b> DEW POINT (Scale 10 ถึง -100 °Cdp กราฟอิสระ)</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

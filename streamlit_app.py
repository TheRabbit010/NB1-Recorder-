# ฟังก์ชันตกแต่งสไตล์กราฟ (ปรับแก้ Legend ให้เห็นชัดเจนขึ้น)
def apply_industrial_style(fig, y_title, y_range=None, is_dual_axis=False):
    layout_args = dict(
        template="plotly_dark",
        plot_bgcolor="#1f1f1f",
        paper_bgcolor="#111111",
        hovermode="x unified",
        showlegend=True,
        # --- ปรับแต่ง Legend Box ใหม่เพื่อความชัดเจน ---
        legend=dict(
            font=dict(
                color="#FFFFFF",     # สีตัวอักษรขาวสว่าง
                size=13,             # ปรับขนาดตัวอักษรให้ใหญ่ขึ้น
                family="Arial Bold"  # ตัวหนา
            ),
            bgcolor="rgba(30, 30, 30, 0.95)", # พื้นหลังกล่องสว่างขึ้นตัดกับตัวอักษร
            bordercolor="#FFFFFF",             # สีกรอบกล่องสีขาว
            borderwidth=1.5,                   # ความหนากรอบ
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
        ),
        xaxis=dict(
            title=dict(text="Absolute Time [Date & Time]", font=dict(color="#FFFFFF", size=13)),
            tickfont=dict(color="#CCCCCC", size=11),
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="#888888",
            type="date",
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(color="#FFFFFF", size=13)),
            tickfont=dict(color="#CCCCCC", size=11),
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)",
            zeroline=False,
            linecolor="#888888",
        ),
        height=450,
        margin=dict(l=60, r=180, t=40, b=40),
    )
    if y_range and not is_dual_axis:
        layout_args["yaxis"]["range"] = y_range
        
    fig.update_layout(**layout_args)

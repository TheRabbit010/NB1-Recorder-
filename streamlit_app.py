# 4. O2 & N2 Flow Rate (CH015, CH018, CH019)
        if show_g4:
            st.subheader("4. ppmO2 Entry/Exit & N2 Flow (CH015, CH018, CH019)")
            fig4 = make_subplots(specs=[[{"secondary_y": True}]])
            
            # CH019 (ENTRANCE O2) - แกนซ้าย
            fig4.add_trace(
                go.Scatter(x=df["DateTime"], y=df["ENTRANCE O2"], name="ENTRANCE O2 (CH019)", mode="lines", line=dict(color="#FF80FF", width=2)), 
                secondary_y=False
            )
            
            # CH015 (EXIT O2) - แกนซ้าย
            fig4.add_trace(
                go.Scatter(x=df["DateTime"], y=df["EXIT O2"], name="EXIT O2 (CH015)", mode="lines", line=dict(color="#A52A2A", width=2)), 
                secondary_y=False
            )
            
            # CH018 (N2 Flow) - แกนขวา
            fig4.add_trace(
                go.Scatter(x=df["DateTime"], y=df["N2 Flow"], name="N2 Flow (CH018)", mode="lines", line=dict(color="#ADD8E6", width=2)), 
                secondary_y=True
            )
            
            # ตกแต่งสไตล์พื้นฐาน
            apply_industrial_style(fig4, "Oxygen Level (ppm)", is_dual_axis=True)
            
            # บังคับการตั้งค่าแกน Y1 (ซ้าย) และ Y2 (ขวา) ให้อ่านค่า Auto Range ของ N2 Flow
            fig4.update_layout(
                yaxis=dict(
                    title=dict(text="Oxygen Level (ppm) [0-200]", font=dict(color="#FFFFFF", size=12)),
                    range=[0, 200],
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.08)"
                ),
                yaxis2=dict(
                    title=dict(text="N2 Flow Rate (Free Scale)", font=dict(color="#ADD8E6", size=12)),
                    tickfont=dict(color="#ADD8E6", size=10),
                    showgrid=False,
                    overlaying="y",
                    side="right",
                    linecolor="#ADD8E6",
                    autorange=True  # บังคับขยายสเกลตามค่าจริงของ N2 Flow
                )
            )
            st.plotly_chart(fig4, use_container_width=True)

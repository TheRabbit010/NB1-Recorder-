st.markdown("""
    <style>
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background-color: #0e1117 !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
        }
        .stMarkdown, h1, h2, h3, p, span, label {
            color: #ffffff !important;
        }

        /* --- 1. ปรับสไตล์ปุ่มเคลียร์ข้อมูล --- */
        [data-testid="stSidebar"] div.stButton > button {
            background-color: #21262d !important;
            color: #ffffff !important;
            border: 1px solid #F0B90B !important;
            font-weight: bold !important;
            width: 100% !important;
            padding: 8px 16px !important;
        }
        [data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #F0B90B !important;
            color: #000000 !important;
        }

        /* --- 2. ตกแต่งกล่อง File Uploader --- */
        [data-testid="stFileUploader"] {
            background-color: #161b22 !important;
            border: 1.5px solid #F0B90B !important;
            border-radius: 8px !important;
            padding: 10px !important;
        }
        [data-testid="stFileUploader"] section {
            background-color: #1c2128 !important;
            border: 1px dashed #F0B90B !important;
            border-radius: 6px !important;
        }
        [data-testid="stFileUploader"] section div, 
        [data-testid="stFileUploader"] section span,
        [data-testid="stFileUploader"] section small {
            color: #e6edf3 !important;
        }

        /* --- 3. แก้ไขการ์ดไฟล์ที่อัปโหลดแล้ว (แก้ปัญหาการ์ดขาวตัวหนังสือกลืน) --- */
        [data-testid="stFileUploaderFileData"],
        [data-testid="stFileUploaderFileData"] > div,
        [data-testid="stFileUploaderFile"] {
            background-color: #21262d !important;
            border: 1px solid #F0B90B !important;
            border-radius: 6px !important;
        }
        /* บังคับสีตัวอักษรชื่อไฟล์และขนาดไฟล์ให้อ่านง่าย */
        [data-testid="stFileUploaderFileData"] *,
        [data-testid="stFileUploaderFile"] * {
            color: #ffffff !important;
            font-weight: bold !important;
        }
        /* ปุ่มลบไฟล์ (X) */
        [data-testid="stFileUploaderFile"] button,
        [data-testid="stFileUploaderFileData"] button {
            background-color: transparent !important;
            color: #F0B90B !important;
        }
        [data-testid="stFileUploaderFile"] button:hover {
            color: #ff4b4b !important;
        }
    </style>
""", unsafe_allow_html=True)

def parse_single_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    
    # อ่านไฟล์ดิบ
    if file_name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file, header=None)
    elif file_name.endswith('.xls'):
        raw_df = pd.read_excel(uploaded_file, header=None, engine='xlrd')
    else:
        raw_df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')

    # แถวที่ 27 (Index 26) คือแถวที่มีคำว่า CH001, CH002, ..., CH016, CH017
    # แถวที่ 28 (Index 27) คือแถวบอก MIN/MAX
    header_ch_row = raw_df.iloc[26].astype(str).tolist()
    header_mm_row = raw_df.iloc[27].astype(str).tolist()

    # ฟังก์ชันค้นหา Column Index ของ Channel นั้นๆ ที่เป็นค่า 'MAX'
    def find_ch_max_col(ch_name):
        for idx, ch in enumerate(header_ch_row):
            if ch_name in ch:
                # ตรวจสอบคอลัมน์นั้น หรือคอลัมน์ถัดไป หาแถวที่มีคำว่า MAX
                if "MAX" in str(header_mm_row[idx]).upper():
                    return idx
                elif idx + 1 < len(header_mm_row) and "MAX" in str(header_mm_row[idx + 1]).upper():
                    return idx + 1
        return None

    # ดึงเฉพาะข้อมูลตั้งแต่แถวที่ 29 เป็นต้นไป
    data_df = raw_df.iloc[28:].copy().reset_index(drop=True)
    df = pd.DataFrame()
    
    # แกน X (DateTime)
    df["DateTime"] = pd.to_datetime(data_df[0].astype(str) + " " + data_df[1].astype(str), errors="coerce")

    # ฟังก์ชันดึงค่าจากชื่อ Channel แบบไดนามิก
    def get_ch_data(ch_str):
        col_idx = find_ch_max_col(ch_str)
        if col_idx is not None:
            return pd.to_numeric(data_df[col_idx], errors="coerce")
        return None

    # 1. Top Zone CH001 - CH007
    for i in range(1, 8):
        df[f"Top Zone #{i}"] = get_ch_data(f"CH{i:03d}") or get_ch_data(f"CH{i}")

    # 2. Bottom Zone CH008 - CH014
    for i in range(1, 8):
        ch_num = 7 + i
        df[f"Bottom Zone #{i}"] = get_ch_data(f"CH{ch_num:03d}") or get_ch_data(f"CH{ch_num}")

    # 3. EXIT O2 (CH015)
    df["EXIT O2"] = get_ch_data("CH015") or get_ch_data("CH15")

    # 4. Dryer #1 (CH016) & Dryer #2 (CH017) -> ค้นหาจากชื่อ CH016/CH017 โดยตรง
    df["Dryer #1"] = get_ch_data("CH016") or get_ch_data("CH16")
    df["Dryer #2"] = get_ch_data("CH017") or get_ch_data("CH17")

    # 5. N2 Flow (CH018)
    df["N2 Flow"] = get_ch_data("CH018") or get_ch_data("CH18")

    # 6. ENTRANCE O2 (CH019)
    df["ENTRANCE O2"] = get_ch_data("CH019") or get_ch_data("CH19")

    # 7. DEW POINT (CH020)
    df["DEW POINT"] = get_ch_data("CH020") or get_ch_data("CH20")

    return df.dropna(subset=["DateTime"])

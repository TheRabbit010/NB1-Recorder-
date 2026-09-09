def parse_single_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    
    # อ่านไฟล์ดิบ
    if file_name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file, header=None, low_memory=False)
    elif file_name.endswith('.xls'):
        raw_df = pd.read_excel(uploaded_file, header=None, engine='xlrd')
    else:
        raw_df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')

    # ค้นหาแถวเริ่มต้นของข้อมูลตัวเลข (หาแถวที่เริ่มมี Date/Time)
    data_start_row = 28
    for r in range(min(50, len(raw_df))):
        val_str = str(raw_df.iloc[r, 0])
        if re.search(r'\d{2,4}[-/]\d{1,2}[-/]\d{1,2}', val_str):
            data_start_row = r
            break

    header_df = raw_df.iloc[:data_start_row].copy()
    data_df = raw_df.iloc[data_start_row:].copy().reset_index(drop=True)

    # ฟังก์ชันสแกนหา Index คอลัมน์ (แก้ไขจุดที่เกิด Error โดยเติม .fillna('') และ str())
    def scan_channel_col(ch_num):
        target_patterns = [f"CH{ch_num:03d}", f"CH{ch_num:02d}", f"CH{ch_num}"]
        matched_cols = []
        
        for col in range(header_df.shape[1]):
            # แปลงค่าทุกช่องในคอลัมน์เป็น String และแทนที่ NaN ด้วยข้อความว่าง
            col_cells = header_df[col].fillna('').astype(str).tolist()
            col_text = " ".join([str(cell) for cell in col_cells]).upper()
            
            if any(p in col_text for p in target_patterns):
                matched_cols.append(col)
        
        if not matched_cols:
            return None
        
        if len(matched_cols) == 1:
            return matched_cols[0]
            
        # ถ้ามีหลายคอลัมน์ (MIN/MAX) ให้เลือกคอลัมน์ที่มีคำว่า MAX
        for col in matched_cols:
            col_cells = header_df[col].fillna('').astype(str).tolist()
            col_text = " ".join([str(cell) for cell in col_cells]).upper()
            if "MAX" in col_text:
                return col
                
        return matched_cols[-1]

    df = pd.DataFrame()
    df["DateTime"] = pd.to_datetime(data_df[0].astype(str) + " " + data_df[1].astype(str), errors="coerce")

    def extract_series(col_idx):
        if col_idx is not None and col_idx < data_df.shape[1]:
            return pd.to_numeric(data_df[col_idx], errors="coerce")
        return pd.Series([None] * len(data_df))

    mapping_info = {}

    # CH001 - CH007: Top Zone #1 - #7
    for i in range(1, 8):
        c = scan_channel_col(i)
        df[f"Top Zone #{i}"] = extract_series(c)
        mapping_info[f"Top Zone #{i}"] = f"Col {c}" if c is not None else "Not Found"

    # CH008 - CH014: Bottom Zone #1 - #7
    for i in range(1, 8):
        ch_num = 7 + i
        c = scan_channel_col(ch_num)
        df[f"Bottom Zone #{i}"] = extract_series(c)
        mapping_info[f"Bottom Zone #{i}"] = f"Col {c}" if c is not None else "Not Found"

    # CH015: EXIT O2
    c15 = scan_channel_col(15)
    df["EXIT O2"] = extract_series(c15)
    mapping_info["EXIT O2 (CH15)"] = f"Col {c15}" if c15 is not None else "Not Found"

    # CH016 & CH017: Dryer #1 & Dryer #2
    c16 = scan_channel_col(16)
    c17 = scan_channel_col(17)
    df["Dryer #1"] = extract_series(c16)
    df["Dryer #2"] = extract_series(c17)
    mapping_info["Dryer #1 (CH16)"] = f"Col {c16}" if c16 is not None else "Not Found"
    mapping_info["Dryer #2 (CH17)"] = f"Col {c17}" if c17 is not None else "Not Found"

    # CH018: N2 Flow
    c18 = scan_channel_col(18)
    df["N2 Flow"] = extract_series(c18)
    mapping_info["N2 Flow (CH18)"] = f"Col {c18}" if c18 is not None else "Not Found"

    # CH019: ENTRANCE O2
    c19 = scan_channel_col(19)
    df["ENTRANCE O2"] = extract_series(c19)
    mapping_info["ENTRANCE O2 (CH19)"] = f"Col {c19}" if c19 is not None else "Not Found"

    # CH020: DEW POINT
    c20 = scan_channel_col(20)
    df["DEW POINT"] = extract_series(c20)
    mapping_info["DEW POINT (CH20)"] = f"Col {c20}" if c20 is not None else "Not Found"

    return df.dropna(subset=["DateTime"]), mapping_info

# ฟังก์ชันคำนวณตำแหน่งคอลัมน์ค่า MAX ของแต่ละ Channel จากไฟล์ Excel Yokogawa DX2000
# คอลัมน์ 0=Date, 1=Time, 2=Alarm State, 3/4=CH1 MIN/MAX, 5/6=CH2 MIN/MAX ...
def get_ch_max_col_idx(ch_number):
    return 3 + (ch_number * 2) - 1  # ดึงค่าคอลัมน์ MAX (เช่น CH16 = Index 34, Excel Column AK)

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
        ch_num = 7 + i  # CH008 ถึง CH014
        df[f"Bottom Zone #{i}"] = pd.to_numeric(raw_df[get_ch_max_col_idx(ch_num)], errors="coerce")

    # CH015: EXIT O2
    df["EXIT O2"] = pd.to_numeric(raw_df[get_ch_max_col_idx(15)], errors="coerce")

    # CH016: Dryer #1 (ตรงกับคอลัมน์ AK = ค่า MAX ~242-243 °C)
    df["Dryer #1"] = pd.to_numeric(raw_df[get_ch_max_col_idx(16)], errors="coerce")

    # CH017: Dryer #2 (ตรงกับคอลัมน์ AM = ค่า MAX ~260-261 °C)
    df["Dryer #2"] = pd.to_numeric(raw_df[get_ch_max_col_idx(17)], errors="coerce")

    # CH018: N2 Flow Rate
    df["N2 Flow"] = pd.to_numeric(raw_df[get_ch_max_col_idx(18)], errors="coerce")

    # CH019: ENTRANCE O2
    df["ENTRANCE O2"] = pd.to_numeric(raw_df[get_ch_max_col_idx(19)], errors="coerce")

    # CH020: DEW POINT
    df["DEW POINT"] = pd.to_numeric(raw_df[get_ch_max_col_idx(20)], errors="coerce")

    return df.dropna(subset=["DateTime"])

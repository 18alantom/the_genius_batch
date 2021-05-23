import re
import numpy as np

MAX_TOTAL_MARKS_DICT = {
    '2C00255': 600,
    '2C00455': 600,
    '2C00345': 600,
    '3A00145': 600,
    '3L00115': 400,
}

NENG_NUM_COLS = [
    ('1_100', '2_100', '3_100', '4_100', 'total_marks'),
    ('total_marks', 'ac', 'acg', 'gpa'),
    ('ac', 'acg', 'gpa'),
]

NENG_KIDX = [
    ('3L00115'),
    ('2C00255','2C00455','2C00345','3A00145'),
    ('4E00143','2M00733','1P00137'),
]

def get_fixed_and_auged_df(dcourse):
    """
    Function that fixes the numeric values and
    maybe adds a total and percentage column.
    """
    if check_is_eng(dcourse):
        return get_fixed_and_auged_df_eng(dcourse)
    else:
        return get_fixed_and_auged_df_non_eng(dcourse)
    
def check_is_eng(dcourse):
    return dcourse.meta['degree'] == 'B.E'

def get_fixed_and_auged_df_eng(dcourse):
    df = dcourse.df.copy()
    num_cols, mark_cols, max_tot = get_cols_and_tot(dcourse)
    df = clean_numerics(df, num_cols)
    if 'total_marks' in df.columns:
        df = fix_tot_col(df)
        
    df = df.fillna(0)
    
    if 'total_marks' not in df.columns:
        df = append_tot_col(df, mark_cols)
        
    df = append_percent_col(df, max_tot)
    return df

def get_fixed_and_auged_df_non_eng(dcourse):
    df = dcourse.df.copy()
    cols, max_tot = get_cols_and_tot_neng(dcourse.meta['code'])
    df = clean_numerics(df, cols)
    df = df.fillna(0)
    
    if max_tot is not None:
        append_percent_col(df, max_tot)
    return df

def get_cols_and_tot_neng(code):
    idx = [i for i, c in enumerate(NENG_KIDX) if code in c][0]
    if code in MAX_TOTAL_MARKS_DICT:
        total = MAX_TOTAL_MARKS_DICT[code]
    else:
        total = None
    return NENG_NUM_COLS[idx], total

def get_cols_and_tot(dcourse):
    if hasattr(dcourse, 'subj_break_down'):
        sb = dcourse.subj_break_down
        return (
            get_all_num_cols_from_sb(sb),
            *get_mark_cols_and_max_tot_from_sb(sb)
        )
    else:
        raise NotImplementedError("yo wtf?!")

def clean_numerics(df, num_cols):
    df = df.apply(fix_numeric_values, axis=1, args=(num_cols, ))
    return df

def append_tot_col(df, marks_cols):
    marks = df[marks_cols]
    df['total_marks'] = marks.sum(axis=1)
    return df

def append_percent_col(df, max_tot):
    df['percent'] = df['total_marks'] / max_tot
    return df

def fix_tot_col(df):
    return df.apply(get_fixed_tm, axis=1)

def get_fixed_tm(row):
    tm = row['total_marks']
    if "NA" in tm:
        tm = np.nan
    elif "/" in tm:
        tm = tm.split("/")[0]
        tm = tm.split("@")[0]
        tm = float(tm)
    else:
        tm = float(tm)
    row['total_marks'] = tm
    return row

def fix_numeric_values(row, num_cols):
    for c in num_cols:
        row[c] = convert_numeric(row[c])
    return row

ex_num = lambda v: re.findall("(\d+(?:\.\d+)?)\w?", v)
def convert_numeric(v):
    if v in ['--', '---', 'A', 'AA', 'ABS', 'EX']:
        return np.nan
    elif isinstance(v, str):
        return float(ex_num(v)[0])
    else:
        return float(v)

def get_mark_tups_from_sb(sb):
    return [(k,v) for k, i in sb.items() for v in i[0] if re.findall("^\d+/\d+$", v)]

def get_all_num_cols_from_sb(sb):
    return [f"{k}_{v}" for k, i in sb.items() for v in i[0] if not re.findall("^G$", v)] + ['ac', 'acg', 'gpa']

def get_mark_cols_from_mt(mt):
    return [f"{k}_{v}" for k,v in mt]

def get_max_tot_from_mt(mt):
    return sum([int(v.split("/")[0]) for _, v in mt])

def get_mark_cols_and_max_tot_from_sb(sb):
    # From subject break down
    mt = get_mark_tups_from_sb(sb)
    mc = get_mark_cols_from_mt(mt)
    mx = get_max_tot_from_mt(mt)
    return mc, mx
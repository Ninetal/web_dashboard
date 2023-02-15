import os
import pandas as pd
from datetime import datetime
from fuzzywuzzy import process

from components.constants import DATA_FILE, DATA_DIR, FILTER_SUBSTR, DATE_FORMAT_MONTH, DATE_FORMAT_ISO, \
    BASE_DATA_COLUMNS, ALL_VALUES_FLAG, MATCH_RATIO, MIN_WORD_LEN


def get_data() -> pd.DataFrame():
    data_path = os.path.join(DATA_DIR, DATA_FILE)
    data = pd.read_csv(data_path)
    data = clean_data(data)
    return data


def clean_data(data: pd.DataFrame):
    data = data.loc[data['PAID_AMOUNT'] > 0]
    data['MONTH_DT'] = pd.to_datetime(data['MONTH'], format=DATE_FORMAT_MONTH, errors='coerce').dt.date
    data = data.dropna()
    data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY'].str.upper().str.strip()
    for item in FILTER_SUBSTR:
        data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY'].str.replace(item, ' ', regex=True)
    data['CLAIM_SPECIALTY_SPLIT'] = data['CLAIM_SPECIALTY'].apply(lambda x: str(x).split())
    data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY_SPLIT'].apply(lambda x: ' '.join(sorted(set(x), key=x.index)))
    del data['CLAIM_SPECIALTY_SPLIT']
    data['SERVICE_CATEGORY'] = data['SERVICE_CATEGORY'].replace('SpecialistFFS', 'SpecialistsFFS')
    data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY'].replace({'SURGICAL': 'SURGERY',
                                                               'ORTHOPAEDIC': 'ORTHOPEDIC'}, regex=True)
    match_map = match_rows(set(data['CLAIM_SPECIALTY'].tolist()))
    data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY'].replace(match_map)
    substr_map = find_substrings(set(data['CLAIM_SPECIALTY'].tolist()))
    data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY'].replace(substr_map)
    return data


def find_substrings(vals: set) -> dict:
    vals = sorted(vals)
    match_map = {}
    for index, val in enumerate(vals[:-1]):
        for next_index in range(index + 1, len(vals)):
            if vals[next_index].find(val, 0, len(val)) < 0:
                break
            if vals[next_index][len(val)] == ' ':
                continue
            if match_map.get(val) and len(match_map.get(val)) <= len(vals[next_index]):
                continue
            match_map[val] = vals[next_index]
    for item in list(set(match_map.keys()) & set(match_map.values())):
        match_map.pop(item)
    return match_map


def match_rows(vals: set) -> dict:
    results = {}
    vals = sorted(list(filter(lambda x: len(x) >= MIN_WORD_LEN, vals)))
    for val in vals:
        res = process.extract(val, vals, limit=4)
        results[val] = res[1:]
    match_map = {}
    for val in vals:
        if val in match_map.keys():
            continue
        similar_combinations = results.get(val, [])
        for similar_comb, ratio in similar_combinations:
            if ratio <= MATCH_RATIO:
                continue
            match_map[similar_comb] = val
    return match_map


def get_column_vals(data: pd.DataFrame, column_name: str) -> list:
    return sorted(set(data[column_name].dropna().tolist()))


def filter_data(df_data, payer_value, serv_cat_value, cl_spec_value, start_date, end_date) -> pd.DataFrame():
    start_month = convert_date_to_month(start_date)
    end_month = convert_date_to_month(end_date)
    mask = (df_data['MONTH'] >= start_month) & (df_data['MONTH'] <= end_month)
    filtered_df = df_data.loc[mask]
    if len(payer_value) == 0 or len(serv_cat_value) == 0 or len(cl_spec_value) == 0:
        return pd.DataFrame(columns=BASE_DATA_COLUMNS + ['MONTH_DT'])
    if len(payer_value):
        filtered_df = filtered_df.loc[filtered_df['PAYER'].isin(payer_value)]
    if len(serv_cat_value):
        filtered_df = filtered_df.loc[filtered_df['SERVICE_CATEGORY'].isin(serv_cat_value)]
    if len(cl_spec_value) and ALL_VALUES_FLAG not in cl_spec_value:
        filtered_df = filtered_df.loc[filtered_df['CLAIM_SPECIALTY'].isin(cl_spec_value)]
    return filtered_df


def convert_month_to_date(month: int) -> str:
    return datetime.strptime(str(month), DATE_FORMAT_MONTH).strftime(DATE_FORMAT_ISO)


def convert_date_to_month(date: str) -> int:
    return int(datetime.strptime(date, DATE_FORMAT_ISO).strftime(DATE_FORMAT_MONTH))


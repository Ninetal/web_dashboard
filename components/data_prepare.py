import os
import pandas as pd
from datetime import datetime

from components.constants import DATA_FILE, DATA_DIR, AND_SUBSTR, DATE_FORMAT_MONTH, DATE_FORMAT_ISO, \
    BASE_DATA_COLUMNS, ALL_VALUES_FLAG


def get_data() -> pd.DataFrame():
    data_path = os.path.join(DATA_DIR, DATA_FILE)
    data = pd.read_csv(data_path)
    data['MONTH_DT'] = pd.to_datetime(data['MONTH'], format=DATE_FORMAT_MONTH, errors='coerce').dt.date
    data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY'].str.upper().str.strip()
    for item in AND_SUBSTR:
        data['CLAIM_SPECIALTY'] = data['CLAIM_SPECIALTY'].str.replace(item, '/')
    data = data.dropna()
    data = data.loc[data['PAID_AMOUNT'] != 0]
    return data


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


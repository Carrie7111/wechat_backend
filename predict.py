# -*- coding: utf-8 -*-
"""
桃花花期预测模型（scikit-learn 线性回归，与 mock_data 多花种推演联动）。
训练目标列默认为「平坝山脚盛花期」；多花种输出在 mock_data._build_multi_species_predictions 中生成。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# ==============================
# 1. 数据预处理
# ==============================

def add_time_features(df):
    df['日期'] = pd.to_datetime(df['日期'])
    df['年份'] = df['日期'].dt.year
    df['doy'] = df['日期'].dt.dayofyear
    df['hou'] = (df['doy'] - 1) // 5 + 1
    return df


# ==============================
# 2. 候尺度统计
# ==============================

def compute_hou_features(df):
    hou_df = df.groupby(['年份', 'hou']).agg({
        '平均气温': 'mean',
        '最低气温': 'mean',
        '最高气温': 'mean',
        '日照时数': 'sum',
        '降水量20-20': 'sum',
        '空气相对湿度': 'mean'
    }).reset_index()

    return hou_df


# ==============================
# 3. 冷积温（0–7.2℃）
# ==============================

def compute_cold_accumulation(df):
    def cold_func(t):
        if t < 0:
            return 7.2
        elif t <= 7.2:
            return 7.2 - t
        else:
            return 0

    df['cold'] = df['平均气温'].apply(cold_func)
    cold_sum = df.groupby('年份')['cold'].sum()

    return cold_sum


# ==============================
# 4. 构建特征
# ==============================

def extract_feature(hou_df, year, hou, col):
    val = hou_df[(hou_df['年份'] == year) & (hou_df['hou'] == hou)][col]
    return val.values[0] if len(val) > 0 else np.nan


def build_feature_vector(hou_df, cold_sum, year):
    feature = {
        "x1": extract_feature(hou_df, year, 15, '最低气温'),
        "x2": extract_feature(hou_df, year, 9, '平均气温'),
        "x3": extract_feature(hou_df, year, 16, '最高气温'),
        "x4": extract_feature(hou_df, year, 8, '日照时数'),
        "x5": extract_feature(hou_df, year, 9, '降水量20-20'),
        "x6": extract_feature(hou_df, year, 15, '空气相对湿度'),
        "x7": extract_feature(hou_df, year, 4, '日照时数'),
        "x8": extract_feature(hou_df, year, 13, '降水量20-20'),
        "cold": cold_sum.get(year, np.nan)
    }
    return feature


# ==============================
# 5. 花期数据处理（日期 → 日序数）
# ==============================

def date_to_doy(date_str, year):
    date = datetime.strptime(f"{year}-{date_str}", "%Y-%m月%d日")
    return date.timetuple().tm_yday


# ==============================
# 6. 构建训练集
# ==============================

def build_dataset(hou_df, cold_sum, flowering_df, target_col):
    """
    构建训练集
    :param hou_df: 候尺度气象特征数据
    :param cold_sum: 冷积温数据
    :param flowering_df: 花期csv数据
    :param target_col: 要预测的花期列名（如"平坝山脚初花期"）
    :return: 特征矩阵X，目标值y
    """
    X = []
    y = []
    for _, row in flowering_df.iterrows():
        year = row['年份']
        # 跳过花期目标列缺失的行（如2026年的部分花期）
        if pd.isna(row[target_col]):
            continue
        # 构建特征向量
        feature = build_feature_vector(hou_df, cold_sum, year)
        # 跳过气象特征有缺失的行
        if np.any(pd.isnull(list(feature.values()))):
            continue
        X.append(list(feature.values()))
        # 根据指定的目标列获取花期，转换为日序数
        y.append(date_to_doy(row[target_col], year))
    return np.array(X), np.array(y)

def load_weather_data(path):
    df = pd.read_excel(path)

    df.columns = df.columns.str.strip()

    # 标准化列名（防止不同版本）
    rename_map = {
        "平均气温(℃)": "平均气温",
        "最高气温(℃)": "最高气温",
        "最低气温(℃)": "最低气温"
    }
    df = df.rename(columns=rename_map)

    df["日期"] = pd.to_datetime(df["日期"], errors='coerce')

    cols = ["平均气温","最高气温","最低气温","日照时数","降水量20-20","空气相对湿度"]

    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df = df.dropna()

    return df
# ==============================
# 7. 模型训练
# ==============================

def train_model(X, y, verbose=False):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    if verbose:
        # 在 Flask 接口环境下不默认打印，避免 Windows 控制台编码导致异常
        print("R²:", r2_score(y_test, y_pred))
        print("MAE:", mean_absolute_error(y_test, y_pred))

    return model


# ==============================
# 8. 预测函数
# ==============================

def predict_flowering(model, hou_df, cold_sum, feature_year, out_year=None):
    """
    预测花期（返回日期字符串）

    - feature_year: 用于构建特征向量的年份（必须在 hou_df/cold_sum 中存在，否则会产生 NaN）
    - out_year: 将预测得到的“日序数(DoY)”映射到哪个年份的日期；为空则使用 feature_year
    """
    if out_year is None:
        out_year = feature_year

    feature = build_feature_vector(hou_df, cold_sum, feature_year)

    X = np.array(list(feature.values())).reshape(1, -1)
    doy = model.predict(X)[0]

    date = datetime(out_year, 1, 1) + timedelta(days=int(doy) - 1)
    return date.strftime("%Y-%m-%d")


def train_models_for_zone_columns(flowering_df, hou_df, cold_sum, columns):
    """
    同一特征结构下对多个花期目标列分别训练 LinearRegression（多输出/多分类花期预测）。
    columns 例如：["平坝山脚盛花期", "山腰盛花期", "山顶盛花期"]
    """
    models = {}
    for col in columns:
        if col not in getattr(flowering_df, "columns", []):
            continue
        X, y = build_dataset(hou_df, cold_sum, flowering_df, col)
        if len(X) < 3:
            continue
        models[col] = train_model(X, y)
    return models


# ==============================
# 9. 主程序
# ==============================
def main():

    # === 1. 读取气象数据 ===
    weather_df = load_weather_data("龙泉驿56286.xlsx")

    # === 2. 添加时间特征 ===
    weather_df = add_time_features(weather_df)

    # ❗❗❗ 关键：生成 hou_df
    hou_df = compute_hou_features(weather_df)

    # === 3. 冷积温 ===
    cold_sum = compute_cold_accumulation(weather_df)

    # === 4. 花期数据 ===
    flowering_df = pd.read_csv("flowering.csv")

    # 👉 修改点1：新增！指定你要预测的花期类型（可自由切换）
    target_col = "平坝山脚初花期"

    # 👉 修改点2：补全参数！把目标花期传给函数（必须加，否则报错）
    X, y = build_dataset(hou_df, cold_sum, flowering_df, target_col)

    # 默认不输出；需要时可在 main() 中手动改 verbose
    # print(f"预测目标：{target_col} | 样本数:", len(X))

    # === 5. 训练模型 ===
    model = train_model(X, y)

    # === 6. 预测 ===
    year = 2025
    pred = predict_flowering(model, hou_df, cold_sum, year)

    # print(f"{year}年预测花期:", pred)


if __name__ == "__main__":
    main()
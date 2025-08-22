# wiz-stock/data/PredictModel.py
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBClassifier
from sklearn.metrics import mean_squared_error
from pathlib import Path
import os
import re
from SupabaseHandle import insert_rows, request_table
from GetData import get_technical_data 

def insert_predict_rows(df):
    """ 예측 데이터프레임을 predict_modeling 테이블에 업로드 """
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    df_to_dictionary = df.to_dict('records')
    from SupabaseHandle import supabase 
    response = supabase.table('predict_modeling').insert(df_to_dictionary).execute()
    print("[Alert] Success Insert Prediction Rows.")
    return response

# 시계열 데이터 생성 함수 (LSTM용)
def create_sequences(data, sequence_length):
    sequences = []
    targets = []
    for i in range(len(data) - sequence_length - 1):
        sequences.append(data.iloc[i:i+sequence_length].values)
        targets.append(data['Close'].iloc[i+sequence_length])
    return np.array(sequences), np.array(targets)

def run_predictive_modeling():
    """ 
    기술적 지표 데이터 파일(stock_data.csv)을 읽고
    예측 모델링을 수행하여 결과를 데이터베이스에 업로드하는 메인 함수
    """
    print("[Function: run_predictive_modeling] Start")

    current_path = Path.cwd()
    file_path = current_path / 'cache/stock_data.csv'

    try:
        df = pd.read_csv(file_path, dtype={'stock_code': str})
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Please run DataPipeline.py first.")
        return

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['stock_code', 'Date'])

    stock_codes = df['stock_code'].unique()
    results = []

    for stock_code in stock_codes:
        print(f"--- Processing stock code: {stock_code} ---")
        stock_df = df[df['stock_code'] == stock_code].copy()
        stock_df = stock_df.set_index('Date')

        if len(stock_df) < 100:
            print(f"Skipping {stock_code} due to insufficient data.")
            continue

        split_date_str = '2023-01-01'
        split_date = pd.Timestamp(split_date_str)

        try:
            if split_date not in stock_df.index:
                split_date = stock_df[stock_df.index > split_date].index[0]
        except IndexError:
            print(f"Skipping {stock_code} due to no data after {split_date_str}.")
            continue

        ### 1. 머신러닝 (XGBoost) 모델링 - 주가 등락 예측
        features_ml = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_5', 'SMA_20', 'RSI', 'MACD', 'MACD_Signal', 'EMA_26']
        feature_df_ml = stock_df.loc[:, features_ml]
        feature_df_ml['target'] = (feature_df_ml['Close'].shift(-1) > feature_df_ml['Close']).astype(int)
        
        X_predict_ml = feature_df_ml.iloc[-1].drop('target').to_frame().T
        feature_df_ml.dropna(inplace=True)

        X_train_ml = feature_df_ml[feature_df_ml.index < split_date].drop(columns=['target'])
        y_train_ml = feature_df_ml[feature_df_ml.index < split_date]['target']
        X_test_ml = feature_df_ml[feature_df_ml.index >= split_date].drop(columns=['target'])
        y_test_ml = feature_df_ml[feature_df_ml.index >= split_date]['target']

        if len(X_train_ml) == 0 or len(X_test_ml) == 0:
            print(f"Skipping {stock_code} due to empty ML train or test set.")
            continue

        xgb_model = XGBClassifier(n_estimators=100, random_state=42)
        xgb_model.fit(X_train_ml, y_train_ml)
        xgb_pred_next_day = xgb_model.predict(X_predict_ml)
        predicted_trend = "상승" if xgb_pred_next_day[0] == 1 else "하락"
        xgb_pred_test = xgb_model.predict(X_test_ml)
        accuracy_xgb = np.mean(xgb_pred_test == y_test_ml)
        feature_importance = pd.Series(xgb_model.feature_importances_, index=X_train_ml.columns).sort_values(ascending=False)

        ### 2. 딥러닝 (LSTM) 모델링 - 주가 가격 예측
        features_dl = ['Open', 'High', 'Low', 'Close', 'Volume', 'EMA_26']
        feature_df_dl = stock_df.loc[:, features_dl]

        scaler = MinMaxScaler()
        scaled_features_dl = scaler.fit_transform(feature_df_dl)
        scaled_feature_df_dl = pd.DataFrame(scaled_features_dl, columns=features_dl, index=feature_df_dl.index)
        close_scaler = MinMaxScaler()
        close_scaler.fit(feature_df_dl[['Close']])

        sequence_length = 30
        X_dl, y_dl = create_sequences(scaled_feature_df_dl, sequence_length)
        split_index_dl = scaled_feature_df_dl.index.get_loc(split_date) - sequence_length
        split_index_dl = max(0, split_index_dl)
        X_train_dl, X_test_dl = X_dl[:split_index_dl], X_dl[split_index_dl:]
        y_train_dl, y_test_dl = y_dl[:split_index_dl], y_dl[split_index_dl:]

        if len(X_train_dl) == 0 or len(X_test_dl) == 0:
            print(f"Skipping {stock_code} due to empty DL train or test set.")
            continue

        model_dl = tf.keras.Sequential([
            tf.keras.layers.LSTM(units=128, return_sequences=True, input_shape=(X_train_dl.shape[1], X_train_dl.shape[2])),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.LSTM(units=128, return_sequences=False),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.Dense(units=1)
        ])
        model_dl.compile(optimizer='adam', loss='mean_squared_error')
        model_dl.fit(X_train_dl, y_train_dl, epochs=50, batch_size=64, verbose=0)
        
        last_sequence_dl = scaled_feature_df_dl.iloc[-sequence_length:].values
        X_predict_dl = last_sequence_dl.reshape(1, sequence_length, len(features_dl))
        predicted_price_scaled = model_dl.predict(X_predict_dl, verbose=0)
        predicted_price_next_day = close_scaler.inverse_transform(predicted_price_scaled)[0][0]
        
        test_predictions_scaled = model_dl.predict(X_test_dl, verbose=0)
        test_predictions = close_scaler.inverse_transform(test_predictions_scaled)
        y_test_origin = close_scaler.inverse_transform(y_test_dl.reshape(-1, 1))
        rmse_val = np.sqrt(mean_squared_error(y_test_origin, test_predictions))

        # 결과 저장
        results.append({
            'stock_code': stock_code,
            'predict_date': pd.to_datetime('today').strftime('%Y-%m-%d'),
            'trend_predict': predicted_trend,
            'price_predict': round(predicted_price_next_day, 2),
            'trend_accuracy': round(accuracy_xgb, 4),
            'price_rmse': round(rmse_val, 4),
            'top_feature': feature_importance.index[0]
        })
        print(f"  등락 예측 정확도: {accuracy_xgb:.4f}, 가격 예측 RMSE: {rmse_val:.4f}")
        print(f"  가장 영향력 있는 지표: {feature_importance.index[0]}")
        print(f"  --> 다음날 등락 예측: {predicted_trend}")
        print(f"  --> 다음날 종가 예측: {predicted_price_next_day:.2f}")
        print("-" * 30)

    results_df = pd.DataFrame(results)

    # 데이터베이스 업로드
    try:
        print("[Function: run_predictive_modeling] Checking DB for new data...")
        supabase_table = request_table('predict_modeling')
        
        if supabase_table.empty:
            print("[Function: run_predictive_modeling] No data in DB. Uploading all new results.")
            insert_predict_rows(results_df)
        else:
            # 기존 데이터와 새 데이터 비교하여 새로운 행만 추출
            common_cols = ['stock_code', 'predict_date']
            merged_df = pd.concat([supabase_table[common_cols], results_df[common_cols]]).drop_duplicates(keep=False)
            new_rows_to_upload = merged_df.merge(results_df, on=common_cols, how='inner')
            
            if not new_rows_to_upload.empty:
                print(f"[Function: run_predictive_modeling] Found {len(new_rows_to_upload)} new rows. Uploading new results.")
                insert_predict_rows(new_rows_to_upload)
            else:
                print("[Alert] All prediction data is already up-to-date.")
    except Exception as e:
        print(f"Error during prediction data upload: {e}")

    print("[Function: run_predictive_modeling] End")

if __name__ == "__main__":
    # 이 파일을 단독으로 실행하여 모델링 및 업로드 수행
    run_predictive_modeling()
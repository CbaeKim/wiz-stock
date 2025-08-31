# wiz-stock/data/PredictModel.py
import os
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path
import joblib
from datetime import datetime
import shap
from SupabaseHandle import insert_rows, request_table

MODEL_DIR = Path.cwd() / "models"
SCALER_DIR = Path.cwd() / "scalers"
MODEL_DIR.mkdir(exist_ok=True)
SCALER_DIR.mkdir(exist_ok=True)

# 모델 학습에 사용할 Feature 선택
FEATURES = ['Close', 'Volume', 'SMA_50', 'RSI', 'ATR', 'OBV', 'ADX', 'MACD_Soft_-100_100']
SEQUENCE_LENGTH = 30

def insert_predict_rows(df):
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    df_to_dictionary = df.to_dict('records')
    from SupabaseHandle import supabase 
    response = supabase.table('predict_modeling').insert(df_to_dictionary).execute()
    print("[+] 예측 결과를 성공적으로 DB에 업로드했습니다.")
    return response

def create_sequences(data, sequence_length):
    sequences, targets = [], []
    for i in range(len(data) - sequence_length):
        sequences.append(data.iloc[i:i+sequence_length].values)
        targets.append(data['Close'].iloc[i+sequence_length])
    return np.array(sequences), np.array(targets)

def build_lstm_model(input_shape):
    units, dropout, learning_rate = 128, 0.2, 0.001

    inputs = tf.keras.Input(shape=input_shape)

    x = tf.keras.layers.LSTM(units=units, return_sequences=True)(inputs)
    x = tf.keras.layers.Dropout(dropout)(x)
    x = tf.keras.layers.LSTM(units=units)(x)
    x = tf.keras.layers.Dropout(dropout)(x)
    outputs = tf.keras.layers.Dense(units=1)(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs)

    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    return model

def run_predictive_modeling():
    print("[+] 예측 모델링 프로세스를 시작합니다.")
    try:
        csv_path = Path.cwd() / 'cache' / 'stock_data.csv'
        df = pd.read_csv(csv_path, dtype={'stock_code': str}, parse_dates=['Date'])
        df = df.sort_values(['stock_code', 'Date'])
    except FileNotFoundError:
        print(f"[!] 오류: {csv_path} 파일을 찾을 수 없습니다. DataPipeline.py를 먼저 실행하세요.")
        return

    stock_codes = df['stock_code'].unique()
    all_results = []

    for code in stock_codes:
        print(f"\n--- 종목 코드 처리 중: {code} ---")
        
        stock_df = df[df['stock_code'] == code][FEATURES + ['Date']].copy().dropna()
        stock_df = stock_df.set_index('Date')

        if len(stock_df) < SEQUENCE_LENGTH + 50:
            print(f"[!] {code}: 데이터가 부족하여 건너뜁니다 (필요: {SEQUENCE_LENGTH+50}, 보유: {len(stock_df)}).")
            continue

        model_path = MODEL_DIR / f"{code}.keras"
        scaler_paths = {f: SCALER_DIR / f"{code}_{f}_scaler.pkl" for f in FEATURES}
        feature_df = stock_df[FEATURES]
        scaled_df = pd.DataFrame(index=feature_df.index)
        scalers = {}
        for f in FEATURES:
            scaler = MinMaxScaler()
            scaled_df[f] = scaler.fit_transform(feature_df[[f]])
            scalers[f] = scaler
        
        X_train_full, _ = create_sequences(scaled_df, SEQUENCE_LENGTH)

        if model_path.exists():
            print(f"[+] {code}: 기존 모델을 불러옵니다.")
            model = tf.keras.models.load_model(model_path)
            
            last_trained_time = datetime.fromtimestamp(model_path.stat().st_mtime).date()
            last_data_date = stock_df.index[-1].date()

            if last_data_date > last_trained_time:
                print(f"[+] {code}: 새로운 데이터에 대해 추가 학습을 진행합니다.")
                new_data_df = scaled_df[scaled_df.index.date > last_trained_time]
                
                if len(new_data_df) > SEQUENCE_LENGTH:
                    X_new, y_new = create_sequences(new_data_df, SEQUENCE_LENGTH)
                    model.fit(X_new, y_new, epochs=10, batch_size=32, verbose=0)
                    model.save(model_path)
            else:
                print(f"[+] {code}: 모델이 이미 최신 상태입니다.")
        else:
            print(f"[+] {code}: 기존 모델이 없어 새로 학습합니다.")
            if len(X_train_full) == 0:
                print(f"[!] {code}: 학습용 시퀀스를 만들 수 없어 건너뜁니다.")
                continue
            
            model = build_lstm_model(input_shape=(X_train_full.shape[1], X_train_full.shape[2]))
            model.fit(X_train_full, _[:len(X_train_full)], epochs=50, batch_size=64, verbose=0)
            model.save(model_path)
            
        for f, scaler in scalers.items():
            joblib.dump(scaler, scaler_paths[f])

        # 다음 날 종가 예측
        last_sequence = scaled_df.iloc[-SEQUENCE_LENGTH:].values
        X_predict = np.reshape(last_sequence, (1, SEQUENCE_LENGTH, len(FEATURES)))
        
        predicted_scaled_price = model.predict(X_predict, verbose=0)
        predicted_price_float = scalers['Close'].inverse_transform(predicted_scaled_price)[0, 0]
        
        # 최종 예측가를 소수점 첫째 자리에서 반올림하여 정수로 변환
        predicted_price = int(round(predicted_price_float))
        
        # 등락 판단
        last_real_price = feature_df['Close'].iloc[-1]
        predicted_trend = "상승" if predicted_price > last_real_price else "하락"

        # SHAP 분석 추가
        top_feature = 'N/A'
        try:
            # SHAP 분석을 위한 배경 데이터 샘플링 (속도 향상)
            background_data = X_train_full[np.random.choice(X_train_full.shape[0], 100, replace=False)]
            explainer = shap.GradientExplainer(model, background_data)
            shap_values = explainer.shap_values(X_predict)
            
            # Feature별 중요도 계산 (전체 기간에 대한 평균 영향력)
            mean_abs_shap = np.mean(np.abs(shap_values[0]), axis=0)
            top_feature_index = np.argmax(mean_abs_shap)
            top_feature = FEATURES[top_feature_index]
            print(f"  [SHAP] 가장 영향력 있는 Feature: {top_feature}")
        except Exception as e:
            print(f"  [!] SHAP 분석 중 오류 발생: {e}")
        

        print(f"[결과] 현재 종가: {last_real_price:,.0f}원 -> 예측 종가: {predicted_price:,.0f}원. 예측 등락: {predicted_trend}")

        # 결과 저장
        all_results.append({
            'stock_code': code,
            'predict_date': datetime.now().strftime('%Y-%m-%d'),
            'trend_predict': predicted_trend,
            'price_predict': predicted_price,
            'trend_accuracy': 0.0,
            'price_rmse': 0.0,
            'top_feature': top_feature
        })

    # 최종 결과를 데이터베이스에 업로드
    if all_results:
        results_df = pd.DataFrame(all_results)
        try:
            print("\n[+] DB와 비교하여 새로운 예측을 업로드합니다...")
            supabase_table = request_table('predict_modeling')
            
            if supabase_table.empty:
                insert_predict_rows(results_df)
            else:
                common_cols = ['stock_code', 'predict_date']
                supabase_table['predict_date'] = pd.to_datetime(supabase_table['predict_date']).dt.strftime('%Y-%m-%d')
                
                merged_df = pd.merge(results_df, supabase_table[common_cols], on=common_cols, how='left', indicator=True)
                new_rows_to_upload = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])

                if not new_rows_to_upload.empty:
                    print(f"[+] {len(new_rows_to_upload)}개의 새로운 예측을 발견하여 업로드합니다.")
                    insert_predict_rows(new_rows_to_upload)
                else:
                    print("[+] 모든 예측 데이터가 이미 최신 상태입니다.")
        except Exception as e:
            print(f"[!] 예측 데이터 업로드 중 오류 발생: {e}")
    else:
        print("[!] 처리된 결과가 없어 DB 업로드를 건너뜁니다.")

    print("\n[+] 예측 모델링 프로세스를 종료합니다.")

if __name__ == "__main__":
    run_predictive_modeling()

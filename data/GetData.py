# 라이브러리 정의
import pandas as pd
import numpy as np
import yfinance as yf

def get_data(ticker_symbol, period="1y", first_execute = True, date = None):
    try:
        # yfinance 객체 생성
        ticker = yf.Ticker(ticker_symbol)

        if first_execute is True:
            # 주가 데이터 가져오기
            df = ticker.history(period=period)
        else:
            df = ticker.history(start = date)

        if df.empty:
            raise Exception("Data mining Error")

        return df.ffill().sort_index()

    except Exception as e:
        print(f"Error: {e}")
        return None

# 이동평균선 구하는 함수 정의
def get_ma(df, close_col, ma_value, ma):
    """
    df : 데이터프레임
    close_col : 종가 컬럼명 (문자열)
    sma_value : ~일 선 (정수형)
    ma : sma와 ema 여부 문자열

    """
    # SMA 계산일 경우 실행 (기본값)
    if ma == 'sma':
        sma = f'SMA_{ma_value}'
        sma_result = df[close_col].rolling(window = ma_value).mean()

        return sma_result
    
    # EMA 계산일 경우 실행
    elif ma == 'ema':
        try:
		        # 추세 : mean() / 변동성 : std(), var()
            ema = df[close_col].ewm(span = ma_value).mean()
            return ema

        except Exception as e:
            print(f"EMA 계산 오류: {e}")

# MACD를 계산하는 함수 정의
def get_macd(df, close_col, ma_value = [12, 26]):
    # ma_value = 리스트 형태로 전달 -> 기본값은 12일, 26일
    # 2개의 EMA 산출
    ema_1 = get_ma(df, close_col, ma_value = ma_value[0], ma = 'ema')
    ema_2 = get_ma(df, close_col, ma_value = ma_value[1], ma = 'ema')

    return (ema_1 - ema_2)

# 볼린저 밴드 산출 함수
def get_bollinger_bands(df, close_col, ma_value = 20, visualization = False):
    """ 
    중간 밴드 : X 기간 동안의 SMA ( = ma_value )
    상위 밴드 : 중간 밴드 + (X 기간 표준편차 * 2)
    하위 밴드 : 중간 밴드 - (X 기간 표준편차 * 2)
    """
    
    # get_ma 함수를 이용하여 SMA 20일 산출
    middle_band = get_ma(df, close_col, ma_value = ma_value, ma = 'sma')
    upper_band = middle_band + (df[close_col].rolling(window = ma_value).std() * 2)
    lower_band = middle_band - (df[close_col].rolling(window = ma_value).std() * 2)

    # 볼린저 밴드 시각화
    if visualization is True:
        import matplotlib.pyplot as plt

        ## ========== 시각화 도화지 ========== ##
        plt.figure(figsize=(12, 6))

        ## ========== 데이터 Line ========== ##
        plt.plot(df[close_col], label='Close Price', color='blue')       # 종가 라인
        plt.plot(middle_band, label='Middle Band (SMA)', color='orange') # 중간 밴드 라인
        plt.plot(upper_band, label='Upper Band', color='green')          # 상위 밴드 라인
        plt.plot(lower_band, label='Lower Band', color='red')            # 하위 밴드 라인

        ## ========== 영역 색 채움 ========== ##
        plt.fill_between(df.index, upper_band, lower_band, color='lightgray', alpha=0.5)

        ## ======== 그래프 메타 데이터 ======== ##
        plt.title('Bollinger Bands')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.show()

        return middle_band, upper_band, lower_band    
    else:
        return middle_band, upper_band, lower_band

### RSI 계산 함수
def get_rsi(df, day=14):

    # 전날 종가 차이 계산
    delta = df['Close'].diff()

    # 이익 (delta > 0 인 경우)
    gain = delta.where(delta > 0, 0)

    # 손실 (delta < 0 인 경우, 절대값 취함)
    loss = -delta.where(delta < 0, 0)

    # 기간별 이동 평균 이익/손실
    avg_gain = gain.rolling(window=day).mean()
    avg_loss = loss.rolling(window=day).mean()

    # 상대 강도 (RS) 계산
    rs = avg_gain / avg_loss

    # RSI 계산
    rsi = 100 - (100 / (1 + rs))

    return rsi

def get_stochastic(df, k_day=14, d_day=3):
    """ Stochastic Oscillator 계산 함수 """
    # 기간 중 최저가 (Lowest Low) 계산
    lowest_low = df['Low'].rolling(window=k_day).min()

    # 기간 중 최고가 (Highest High) 계산
    highest_high = df['High'].rolling(window=k_day).max()

    # %K 계산
    k_percent = ((df['Close'] - lowest_low) / (highest_high - lowest_low)) * 100

    # %D 계산 (%K의 이동 평균)
    d_percent = k_percent.rolling(window=d_day).mean()

    # 결과를 DataFrame으로 반환
    stochastic_df = pd.DataFrame({
        '%K': k_percent,
        '%D': d_percent
    })

    return stochastic_df

def get_adx(df, high_col, low_col, close_col, period=14):
    
    """
    df : 데이터프레임
    high_col : 고가 컬럼명(문자열)
    low_col : 저가 컬럼명(문자열)
    close_col : 종가 컬럼명(문자열)
    period: ADX 계산 기간, 기본값은 14일 (정수형)
    """

    # TR(True Range, 당일 가격의 움직임의 폭, 갭까지 고려하여 실제로 얼마나 변동되었는지 계산)
    # .abs = 절대값, .shift= 전날 값을 가져옴
    tr = pd.concat([
        df[high_col] - df[low_col],                         # 오늘 고가 - 오늘 저가 = 하루간의 가격폭(오늘 종가)
        (df[high_col] - df[close_col].shift(1)).abs(),      # 오늘 고가 - 어제 종가 = 갭상승
        (df[low_col] - df[close_col].shift(1)).abs()        # 오늘 저가 - 어제 종가 = 갭하락
    ], axis=1).max(axis=1)                                  # 세가지 값 중 가장 큰 값이 실제 가격 폭

    # +DM, -DM
    up_move = df[high_col] - df[high_col].shift(1)  # +DM(상승한 값) = 오늘 고가 - 전일 고가
    down_move = df[low_col].shift(1) - df[low_col]  # -DM(하락한 값) = 전일 저가 - 오늘 저가

    # +DM, -DM 중 사용할 값(주요 추세(방향성)를 비교하기 위해)
    # np.where(조건, A, B) = 조건을 만족하면 A, 또는 B로 구성된 배열 반환
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0), index=df.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0), index=df.index)

    # 평활화 (지속적으로 경향이 어떻게 변했는지 보기 위해)
    # EMA = SMA보다 최신 데이터에 더 많은 가중치를 두어 반응속도가 빠르고 추세감지에 민감하다
    # Series.ewm() = 지수 가중 이동평균(EMA)을 계산하는 메서드
    # span = 평활화 강도 설정
    tr_ema = pd.Series(tr).ewm(span=period, adjust=False).mean()
    plus_dm_ema = pd.Series(plus_dm).ewm(span=period, adjust=False).mean()
    minus_dm_ema = pd.Series(minus_dm).ewm(span=period, adjust=False).mean()

    # +DI, -DI(변동값(+DM,-DM)이 전체 변동성(TR)에서 얼마나 기여했는가)를 백분율로 표현
    plus_di = 100 * (plus_dm_ema / tr_ema)
    minus_di = 100 * (minus_dm_ema / tr_ema)

    # DX = 상승세력(+DI)과 하락세력(-DI)의 차이(방향성 크기의 비율), ADX = 추세 강도 판단
    # DX= (|+DI - -DI| / (+DI + -DI)) × 100
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.ewm(span=period, adjust=False).mean()

    return pd.DataFrame({'ADX': adx, 'DX': dx, '+DI': plus_di, '-DI': minus_di})

def get_atr(df, high_col, low_col, close_col, window=14):
    """ ATR 산출 함수 """
    ### TR 계산
    ## 1. 당일 고가 - 당일 저가
    range1 = df[high_col] - df[low_col]

    ## 2. |당일 고가 - 전일 종가|
    range2 = abs(df[high_col] - df[close_col].shift(1))

    ## 3. |당일 저가 - 전일 종가|
    range3 = abs(df[low_col] - df[close_col].shift(1))

    TR = pd.concat([range1, range2, range3], axis=1).max(axis=1) # 세 값 중 가장 큰 값을 선택

    ### ATR 계산
    # 단순 이동 평균(SMA)
    # atr TR.rolling(window=window).mean()
    # 지수 이동 평균(EMA) 
    atr = TR.ewm(span=window, adjust=False).mean()

    return atr

def get_obv(df, close_col, volume_col):
    '''
    # df: 데이터프레임
    # close_col: 종가 컬럼(str)
    # volume_col: 거래량 컬럼(str)
    '''
    # OBV 초기값 설정
    obv = [0]
    for i in range(1, len(df)): # 전일 종가와 당일 종가를 비교해야하므로
        # 당일 종가 > 전일 종가 --> OBV = OBV + 거래량
        if df[close_col].iloc[i] > df[close_col].iloc[i-1]:
            obv.append(obv[-1] + df[volume_col].iloc[i])
        # 당일 종가 < 전일 종가 --> OBV = OBV - 거래량
        elif df[close_col].iloc[i] < df[close_col].iloc[i-1]:
            obv.append(obv[-1] - df[volume_col].iloc[i])
        else:
            # 당일 종가 = 전일 종가 --> OBV 유지
            obv.append(obv[-1])

    return pd.Series(obv, index = df.index)

def analyze_data(ticker_symbol, period="max", start_date = None):
    """ 주가 데이터 Load & 기술적 분석 지표를 계산 후 DataFrame으로 반환 """
    # get_data 함수를 사용하여 주가 데이터 불러오기 및 전처리
    try:
        if start_date is None:
            df = get_data(ticker_symbol, period=period)
        else:
            df = get_data(ticker_symbol, first_execute = False, date = start_date)
    except:
        raise Exception("Error get_data fucnction")

    # 기술적 분석 지표 계산 및 DataFrame에 추가

    # 이동 평균선 (SMA, EMA)
    try:
        df['SMA_5'] = get_ma(df, 'Close', ma_value=5, ma='sma')
        df['SMA_20'] = get_ma(df, 'Close', ma_value=20, ma='sma')
        df['EMA_12'] = get_ma(df, 'Close', ma_value=12, ma='ema')
        df['EMA_26'] = get_ma(df, 'Close', ma_value=26, ma='ema')
    except Exception as e:
        print(f"Error SMA/EMA: {e}")

    # MACD
    try:
        macd_result = get_macd(df, 'Close')
        df['MACD'] = macd_result
        # Signal Line (MACD의 9일 EMA)
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        # MACD Histogram
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    except Exception as e:
         print(f"Error MACD: {e}")

    # 볼린저 밴드
    try:
        middle_band, upper_band, lower_band = get_bollinger_bands(df, 'Close', ma_value=20, visualization=False)
        df['Bollinger_Mid'] = middle_band
        df['Bollinger_Upper'] = upper_band
        df['Bollinger_Lower'] = lower_band
    except Exception as e:
        print(f"Error Bollinger_bands: {e}")

    # RSI
    try:
        df['RSI'] = get_rsi(df, day=14)
    except Exception as e:
        print(f"Error RSI: {e}")

    # Stochastic Oscillator
    try:
        stochastic_result = get_stochastic(df, k_day=14, d_day=3)
        df['%K'] = stochastic_result['%K']
        df['%D'] = stochastic_result['%D']
    except Exception as e:
        print(f"Error Stochastic: {e}")

    # ADX (Average Directional Index)
    try:
        adx_result = get_adx(df, high_col='High', low_col='Low', close_col='Close', period=14)
        df['ADX'] = adx_result['ADX']
        df['+DI'] = adx_result['+DI']
        df['-DI'] = adx_result['-DI']
    except Exception as e:
        print(f"Error ADX: {e}")

    # ATR (Average True Range)
    try:
        df['ATR'] = get_atr(df, high_col='High', low_col='Low', close_col='Close', window=14)
    except Exception as e:
        print(f"Error ATR: {e}")

    # OBV (On-Balance Volume)
    try:
        df['OBV'] = get_obv(df, close_col='Close', volume_col='Volume')
    except Exception as e:
        print(f"Error OBV: {e}")

    # Final DataFrame Reprocess
    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    df.insert(0, 'stock_code', ticker_symbol[:-3], allow_duplicates = False)
    df = df.replace(np.nan, 0)

    change_columns = ['Open', 'High', 'Low', 'Close',
       'Dividends', 'Stock Splits', 'SMA_5', 'SMA_20', 'EMA_12', 'EMA_26',
       'MACD', 'MACD_Signal', 'MACD_Hist', 'Bollinger_Mid', 'Bollinger_Upper',
       'Bollinger_Lower', 'RSI', '%K', '%D', 'ADX', '+DI', '-DI', 'ATR']

    df[change_columns] = df[change_columns].round(2)
    
    return df
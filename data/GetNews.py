import os, requests, json, re, time
import pandas as pd
import numpy as np
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from supabase import Client, create_client


# Load Parent Path
current_path = Path.cwd()
env_path = current_path / '.env'

load_dotenv(dotenv_path = env_path)

# Set Supabase API KEY
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase 클라이언트 연결 완료.")
except Exception as e:
    print(f"Supabase 클라이언트 연결 실패: {e}")

# Set Gemini API KEY
genai.configure(api_key = os.getenv('GEMINI_API_KEY'))

try:
    # Naver Developer API Configuration
    client_id = os.getenv('NAVER_CLIENT_ID')
    client_secret = os.getenv('NAVER_CLIENT_SECRET')
    print("API Configuration Load Success")
except Exception as e:
    print(f"API Configuration Load Error: {e}")

def request_gem(text: str, prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """ Get Reponse from Gemini """
    client = genai.GenerativeModel(model)

    contents = [
        {
            'role': 'user',
            'parts': [f'{prompt}\n\n요청사항: {text}']
        }
    ]

    time.sleep(25)

    response = client.generate_content(
        contents = contents
    )

    return response.text

class GetNewsData():
    def __init__(self, client_id = client_id, client_secret = client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
    

    def get_news_data(self, query, display=25, start=1, sort='date'):
        """
        네이버 뉴스 검색 API를 사용하여 뉴스 링크와 제목을 가져오는 함수
        
        Parameters:
        - query: 검색할 키워드
        - display: 검색 결과 출력 건수 (기본값: 10, 최대: 100)
        - start: 검색 시작 위치 (기본값: 1, 최대: 1000)
        - sort: 정렬 옵션 ('sim': 정확도순, 'date': 날짜순)
        """
        
        # API 엔드포인트
        url = "https://openapi.naver.com/v1/search/news.json"
        
        # 헤더 설정
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        # 파라미터 설정
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        
        links = []
        titles = []
        
        try:
            # API 요청
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # HTTP 에러가 있으면 예외 발생
            
            # JSON 응답 파싱
            data = response.json()
            
            # 링크와 제목들 추출
            for item in data.get('items', []):
                link = item.get('link')
                
                links.append(link)
            
            return links
            
        except requests.exceptions.RequestException as e:
            print(f"API 요청 중 오류 발생: {e}")
            return [], []
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 중 오류 발생: {e}")
            return [], []
        except Exception as e:
            print(f"예상치 못한 오류 발생: {e}")
            return [], []
        
    def get_htmltext(self, news_links):
        """ 
        get_news_link()의 결과값을 매개변수로 넣어, 웹 페이지의 텍스트만을 리스트 형태로 리턴
        """
    
        results = []
        
        for link in news_links:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            try:
                response = requests.get(link, headers = headers).text
                soup = BeautifulSoup(response, 'html.parser').text

                cleaned_soup = re.sub(r'\n+', '\n', soup)

                results.append(cleaned_soup)
            except:
                results.append(f"failed: {link}")
                print(f"failed: {link}")

        return results
    
    def get_sentimental_score(self, results):
        
        # 토큰 제한으로 인한 뉴스 50개 단위 분할
        part = '[next_news]'.join(results)

        prompt_text = """
        당신은 경제 뉴스 분석 전문가입니다.
        아래 입력된 뉴스들에 대해 감성분석을 수행하세요.
        각 뉴스는 문자열 "[next_news]"로 구분되어 있습니다.
        뉴스 분석 시, 하나의 뉴스가 끝나면 다음 뉴스는 "[next_news]"로 시작합니다.

        [분석 규칙]
        1. 감성 점수 범위:
        - 긍정(positive): 51 ~ 100점
        - 부정(negative): 1 ~ 50점
        2. 분석 결과는 각 뉴스의 날짜와 점수로만 표현하세요.
        3. 반드시 무조건 JSON 배열 형식으로 출력하고, 개행 없이 한 줄로 작성하세요.

        [출력 예시]
        [{"date":"2025-01-01","score":51},{"date":"2025-01-02","score":45}]

        뉴스 데이터:
        """
        try:
            # 첫번째 시도: AI가 실수를 할 수 있음
            print("First Challenge")
            prompt_result = request_gem(prompt = prompt_text, text = '[next_news]'+part)
            prompt_result = prompt_result.replace('json', '', 1)

            final_dict = json.loads(prompt_result)
            print(type(final_dict))
            print("Translate Dictionary Success!")
            
            return final_dict
        except:
            try:
                # 두번째 시도: 한 번 더 시도
                print("Second Challenge")
                prompt_result = request_gem(prompt = prompt_text, text = '[next_news]'+part)
                prompt_result = prompt_result.replace('json', '', 1)

                final_dict = json.loads(prompt_result)
                print(type(final_dict))
                print("Translate Dictionary Success!")
            
                return final_dict
            except:
                # 세번째 시도: 한 번 더 시도
                print("Last Challenge")
                prompt_result = request_gem(prompt = prompt_text, text = '[next_news]'+part)
                prompt_result = prompt_result.replace('json', '', 1)

                final_dict = json.loads(prompt_result)
                print(type(final_dict))
                print("Translate Dictionary Success!")
            
                return final_dict

    def run(self, query, get_page_value):
        """ Sentimental Score Analysis 25 News """
        
        collect = GetNewsData()
        
        current_path = Path.cwd()
        dir_path = current_path / 'cache'

        display = 25
        results = []

        try:
            for start in range(1, (get_page_value * display) + 1, 25):
                # Extract News URL
                news_links = collect.get_news_data(query = query, display = display, start = start)
                print(f"{query} start: {start}")

                # Extract string in URL
                extract_news_texts = collect.get_htmltext(news_links)

                # Execute Sentimental-Analysis
                sentimental_results = collect.get_sentimental_score(extract_news_texts)
                time.sleep(1)

                # Cache
                with open(dir_path / f'sentimental_cache_{query}_{start}.json', 'w', encoding='utf-8') as f:
                    json.dump(sentimental_results, f, indent = 4, ensure_ascii = False)

                if start == 1:
                    results.append(sentimental_results)
                else:
                    results.extend(sentimental_results)
            
            return results
        except:
            print("Error")
    
def combine_json_files(query, get_page_value):
    """ 생성된 JSON Cache 파일을 합쳐서 하나의 파일로 생성 """
    # JSON 캐시 파일 경로 정의
    current_path = Path.cwd()
    dir_path = current_path / 'cache'

    # JSON 캐시 파일 서치
    pattern = f'sentimental_cache_{query}_*.json'

    # JSON 파일 목록 반환
    json_files = dir_path.glob(pattern)
    json_file_names = [file for file in json_files]

    # 정상적으로 분석이 안 된 경우 체크
    if len(json_file_names) < get_page_value:
        need_numbers = {val for val in range(1, 1000, 25)}
        exist_file_numbers = [json_file.name for json_file in json_file_names]
        extract_exist_numbers = {int(re.findall(r'\d+', exist_file)[0]) for exist_file in exist_file_numbers}
        non_exist_numbers = need_numbers ^ extract_exist_numbers

        start_index = min(list(non_exist_numbers))

        collect = GetNewsData()

        run_result = collect.run(query = query, get_page_value = start_index)

        json_files = dir_path.glob(pattern)
        json_file_names = [file for file in json_files]
    
    final_json_dict = []

    for json_file in json_file_names:
        with json_file.open('r', encoding = 'utf-8') as f:
            data = json.load(f)

            if isinstance(data, list):
                final_json_dict.extend(data)
                print("Data Extend Success!")
            else:
                print("Skip json_file")
    
    with open(dir_path / f'{query}_news.json', 'w', encoding = 'utf-8') as f:
        json.dump(final_json_dict, f, indent = 4, ensure_ascii = False)
    
    for file in dir_path.glob(pattern):
        try:
            file.unlink()
        except:
            print("Sentimental Cache File Delete Error")
    
    return final_json_dict

def json_files_load(top_10_stocks):
    """ cache 디렉터리 내 json 파일들을 sentimental_score 테이블에 업로드 """
    not_updated_files = []
    current_path = Path.cwd()
    dir_path = current_path / 'cache'

    df = pd.DataFrame(top_10_stocks)
    stock_names = [stock['name'] for stock in top_10_stocks]
    stock_codes = [stock['code'][:-3] for stock in top_10_stocks]
    start_index = 0

    for file_name in stock_names:
        # Find Json file
        file_path = list(dir_path.glob(file_name+'_news.json'))

        try:
            # Open Json File >> DataFrame
            with open(file_path[0], 'r', encoding = 'utf-8') as f:
                json_df = pd.DataFrame(json.load(f))
            
                # Prerprocess DataFrame
                proprecessed_df = json_df.groupby(by='date', as_index=False).mean()
                proprecessed_df['score'] = proprecessed_df['score'].astype(int)
                proprecessed_df.insert(loc = 1, column = 'stock_code', value = stock_codes[start_index])               
                proprecessed_df['label'] = np.where(proprecessed_df['score'] >= 50, 1, 0)
                df_to_dictionary = proprecessed_df.to_dict('records')

                # Insert Table
                response = supabase.table('sentimental_score').insert(df_to_dictionary).execute()

                file_path[0].unlink()
        except:
            print(f"Failed: insert table -> '{file_path}'")
            not_updated_files.append(file_path)
            pass

        start_index += 1
    if len(not_updated_files) < 10:
        print(f"Not updated Files: {len(not_updated_files)}")
        print(f"Files: {not_updated_files}")
    else:
        print("Database Update Success")

    return not_updated_files
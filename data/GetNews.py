import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os, requests, json, re, time

def request_gem(text: str, prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """ Get Reponse from Gemini """
    client = genai.GenerativeModel(model)

    contents = [
        {
            'role': 'user',
            'parts': [f'{prompt}\n\n요청사항: {text}']
        }
    ]

    response = client.generate_content(
        contents = contents
    )

    return response.text

# Load Parent Path
current_path = Path(os.getcwd())
parent_path = current_path.parent / '.env'

load_dotenv(dotenv_path = parent_path)

# Set Gemini API KEY
genai.configure(api_key = os.getenv('GEMINI_API_KEY'))

try:
    # Naver Developer API Configuration
    client_id = os.getenv('NAVER_CLIENT_ID')
    client_secret = os.getenv('NAVER_CLIENT_SECRET')
    print("API Configuration Load Success")
except Exception as e:
    print(f"API Configuration Load Error: {e}")


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
        
        Returns:
        - tuple: (뉴스 링크 리스트, 뉴스 제목 리스트)
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
        너는 경제 뉴스 분석 전문가야.
        뉴스에 대해서 감성분석해줄래? 총 100개의 뉴스가 있어.
        각 뉴스는 '[next_news]' 문자로 구분되어있어.
        하나의 뉴스가 끝나면 다음 뉴스는 '[next_news]'로 시작해.

        [지시 사항]
        1. 감성분석 결과는 뉴스기사의 날짜와 점수로 산정해줘
        - positive: 51 ~ 100점 / negative: 1 ~ 50점

        2. 무조건 JSON 형태로 내게 답변해. (개행 금지)

        3. 최종 답변 전 답변이 아래 JSON 형태가 맞는지 한 번 더 검토해
        
        json{"date": "2025-01-01", "score": 51}
        
        """
        try:
            # 첫번째 시도: AI가 실수를 할 수 있음
            print("First Challenge")
            prompt_result = request_gem(prompt = prompt_text, text = '[next_news]'+part)
            prompt_result = prompt_result.replace('json', '', 1)
            print(prompt_result)

            final_dict = json.loads(prompt_result)
            print("Translate Dictionary Success!")
            time.sleep(30)
            
            return final_dict
        except:
            # 두번째 시도: 한 번 더 시도
            print("Second Challenge")
            prompt_result = request_gem(prompt = prompt_text, text = '[next_news]'+part)
            prompt_result = prompt_result.replace('json', '', 1)
            print(prompt_result)

            final_dict = json.loads(prompt_result)
            print("Translate Dictionary Success!")
            time.sleep(30)

        try:
            # 세번째 시도: 한 번 더 시도
            print("Second Challenge")
            prompt_result = request_gem(prompt = prompt_text, text = '[next_news]'+part)
            prompt_result = prompt_result.replace('json', '', 1)
            print(prompt_result)

            final_dict = json.loads(prompt_result)
            print("Translate Dictionary Success!")
            time.sleep(30)
        
        except:
            # 네번째 시도: 한 번 더 시도
            print("Second Challenge")
            prompt_result = request_gem(prompt = prompt_text, text = '[next_news]'+part)
            prompt_result = prompt_result.replace('json', '', 1)
            print(prompt_result)

            final_dict = json.loads(prompt_result)
            print("Translate Dictionary Success!")
            time.sleep(30)

            return final_dict

    def run(self, query, start):
        """ Sentimental Score Analysis 1000 News """

        collect = GetNewsData()
        
        current_path = Path.cwd()
        dir_path = current_path.parent / 'cache'

        display = 25
        start = start
        results = []

        try:
            while True:
                if start == 501:
                    break
                
                print("START")

                # Extract News URL
                news_links = collect.get_news_data(query = query, display = display, start = start)

                # Extract string in URL
                extract_news_texts = collect.get_htmltext(news_links)

                # Execute Sentimental-Analysis
                sentimental_results = collect.get_sentimental_score(extract_news_texts)

                # Cache
                with open(dir_path / f'sentimental_cache_{query}_{start}.json', 'w', encoding='utf-8') as f:
                    json.dump(sentimental_results, f, indent = 4, ensure_ascii = False)

                if start == 1:
                    results.append(sentimental_results)
                else:
                    results.extend(sentimental_results)
                
                start += display
        except:
            print("Error")

        combine_json_files(query)
            
        return results
    
def combine_json_files(query):
    # JSON 캐시 파일 경로 정의
    current_path = Path.cwd()
    dir_path = current_path.parent / 'cache'

    # JSON 캐시 파일 서치
    pattern = f'sentimental_cache_{query}_*.json'

    # JSON 파일 목록 반환
    json_files = dir_path.glob(pattern)
    json_file_names = [file for file in json_files]

    # 정상적으로 분석이 안 된 경우 체크
    if len(json_file_names) < 20:
        need_numbers = {val for val in range(1, 1000, 25)}
        exist_file_numbers = [json_file.name for json_file in json_file_names]
        extract_exist_numbers = {int(re.findall(r'\d+', exist_file)[0]) for exist_file in exist_file_numbers}
        non_exist_numbers = need_numbers ^ extract_exist_numbers

        start_index = min(list(non_exist_numbers))

        collect = GetNewsData()

        run_result = collect.run(query = query, start = start_index)

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
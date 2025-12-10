import requests
import time
from dotenv import load_dotenv
import os
import database

def get_text_from_url(url, max_length) -> str:
    """
    주어진 URL에서 텍스트 데이터를 크롤링하여 반환합니다.
    """
    try:
        response = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        return text[:max_length]
    except requests.RequestException as e:
        print(f"Error fetching URL {url} skip")
        return None

def fetch_references(keywords: str, database: database.Database, max_length = 2000) -> dict[str, list[dict[str, str]]]:
    """
    주어진 키워드를 구글 검색을 통해 검색, 상위 max_per 개의 논문 및 자료를 크롤링하여 반환합니다.
    """
    load_dotenv()
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GOOGLE_SEARCHENGINE_ID = os.getenv('GOOGLE_SEARCHENGINE_ID')
    results:dict = {}
    for kw in keywords:
        previous_search_result = database.get_search_results_for_keyword(kw)
        if previous_search_result:
            items = []
            for res in previous_search_result:
                items.append({
                    'title': res['title'],
                    'link': res['link'],
                    'text': get_text_from_url(res['link'], max_length) or res['snippet']
                })
            results[kw] = items
            continue
        items = []
        #google custom search
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCHENGINE_ID,  # 여기에 자신의 CSE ID를 입력하세요
            'q': kw,
        }
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                title = item.get('title')
                link = item.get('link')
                snippet = item.get('snippet', '')

                # 데이터베이스에 저장
                database.add_search_result(kw, title, link, snippet)
                text = get_text_from_url(link, max_length) or snippet

                items.append({
                    'title': title,
                    'link': link,
                    'text': text  # 최대 길이 제한
                })
        else:
            print(f"Error fetching search results for keyword '{kw}': {response.status_code}")

        results[kw] = items
    return results

import requests
import time

WIKI_API_SEARCH = 'https://en.wikipedia.org/w/api.php'

def fetch_references(keywords, max_per=2, lang='en'):
    """키워드에 대해 위키백과 또는 더미 텍스트를 통해 참조 자료를 가져옵니다.
    
    Wikipedia 검색을 시도하고, 실패하거나 텍스트가 없으면 더미 텍스트 생성
    returns: dict keyword -> list of {'title':str, 'text':str}
    """
    results = {}
    for kw in keywords:
        items = []
        try:
            # Wikipedia 검색
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': kw,
                'format': 'json',
                'srlimit': max_per
            }
            r = requests.get(WIKI_API_SEARCH, params=params, timeout=5)
            r.raise_for_status()
            data = r.json()
            
            search_results = data.get('query', {}).get('search', [])[:max_per]
            for s in search_results:
                title = s.get('title', '')
                snippet = s.get('snippet', '')
                
                # 페이지 요약 불러오기
                text = ''
                try:
                    summary_params = {
                        'action': 'query',
                        'prop': 'extracts',
                        'exintro': True,
                        'explaintext': True,
                        'titles': title,
                        'format': 'json'
                    }
                    r2 = requests.get(WIKI_API_SEARCH, params=summary_params, timeout=5)
                    r2.raise_for_status()
                    d2 = r2.json()
                    pages = d2.get('query', {}).get('pages', {})
                    for p in pages.values():
                        text = p.get('extract', '')
                        if text:
                            break
                except Exception:
                    pass
                
                # 텍스트가 없으면 snippet 사용
                if not text:
                    text = snippet
                
                # 텍스트가 충분하면 추가
                if text and len(text) > 20:
                    items.append({'title': title, 'text': text})
                    time.sleep(0.1)
        except Exception as e:
            print(f"[DEBUG] Wikipedia search failed for '{kw}': {e}")
            pass
        
        # Wikipedia에서 결과를 못 찾으면 더미 텍스트 생성
        if not items:
            dummy_text = f"""
This is reference material about {kw}.

{kw} is a significant topic in modern technology and science.
It plays an important role in various applications and research areas.
The concept of {kw} has evolved significantly over time.
Many experts and researchers have contributed to the understanding of {kw}.
Understanding {kw} is essential for professionals in related fields.
            """.strip()
            items.append({
                'title': f'Reference: {kw}',
                'text': dummy_text
            })
            print(f"[DEBUG] Using dummy text for keyword '{kw}'")
        
        results[kw] = items
    return results

from collections import Counter
import re

def select_keywords(texts, top_n=5):
    """텍스트 목록에서 가장 많이 나온 단어(top_n)를 반환합니다.

    texts: list of strings
    returns: list of keywords (strings)
    """
    word_re = re.compile(r"[\w가-힣]+")
    stopwords = set(['의','가','이','은','는','을','를','에','와','과','도','하다','있다','있'])
    counter = Counter()
    for t in texts:
        if not t:
            continue
        # 토큰화 후 불용어와 한 글자 토큰(숫자 또는 단일 영문자 포함)은 제외
        raw_words = word_re.findall(t)
        words = []
        for w in raw_words:
            if not w:
                continue
            lw = w.lower()
            # 불용어 필터
            if lw in stopwords:
                continue
            # 숫자만 구성된 토큰 제외
            if lw.isdigit():
                continue
            # 한 글자 토큰(한글, 영문 단일 문자 등) 제외
            if len(lw) <= 1:
                continue
            words.append(lw)
        counter.update(words)
    most = [w for w, _ in counter.most_common(top_n)]
    return most

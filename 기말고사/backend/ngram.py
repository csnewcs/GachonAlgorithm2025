import re
from collections import deque

_word_re = re.compile(r"[\w가-힣]+")

def tokenize(text):
    if not text:
        return []
    return [w.lower() for w in _word_re.findall(text)]


def ngrams_from_tokens(tokens, n=3):
    """토큰 리스트에서 n-gram(토큰 단위)을 생성하여 set으로 반환"""
    if n <= 0:
        return set()
    if len(tokens) < n:
        return set()
    q = deque()
    res = set()
    for t in tokens:
        q.append(t)
        if len(q) == n:
            res.add(' '.join(q))
            q.popleft()
    return res


def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    ia = set(a)
    ib = set(b)
    inter = ia & ib
    uni = ia | ib
    if not uni:
        return 0.0
    return len(inter) / len(uni)


def ngram_similarity(text1, text2, n=3):
    """단순 n-gram Jaccard 유사도 반환 (0..1)

    토큰 단위 n-gram을 사용합니다. 기본 n=3.
    """
    t1 = tokenize(text1)
    t2 = tokenize(text2)
    g1 = ngrams_from_tokens(t1, n)
    g2 = ngrams_from_tokens(t2, n)
    return jaccard(g1, g2)

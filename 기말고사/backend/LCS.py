def find_lcs_positions(a, b) -> dict:
    """LCS를 추적하여 a, b에서 겹치는 부분의 구간(시작, 끝)을 반환합니다.
    
    returns: {
        'a_start': int (텍스트 a에서 겹치는 부분의 시작 위치),
        'a_end': int (끝 위치, 포함),
        'b_start': int (텍스트 b에서 겹치는 부분의 시작 위치),
        'b_end': int (끝 위치, 포함),
        'lcs_length': int (공통 부분수열의 길이)
    }
    """
    if not a or not b:
        return {'a_start': -1, 'a_end': -1, 'b_start': -1, 'b_end': -1, 'lcs_length': 0}
    
    la, lb = len(a), len(b)
    # DP 테이블 구성
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    lcs_len = dp[la][lb]
    if lcs_len == 0:
        return {'a_start': -1, 'a_end': -1, 'b_start': -1, 'b_end': -1, 'lcs_length': 0}
    
    # 역추적: LCS 문자열과 위치 파악
    i, j = la, lb
    lcs_chars = []
    a_indices = []
    b_indices = []
    
    while i > 0 and j > 0:
        if a[i-1] == b[j-1]:
            lcs_chars.append(a[i-1])
            a_indices.append(i-1)
            b_indices.append(j-1)
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    if not a_indices or not b_indices:
        return {'a_start': -1, 'a_end': -1, 'b_start': -1, 'b_end': -1, 'lcs_length': 0}
    
    # 역순이므로 다시 정렬
    a_indices.reverse()
    b_indices.reverse()
    
    a_start = a_indices[0]
    a_end = a_indices[-1]
    b_start = b_indices[0]
    b_end = b_indices[-1]
    
    return {
        'a_start': a_start,
        'a_end': a_end,
        'b_start': b_start,
        'b_end': b_end,
        'lcs_length': lcs_len
    }

def similarity_score(a, b):
    """간단한 유사도 점수: LCS 길이를 기준으로 정규화하여 0..1 반환."""
    if not a or not b:
        return 0.0
    # 문자열 길이 기준으로 정규화 (최소 길이로 나눔)
    lcs = find_lcs_positions(a, b)
    denom = min(len(a), len(b))
    if denom == 0:
        return 0.0
    return lcs, lcs['lcs_length'] / denom

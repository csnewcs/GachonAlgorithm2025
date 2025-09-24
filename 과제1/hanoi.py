# 참고자료: http://www.mathought.com/bbs/board.php?bo_table=04_5&wr_id=122&sfl=&stx=&sst=wr_datetime&sod=asc&sop=and&page=2
# 참고자료2: https://zoosso.tistory.com/489
# 1, 2, 2, 4, 4, 4, 8, 8, 8, 8, 16, 16, 16, 16, 16...
# 즉 계챠가 2^(k-1)개씩 k번 반복됨
# 그리고 그 최소 원판 이동을 하는 방법은 원판 개수를 n, 기둥을 A, B, C, D라고 할 때 n // 2원판을 먼저 옮기고, 아래 원판을 목표 지점으로 옮긴 후 다시 임시로 옮겨둔 원판을 목표 지점으로 옮기는 것 같음

# 시각화는 https://namu.wiki/w/%ED%95%98%EB%85%B8%EC%9D%B4%EC%9D%98%20%ED%83%91?from=%ED%95%98%EB%85%B8%EC%9D%B4%20%ED%83%91#s-5.1 여기에서 가져와 편형

import time


def show_hanoi(n):  
    st_a = [p+p[::-1] for p in [" "*(n-i-1)+"="*(i+1) for i in range(n)]]  
    st_b = [s+s[::-1] for s in [" "*(n-1)+"|"]*n]  
    st_c = [s for s in st_b]  
    st_d = [s for s in st_b]
    all = [st_a, st_b, st_c, st_d]
    A= 0  
    B= 1  
    C= 2  
    D= 3
    print_hanoi(st_a,st_b,st_c, st_d)  
    return move_hanoi_with_4pegs(n, all, A, B, C, D)  
  
def move_hanoi_with_3pegs(n,all,fr,tmp,to, stopAt=0):
    if n <= stopAt:
        return
    if n==1 :
        all[fr][find_top(all[fr])], all[to][find_top(all[to])-1] = all[to][find_top(all[to])-1], all[fr][find_top(all[fr])]  
        print_hanoi(*all)
    else:
        move_hanoi_with_3pegs(n-1,all,fr,to,tmp, stopAt)
        all[fr][find_top(all[fr])], all[to][find_top(all[to])-1] = all[to][find_top(all[to])-1], all[fr][find_top(all[fr])]  
        print_hanoi(*all)
        move_hanoi_with_3pegs(n-1,all,tmp,fr,to, stopAt)  
  
def move_hanoi_with_4pegs(n, all, fr, tmp, to, k): # k는 임시로 쓸 기둥  
    if n==1 :  
        move_hanoi_with_3pegs(1, all, fr, tmp, to)
        print_hanoi(*all)
    else :  
        tempK = n // 2
        move_hanoi_with_3pegs(tempK, all, fr, tmp, k)
        move_hanoi_with_3pegs(n, all, fr, tmp, to, tempK)
        move_hanoi_with_3pegs(tempK, all, k, tmp, to)


def find_top(lst):  
    N = len(lst)  
    for i,l in enumerate(lst):  
        if l != " "*(N-1)+"||"+" "*(N-1):  
            return i  
    else : return N
  

move_count = 0
def print_hanoi(st_a,st_b,st_c, st_d):
    layers= list(zip(st_a,st_b,st_c, st_d))  

    print("\033[2;0H")
    time.sleep(0.5)
    global move_count
    print('이동횟수: ', move_count)
    move_count = move_count + 1
    print(*["".join(l) for l in layers], sep="\n")
  
while True: 
    tower = int(input("디스크 수: "))  
    if tower < 1:  
        print("1 이상의 정수를 입력해주세요")
    else:  
        print('\033[?1049h') # 터미널 가져오기
        print('\033[2J') # 화면 지우기
        print('\033[H') # 커서 맨 위로 이동
        print('디스크 수: ',tower)
        show_hanoi(tower)  
        print("완료 (5초 후 종료)")
        time.sleep(5)
        print('\033[?1049l') # 터미널 원래대로
        break
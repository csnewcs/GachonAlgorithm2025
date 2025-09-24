# 하노이탑 문제에서 기둥 4개 사용하여 디스크를 옮기는 알고리즘 구현하고 동적 시작화하기

def hanoiWith3Pegs(n, start, end, temp = 0):
    if n == 1:
        print(f"1번 디스크를 {start}에서 {end}로 이동")
        return
    hanoiWith3Pegs(n - 1, start, temp, end)
    print(f"{n}번 디스크를 {start}에서 {end}로 이동")
    hanoiWith3Pegs(n - 1, temp, end, start)

    
hanoiWith3Pegs(int(input("디스크 개수 입력: ")), 1, 3, 2)
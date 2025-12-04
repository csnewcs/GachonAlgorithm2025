# SQLite 데이터베이스 설정 가이드

## 개요
이 프로젝트는 사용자 계정 정보를 SQLite 데이터베이스에 저장합니다.

## 데이터베이스 초기화

### 1. 셸 스크립트 사용 (권장)

```bash
cd backend
./init_db.sh
```

이 스크립트는:
- `users.db` 파일 생성
- `users` 테이블 생성 (id, username 컬럼)
- 기존 데이터베이스 자동 백업

### 2. Python으로 초기화

```bash
cd backend
python3 -c "from main import init_db; init_db()"
```

### 3. 직접 실행

앱을 시작하면 자동으로 데이터베이스가 초기화됩니다:

```bash
python3 main.py
```

## 데이터베이스 구조

### users 테이블

```
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- `id`: 사용자 고유 ID (자동 증가)
- `username`: 사용자명 (중복 불가)
- `created_at`: 가입 시간

## API 엔드포인트

### 회원가입

```
POST /signup
Content-Type: application/json

{
  "username": "사용자명"
}
```

**성공 응답 (201):**
```json
{
  "message": "사용자명님 회원가입이 완료되었습니다"
}
```

**실패 응답:**
- 400: 아이디가 비어있거나 2글자 미만
- 409: 이미 존재하는 아이디
- 500: 서버 오류

### 로그인

```
POST /login
Content-Type: application/json

{
  "username": "사용자명"
}
```

**성공 응답 (200):**
```json
{
  "id": 1,
  "username": "사용자명"
}
```

**실패 응답:**
- 400: 아이디가 비어있음
- 401: 가입하지 않은 아이디
- 500: 서버 오류

## 트러블슈팅

### 데이터베이스 파일 삭제하고 싶을 때

```bash
rm backend/users.db
./backend/init_db.sh
```

### 기존 데이터는 유지하면서 테이블만 재생성

백업 파일을 확인하고 필요한 경우 복구:
```bash
ls -la backend/users.db.backup*
cp backend/users.db.backup.YYYYMMDD_HHMMSS backend/users.db
```

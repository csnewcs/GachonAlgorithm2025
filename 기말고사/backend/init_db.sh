#!/bin/bash

# SQLite 데이터베이스 초기화 스크립트
# 이 스크립트는 users.db 파일을 생성하고 users 테이블을 초기화합니다.

DB_FILE="users.db"

echo "데이터베이스 초기화를 시작합니다..."

# 기존 데이터베이스 파일 백업
if [ -f "$DB_FILE" ]; then
    BACKUP_FILE="${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$DB_FILE" "$BACKUP_FILE"
    echo "기존 데이터베이스를 백업했습니다: $BACKUP_FILE"
    rm "$DB_FILE"
fi

# SQLite에서 데이터베이스 및 테이블 생성
sqlite3 "$DB_FILE" <<'EOF'
create table users (
    id int primary key,
    username text unique not null
);

-- 테이블 생성 확인
.tables

-- 스키마 확인
.schema USERS
EOF

if [ $? -eq 0 ]; then
    echo "✓ 데이터베이스 초기화 완료!"
    echo "✓ 파일: $DB_FILE"
    echo "✓ 테이블: users (id, username)"
else
    echo "✗ 데이터베이스 초기화 실패!"
    exit 1
fi

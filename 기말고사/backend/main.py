from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import re
import time
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import shutil

# .env 파일 로드
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# SQLite 데이터베이스 경로
DATABASE = 'users.db'
UPLOAD_DIR = Path('uploads')
EXTRACT_DIR = Path('extracted')

# 지원되는 확장자
ALLOWED_EXT = {'.pdf'}

try:
    import PyPDF2
    _HAS_PYPDF2 = True
except Exception:
    _HAS_PYPDF2 = False

def get_db():
    """데이터베이스 연결"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """데이터베이스 초기화"""
    if not os.path.exists(DATABASE):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        db.close()

# 앱 시작 시 데이터베이스 초기화
init_db()

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    """파일 업로드 처리"""
    if request.method == 'OPTIONS':
        return '', 200
    
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    
    # 간단한 파일 타입 검증
    filename = secure_filename(file.filename)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return {'error': '지원하지 않는 파일 형식입니다. PDF만 업로드 가능'}, 400

    # 디렉터리 생성
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    # 저장 이름 충돌 방지: 타임스탬프 추가
    ts = int(time.time() * 1000)
    stored_name = f"{ts}_{filename}"
    stored_path = UPLOAD_DIR / stored_name
    file.save(str(stored_path))

    return {'message': f'File saved', 'filename': stored_name, 'path': str(stored_path)}, 201

@app.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    """회원가입"""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    if not data or not data.get('username'):
        return {'error': '아이디를 입력하세요'}, 400
    
    username = data.get('username').strip()
    
    if len(username) < 2:
        return {'error': '아이디는 2글자 이상이어야 합니다'}, 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
        db.commit()
        db.close()
        return {'message': f'{username}님 회원가입이 완료되었습니다'}, 201
    except sqlite3.IntegrityError:
        return {'error': '이미 존재하는 아이디입니다'}, 409
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """로그인"""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    if not data or not data.get('username'):
        return {'error': '아이디를 입력하세요'}, 400
    
    username = data.get('username').strip()
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        db.close()
        
        if user:
            return {'id': user['id'], 'username': user['username']}, 200
        else:
            return {'error': '가입하지 않은 아이디입니다'}, 401
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/file', methods=['POST', 'OPTIONS'])
def upload_and_extract():
    """1. 업로드된 파일을 임시 저장
       2. 파일에서 텍스트 추출
       3. 추출된 텍스트를 임시파일로 저장 후(원하면) 원본 삭제
    """
    if request.method == 'OPTIONS':
        return '', 200

    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400

    filename = secure_filename(file.filename)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return {'error': '지원하지 않는 파일 형식입니다. PDF만 업로드 가능'}, 400

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # 사용자 아이디 (form field 'user')
    user = request.form.get('user') or 'anonymous'
    # 사용자별 추출 폴더
    user_extract_dir = EXTRACT_DIR / str(user)
    user_extract_dir.mkdir(parents=True, exist_ok=True)

    ts = int(time.time() * 1000)
    stored_name = f"{ts}_{filename}"
    stored_path = UPLOAD_DIR / stored_name
    file.save(str(stored_path))

    extracted_text = ''
    if _HAS_PYPDF2:
        try:
            reader = PyPDF2.PdfReader(str(stored_path))
            pages_text = []
            for p in reader.pages:
                try:
                    pages_text.append(p.extract_text() or '')
                except Exception:
                    pages_text.append('')
            extracted_text = '\n'.join(pages_text)
        except Exception as e:
            return {'error': 'PDF 텍스트 추출 실패: ' + str(e)}, 500
    else:
        extracted_text = ''

    # 추출된 텍스트 저장: 사용자 폴더 아래에 저장
    txt_name = stored_name + '.txt'
    txt_path = user_extract_dir / txt_name
    try:
        with open(txt_path, 'w', encoding='utf-8') as fw:
            fw.write(extracted_text)
    except Exception as e:
        return {'error': '텍스트 저장 실패: ' + str(e)}, 500

    # 원본 PDF 삭제 (요청에 따라 서버에 보관하지 않음)
    try:
        if stored_path.exists():
            stored_path.unlink()
    except Exception:
        pass

    return {'message': '파일 업로드 및 텍스트 추출 완료', 'pdf': stored_name, 'text_file': str(txt_path.relative_to(EXTRACT_DIR))}, 201

@app.route('/combine_check', methods=['GET','POST','OPTIONS'])
def start_combine_check():
    """간단한 통합 검사 프로토타입 구현

    - 추출된 텍스트(`extracted/`)에서 단어 빈도 계산
    - 상위 키워드 제공 (stopwords 필터링 간단히 적용)
    - 파일별 기본 메타(이름, 크기)와 통계 반환
    """
    # 모듈 연동: mode.py, crolling.py, LCS.py, ngram.py 사용
    try:
        from backend import mode as mode_mod
    except Exception:
        try:
            import mode as mode_mod
        except Exception:
            mode_mod = None
    try:
        from backend import crolling as crolling_mod
    except Exception:
        try:
            import crolling as crolling_mod
        except Exception:
            crolling_mod = None
    try:
        from backend import LCS as LCS_mod
    except Exception:
        try:
            import LCS as LCS_mod
        except Exception:
            LCS_mod = None

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Handle preflight quickly
    if request.method == 'OPTIONS':
        return '', 200

    # Accept payload with { user: <userId>, files: [<server_filenames>] }
    payload = {}
    try:
        payload = request.get_json() or {}
    except Exception:
        payload = {}

    user = payload.get('user')
    requested_files = payload.get('files') or []

    # Optionally save mapping for audit
    map_file = Path('user_file_map.json')
    try:
        if user and requested_files:
            try:
                if map_file.exists():
                    existing = json.loads(map_file.read_text(encoding='utf-8'))
                else:
                    existing = {}
            except Exception:
                existing = {}
            existing[str(user)] = requested_files
            try:
                map_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
            except Exception:
                pass
    except Exception:
        pass

    # Find requested text files. Prefer user directory if provided.
    text_files = []
    user_dir = None
    if user:
        user_dir = EXTRACT_DIR / str(user)
        if user_dir.exists():
            # if specific files given, look for them in this dir
            if requested_files:
                for req in requested_files:
                    p = user_dir / (req + '.txt')
                    if p.exists():
                        text_files.append(p)
            else:
                text_files = sorted(user_dir.glob('*.txt'))

    # If no files found yet and requested_files were provided, search across all user subdirs
    if not text_files and requested_files:
        for req in requested_files:
            try:
                matches = list(EXTRACT_DIR.rglob(req + '.txt'))
            except Exception:
                matches = []
            for m in matches:
                if m.exists():
                    text_files.append(m)

    # Fallback: gather any extracted text
    if not text_files:
        text_files = sorted(EXTRACT_DIR.glob('*/*.txt'))

    if not text_files:
        return {'message': '추출된 텍스트 파일이 없습니다. 먼저 파일을 업로드하고 텍스트를 추출하세요.'}, 200

    # 파일별 텍스트 읽기
    file_texts = []
    for tf in text_files:
        try:
            txt = tf.read_text(encoding='utf-8')
        except Exception:
            txt = ''
        file_texts.append({'name': tf.name, 'text': txt})

    # 3) 비교 (LCS + n-gram) — 파일별 개별 검사
    comparisons = []
    # try to import ngram module
    try:
        from backend import ngram as ngram_mod
    except Exception:
        try:
            import ngram as ngram_mod
        except Exception:
            ngram_mod = None

    # 파일 개별로 검사 수행
    # 클라이언트가 전역 키워드를 보냈는지 확인
    client_keywords = None
    try:
        raw_client_kw = payload.get('keywords') if isinstance(payload, dict) else None
        if raw_client_kw:
            if isinstance(raw_client_kw, str):
                client_keywords = [k.strip() for k in re.split(r'[,;]+', raw_client_kw) if k.strip()]
            elif isinstance(raw_client_kw, list):
                client_keywords = [str(k).strip() for k in raw_client_kw if str(k).strip()]
    except Exception as e:
        client_keywords = None
        print(f"[DEBUG] client_keywords parsing error: {e}")

    print(f"[DEBUG] client_keywords: {client_keywords}")
    print(f"[DEBUG] file_texts count: {len(file_texts)}")

    for f in file_texts:
        file_entry = {'file': f['name'], 'comparisons': []}

        # 1) 각 파일별로 키워드 선정: 클라이언트 제공 키워드 우선, 없으면 mode에서 추출
        keywords = []
        if client_keywords and len(client_keywords) > 0:
            keywords = client_keywords
            print(f"[DEBUG] Using client keywords: {keywords}")
        else:
            if mode_mod and f['text']:
                try:
                    keywords = mode_mod.select_keywords([f['text']], top_n=5)
                    print(f"[DEBUG] Extracted keywords via mode: {keywords}")
                except Exception as e:
                    keywords = []
                    print(f"[DEBUG] mode.select_keywords error: {e}")
            else:
                print(f"[DEBUG] mode_mod or file text not available")
        
        # 2) 크롤링(위키) — 참조 텍스트 수집
        references = {}
        if crolling_mod and keywords:
            try:
                print(f"[DEBUG] Fetching references for keywords: {keywords}")
                references = crolling_mod.fetch_references(keywords, max_per=2)
                print(f"[DEBUG] References fetched: {len(references)} keywords, total refs: {sum(len(v) for v in references.values())}")
            except Exception as e:
                references = {}
                print(f"[DEBUG] crolling.fetch_references error: {e}")
        
        # 3) 비교 수행
        print(f"[DEBUG] Processing file {f['name']}, references: {len(references)} keywords")
        comp_count = 0
        for kw, refs in references.items():
            print(f"[DEBUG] Keyword '{kw}': {len(refs)} references")
            for ref in refs:
                ref_text = ref.get('text', '') or ''
                score = 0.0
                positions = None
                if LCS_mod and f['text'] and ref_text:
                    try:
                        # 비교 대상 텍스트가 길면 앞부분으로 제한하여 성능 확보
                        a = f['text'][:5000]
                        b = ref_text[:5000]
                        score = LCS_mod.similarity_score(a, b)
                        # 겹치는 부분의 위치 추적
                        positions = LCS_mod.find_lcs_positions(a, b)
                    except Exception as e:
                        score = 0.0
                        positions = None
                # n-gram 유사도도 계산
                ngram_score = None
                if ngram_mod and f['text'] and ref_text:
                    try:
                        ngram_score = ngram_mod.ngram_similarity(f['text'], ref_text, n=3)
                    except Exception as e:
                        ngram_score = None
                comp_entry = {'keyword': kw, 'ref_title': ref.get('title'), 'lcs_score': round(score, 4), 'ngram_score': (round(ngram_score,4) if ngram_score is not None else None)}
                if positions:
                    comp_entry['positions'] = positions
                file_entry['comparisons'].append(comp_entry)
                comp_count += 1
        print(f"[DEBUG] Completed {comp_count} comparisons for file {f['name']}")

        
        file_entry['keywords'] = keywords
        comparisons.append(file_entry)

    # 반환할 결과 생성
    result = {
        'file_count': len(file_texts),
        'files': [f['name'] for f in file_texts],
        'comparisons': comparisons
    }

    # 통합 검사 완료 후 해당 사용자 디렉터리 삭제 (안전하게)
    try:
        # determine user_dir: if user_dir set above use it, else infer from text_files[0]
        if user_dir is None and text_files:
            # txt path looks like extracted/<user>/<file>.txt
            try:
                p = text_files[0]
                user_dir = p.parent
            except Exception:
                user_dir = None
        if user_dir and user_dir.exists():
            try:
                shutil.rmtree(user_dir)
            except Exception:
                # best-effort: try unlink individual files
                try:
                    for tf in text_files:
                        try:
                            tf.unlink()
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception:
        pass

    return result, 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

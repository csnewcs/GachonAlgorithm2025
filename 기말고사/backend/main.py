from flask import Flask, jsonify, request
from flask_cors import CORS
import re
import time
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import database
from threading import Thread
import queue
import json

database = database.Database()
app = Flask(__name__)
CORS(app)


UPLOAD_DIR = Path('uploads')
EXTRACT_DIR = Path('extracted')
REPORT_DIR = Path('reports')
MAXIMUM_LENGTH = 10000

# 지원되는 확장자
ALLOWED_EXT = {'.pdf'}

try:
    import PyPDF2
    _HAS_PYPDF2 = True
except Exception:
    _HAS_PYPDF2 = False

def get_simillarity(text, refs):
    from LCS import find_lcs_positions
    from ngram import ngram_similarity
    simillarities = []
    for r in refs:
        print(r['title'])
        if r is None:
            continue
        lcs_result = find_lcs_positions(text, r['text'])
        ngram_sim = ngram_similarity(text, r['text'], n=3)
        simillarities.append({
            'title': r['title'],
            'lcs_length': lcs_result['lcs_length'],
            'ngram_similarity': ngram_sim
        })
        
    return simillarities


def check(user_id, filename):
    import crolling
    import checkAi

    files = database.get_user_files(user_id)
    result = []
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    for file_path in files:
        stored_path = file_path['path']
        file_name = Path(stored_path).name
        extract_path = EXTRACT_DIR / f"{file_name.split('_')[0]}.txt"
        report_file_path = REPORT_DIR / user_id / f"{file_name}_report.json"
        # 만약 이미 만들어진 리포트 있으면 스킵
        if report_file_path.exists() or not extract_path.exists():
            continue

        with open(extract_path, 'r', encoding='utf-8') as f:
            text = f.read()
            text = text[:MAXIMUM_LENGTH]  # 너무 긴 텍스트는 자르기
        
        # AI 작성 여부 체크
        ai_q = queue.Queue()
        ai_check_thread = Thread(target=checkAi.checkGPT, args=(text, ai_q))
        ai_check_thread.start()
        
        # 키워드 기반 크롤링
        keywords = database.get_keywords_for_file(stored_path)
        references = crolling.fetch_references(keywords, database)
        print(references.keys())
        # LCS, ngram 유사도 계산
        similarities = []
        for ref, search in references.items():
            similarities.extend(get_simillarity(text, search))
        

        ai_check_thread.join()
        ai_score = ai_q.get()
        ref_links = {kw: [item['link'] for item in items] for kw, items in references.items()}
        # 리포트 생성(JSON)
        content = {
            'file': file_name,
            'keywords': keywords,
            'similarities': similarities,
            'ai_generated_score': ai_score,
            'references_link': ref_links
        }

        report_file_path.parent.mkdir(parents=True, exist_ok=True)    
            
        with open(report_file_path, 'w', encoding='utf-8') as report_file:
            report_file.write(json.dumps(content, ensure_ascii=False, indent=4))
    
        # 리포트 데이터베이스에 입력
        max_sim = max([s['ngram_similarity'] for s in similarities], default=0)
        database.add_report_for_file(stored_path, max_sim, ai_score)
    

def extract_text_from_pdf(fileName):
    """PDF 파일에서 텍스트 추출"""
    if not _HAS_PYPDF2:
        raise ImportError("PyPDF2 모듈이 설치되어 있지 않습니다.")
    
    text = ""
    with open(fileName, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

@app.route('/file', methods=['POST', 'OPTIONS'])
def upload_file():
    """파일 업로드 처리"""
    if request.method == 'OPTIONS':
        return '', 200
    
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    if not request.form.get('user_id'):
        return {'error': 'User ID is required'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    
    # 간단한 파일 타입 검증
    filename = secure_filename(file.filename)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        return {'error': '지원하지 않는 파일 형식입니다. PDF만 업로드 가능'}, 400
    
    if request.form.get('keywords'):
        keywords = request.form.get('keywords').split(',')
    else:
        keywords = []

    # 디렉터리 생성
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    # 저장 이름 충돌 방지: 타임스탬프 추가
    ts = int(time.time() * 1000)
    stored_name = f"{ts}_{filename}"
    stored_path = UPLOAD_DIR / stored_name
    file.save(str(stored_path))

    # 텍스트 추출
    try:
        extracted_text = extract_text_from_pdf(stored_path)
        extract_file_path = EXTRACT_DIR / f"{ts}.txt"
        database.add_file_for_user(request.form.get('user_id'), str(stored_path), filename)
    except Exception as e:
        return {'error': f'텍스트 추출 실패: {str(e)}'}, 500
    
    # 줄바꿈 제거
    extracted_text = extracted_text.replace('\n', ' ').replace('\r', ' ')

    #공백 제거
    extracted_text = re.sub(r'\s+', ' ', extracted_text).strip()
    with open(extract_file_path, 'w', encoding='utf-8') as text_file:
        text_file.write(extracted_text)

    # 키워드 추출
    if len(keywords) == 0:
        from mode import select_keywords
        keywords = select_keywords([extracted_text], top_n=5)

    database.add_keywords_for_file(str(stored_path), keywords)

    return {'message': f'File saved', 'filename': stored_name, 'keywords': keywords}, 200

@app.route('/file/<user_id>', methods=['GET', 'OPTIONS'])
def get_files_for_user(user_id):
    if request.method == 'OPTIONS':
        return '', 200
    files = database.get_user_files(user_id)
    return {'files': files}, 200

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
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return {'error': '아이디는 영문자, 숫자, 밑줄(_)만 사용할 수 있습니다'}, 400 #injection 방지
    
    if database.is_username_exists(username):
        return {'error': '이미 존재하는 아이디입니다'}, 409
    if database.add_user(username):
        return {'message': f'{username}님 회원가입이 완료되었습니다'}, 200
    else:
        return {'error': '회원가입에 실패했습니다'}, 500

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """로그인"""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    
    if not data or not data.get('username'):
        return {'error': '아이디를 입력하세요'}, 400
    
    username = data.get('username').strip()
    
    user_id = database.get_user_id_by_username(username)
    if user_id is None:
        return {'error': '존재하지 않는 아이디입니다'}, 404
    return {'message': f'{username}님 로그인 성공', 'user_id': user_id}, 200

@app.route('/check_all', methods=['GET', 'OPTIONS'])
def check_all():
    """텍스트 유사도 및 AI 작성 여부 체크"""
    if request.method == 'OPTIONS':
        return '', 200

    data = request.args
    userid = data.get('user_id')
    files = database.get_user_files(userid)
    if not files:
        return {'error': '사용자 파일이 없습니다'}, 404
    
    thread = Thread(target=check, args=(userid, files))
    thread.start()
    return {'message': '확인을 시작하겠습니다! 잠시 후 확인해주세요!'}, 200

@app.route('/reports/<user_id>/<filename>', methods=['GET'])
def get_report(user_id, filename):
    # SQL 저장되어 있는 것만 보기
    report = database.get_report(user_id, filename)
    if not report:
        return {'error': '리포트를 찾을 수 없습니다'}, 404
    return report, 200

@app.route('/reports/<user_id>/<filename>/content', methods=['GET'])
def get_report_content(user_id, filename):
    report_path = REPORT_DIR / user_id / filename
    if not report_path.exists():
        return {'error': '리포트를 찾을 수 없습니다'}, 404
    with open(report_path, 'r', encoding='utf-8') as report_file:
        content = json.load(report_file)
    return content, 200

@app.route('/reports/<user_id>', methods=['GET'])
def list_reports(user_id):
    user_report_dir = REPORT_DIR / user_id
    if not user_report_dir.exists():
        return {'reports': []}, 200
    reports = [f.name for f in user_report_dir.iterdir() if f.is_file()]
    return {'reports': reports}, 200



if __name__ == '__main__':
    app.run(debug=True, port=5000)

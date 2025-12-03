from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)
CORS(app)

# 설정 엔드포인트
@app.route('/config', methods=['GET'])
def get_config():
    """프론트엔드에 필요한 설정 정보 반환"""
    return jsonify({
        'kakao_app_key': os.getenv('KAKAO_RESTAPI', '')
    })

# 파일 업로드 엔드포인트
@app.route('/upload', methods=['POST'])
def upload_file():
    """파일 업로드 처리"""
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    
    # 여기에 파일 처리 로직 추가
    return {'message': f'File {file.filename} uploaded successfully'}, 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)

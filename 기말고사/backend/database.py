import sqlite3
import os

# SQLite 데이터베이스 경로
DATABASE = 'data.db'

class Database:
    def __init__(self):
        """데이터베이스 연결"""
        self.db = sqlite3.connect(DATABASE, check_same_thread=False)
        self.init_db()
    
    def init_db(self):
        """데이터베이스 초기화"""
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                user_id INTEGER,
                path TEXT NOT NULL PRIMARY KEY,
                original_filename TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                path TEXT NOT NULL,
                keyword TEXT NOT NULL,
                FOREIGN KEY(path) REFERENCES files(path)
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                user_id INTEGER,
                report_path TEXT NOT NULL,
                similarity_score REAL,
                ai_generated REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                       keyword TEXT NOT NULL,
                       title TEXT NOT NULL,
                       link TEXT NOT NULL,
                       snippet TEXT,
                       FOREIGN KEY(keyword) REFERENCES keywords(keyword)
                       );
                       ''')
        self.db.commit()
    
    def get_user_id_by_username(self, username):
        """아이디로 사용자 ID 조회"""
        cursor = self.db.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        return user if user else None
    
    def get_user_files(self, user_id):
        """사용자 파일 경로 조회"""
        cursor = self.db.cursor()
        cursor.execute('SELECT path, original_filename FROM files WHERE user_id = ?', (user_id,))
        file = cursor.fetchall()
        files = [{ 'path': f[0], 'original_filename': f[1]} for f in file]
        return files if files else None
    
    def add_user(self, username):
        """새 사용자 추가"""
        cursor = self.db.cursor()
        try:
            cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def add_file_for_user(self, user_id, path, original_filename):
        """사용자 파일 경로 추가"""
        cursor = self.db.cursor()
        try:
            cursor.execute('INSERT INTO files (user_id, path, original_filename) VALUES (?, ?, ?)', (user_id, path, original_filename))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def is_username_exists(self, username):
        """아이디 존재 여부 확인"""
        cursor = self.db.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        return cursor.fetchone() is not None
    
    def add_keywords_for_file(self, path, keywords):
        """파일에 대한 키워드 추가"""
        cursor = self.db.cursor()
        try:
            for kw in keywords:
                cursor.execute('INSERT INTO keywords (path, keyword) VALUES (?, ?)', (path, kw))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_keywords_for_file(self, path):
        """파일에 대한 키워드 조회"""
        cursor = self.db.cursor()
        cursor.execute('SELECT keyword FROM keywords WHERE path = ?', (path,))
        kws = cursor.fetchall()
        return [k[0] for k in kws] if kws else []

    def add_report_for_file(self, file_path, similarity_score, ai_generated):
        """파일에 대한 리포트 추가"""
        cursor = self.db.cursor()
        try:
            # 파일 경로로 사용자 ID 조회
            cursor.execute('SELECT user_id FROM files WHERE path = ?', (file_path,))
            user = cursor.fetchone()
            if not user:
                return False
            user_id = user[0]
            report_path = f'reports/{os.path.basename(file_path)}_report.json'
            cursor.execute('''
                INSERT INTO reports (user_id, report_path, similarity_score, ai_generated)
                VALUES (?, ?, ?, ?)
            ''', (user_id, report_path, similarity_score, ai_generated))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_reports(self, user_id):
        """사용자 리포트 조회"""
        cursor = self.db.cursor()
        cursor.execute('SELECT * FROM reports WHERE user_id = ?', (user_id,))
        return cursor.fetchall()
    def get_report(self, user_id, filename):
        """특정 리포트 조회"""
        cursor = self.db.cursor()
        cursor.execute('SELECT report_path, similarity_score, ai_generated FROM reports WHERE user_id = ? AND report_path LIKE ?', (user_id, f'%{filename}'))
        report = cursor.fetchone()
        return {
            'report_path': report[0],
            'similarity_score': report[1],
            'ai_generated': report[2]
        } if report else None
    def add_search_result(self, keyword, title, link, snippet):
        """검색 결과 추가"""
        cursor = self.db.cursor()
        try:
            cursor.execute('''
                INSERT INTO search_results (keyword, title, link, snippet)
                VALUES (?, ?, ?, ?)
            ''', (keyword, title, link, snippet))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        
    def get_search_results_for_keyword(self, keyword):
        """키워드에 대한 검색 결과 조회"""
        cursor = self.db.cursor()
        cursor.execute('SELECT title, link, snippet FROM search_results WHERE keyword = ?', (keyword,))
        results = cursor.fetchall()
        return [{'title': r[0], 'link': r[1], 'snippet': r[2]} for r in results] if results else []
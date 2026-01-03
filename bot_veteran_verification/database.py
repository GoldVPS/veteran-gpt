import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = 'bot_data.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                access_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Veterans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS veterans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                first_name TEXT,
                last_name TEXT,
                branch TEXT,
                birth_date TEXT,
                discharge_date TEXT,
                status TEXT DEFAULT 'pending',
                verification_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_verifications INTEGER DEFAULT 0,
                successful INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id: int, username: str, first_name: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        self.conn.commit()
    
    def save_token(self, user_id: int, access_token: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tokens (user_id, access_token)
            VALUES (?, ?)
        ''', (user_id, access_token))
        self.conn.commit()
    
    def save_veteran(self, user_id: int, first_name: str, last_name: str, 
                    branch: str, birth_date: str, discharge_date: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO veterans 
            (user_id, first_name, last_name, branch, birth_date, discharge_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, first_name, last_name, branch, birth_date, discharge_date))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_status(self, veteran_id: int, status: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE veterans 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, veteran_id))
        self.conn.commit()
    
    def get_veteran(self, veteran_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM veterans WHERE id = ?
        ''', (veteran_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'branch': row[4],
                'birth_date': row[5],
                'discharge_date': row[6],
                'status': row[7]
            }
        return None
    
    def get_user_verifications(self, user_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM veterans 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        verifications = []
        for row in cursor.fetchall():
            verifications.append({
                'id': row[0],
                'first_name': row[2],
                'last_name': row[3],
                'branch': row[4],
                'birth_date': row[5],
                'discharge_date': row[6],
                'status': row[7],
                'created_at': row[9]
            })
        return verifications
    
    def get_stats(self) -> Dict:
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM veterans WHERE status = "approved"')
        approved = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM veterans WHERE status = "failed"')
        failed = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM veterans WHERE status = "processing"')
        processing = cursor.fetchone()[0]
        
        return {
            'total_users': total_users,
            'approved': approved,
            'failed': failed,
            'processing': processing
        }

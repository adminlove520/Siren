import sqlite3
import logging
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="missav.db"):
        self.db_path = db_path
        self._lock = Lock()
        self.init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            # Videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    title TEXT,
                    actresses TEXT,
                    tags TEXT,
                    duration INTEGER,
                    release_date TEXT,
                    cover_url TEXT,
                    preview_url TEXT,
                    detail_url TEXT,
                    pushed BOOLEAN DEFAULT 0,
                    created_time TEXT
                )
            ''')
            
            # Subscriptions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    chat_type TEXT,
                    type TEXT NOT NULL, -- ALL, ACTRESS, TAG
                    keyword TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_time TEXT
                )
            ''')
            
            # Push records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS push_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    status TEXT NOT NULL, -- SUCCESS, FAILED
                    fail_reason TEXT,
                    pushed_at TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos (id)
                )
            ''')
            conn.commit()
            logger.info("Database initialized successfully at %s", self.db_path)

    def save_video(self, video_data):
        """video_data: dict with keys matching table columns"""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT OR IGNORE INTO videos (
                        code, title, actresses, tags, duration, 
                        release_date, cover_url, preview_url, detail_url, created_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_data.get('code'),
                    video_data.get('title'),
                    video_data.get('actresses'),
                    video_data.get('tags'),
                    video_data.get('duration'),
                    video_data.get('release_date'),
                    video_data.get('cover_url'),
                    video_data.get('preview_url'),
                    video_data.get('detail_url'),
                    now
                ))
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                logger.error("Error saving video %s: %s", video_data.get('code'), e)
                return False

    def is_video_exists(self, code):
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM videos WHERE code = ?', (code,))
            return cursor.fetchone() is not None

    def get_latest_videos(self, limit=10):
        with self._lock, self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM videos ORDER BY created_time DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def subscribe(self, chat_id, chat_type, sub_type, keyword=None):
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO subscriptions (chat_id, chat_type, type, keyword, created_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, chat_type, sub_type, keyword, now))
            conn.commit()

    def unsubscribe(self, chat_id, sub_type=None, keyword=None):
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if not sub_type:
                cursor.execute('DELETE FROM subscriptions WHERE chat_id = ?', (chat_id,))
            else:
                cursor.execute('DELETE FROM subscriptions WHERE chat_id = ? AND type = ? AND keyword = ?', 
                             (chat_id, sub_type, keyword))
            conn.commit()

    def get_subscriptions(self, chat_id=None):
        with self._lock, self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if chat_id:
                cursor.execute('SELECT * FROM subscriptions WHERE chat_id = ? AND enabled = 1', (chat_id,))
            else:
                cursor.execute('SELECT * FROM subscriptions WHERE enabled = 1')
            return [dict(row) for row in cursor.fetchall()]

    def mark_pushed(self, video_id):
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE videos SET pushed = 1 WHERE id = ?', (video_id,))
            conn.commit()

import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('system_state.db')
    cursor = conn.cursor()
    
    # 1. جدول تتبع العمليات والمحاولات الثلاث
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            task_id TEXT PRIMARY KEY,
            current_agent TEXT,
            retry_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'PENDING',
            updated_at DATETIME
        )
    ''')
    
    # 2. جدول الذاكرة التسويقية والربحية المستدامة للوكلاء
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents_knowledge_base (
            rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT,
            instruction TEXT,
            ctr_impact_score REAL,
            timestamp DATETIME
        )
    ''')
    
    # 3. جدول المحتوى المنشور ومزامنة المعرفات والـ C2PA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS published_content (
            video_id TEXT PRIMARY KEY,
            platform TEXT,
            title TEXT,
            c2pa_status TEXT DEFAULT 'NOT_INJECTED',
            views_count INTEGER DEFAULT 0,
            rpm_rate REAL DEFAULT 0.0,
            publish_timestamp DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()
    print("🤖 [SQLite] Database initialized successfully with ACID compliance.")

if __name__ == "__main__":
    init_db()

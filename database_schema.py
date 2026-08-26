import sqlite3
import datetime

class DatabaseManager:
    def __init__(self, db_name="ai_trends.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """
        إنشاء وتحديث الجداول الأساسية للنظام مع دمج آليات الحماية والتعلم الجديدة
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. الجدول الأساسي لإدارة المقاطع (موجود سابقاً وتحديث الحالات)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS segments (
                    segment_id TEXT PRIMARY KEY,
                    script_text TEXT,
                    audio_path TEXT,
                    video_path TEXT,
                    status TEXT DEFAULT 'PENDING' -- PENDING, APPROVED, REJECTED, PUBLISHED
                )
            ''')

            # 2. [جديد] جدول جدار الحماية المالي لمراقبة المصاريف الشهرية واليومية
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budget_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT,
                    amount_spent REAL,
                    timestamp TEXT,
                    billing_month TEXT -- صيغة الشهور YYYY-MM لسهولة الفرز
                )
            ''')

            # 3. [جديد] جدول تعقب العدادات والمحاولات الثلاث (منع الحلقات اللانهائية)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retry_counters (
                    process_key TEXT PRIMARY KEY, -- مثال: 'video_long_id_123' أو 'video_short_id_123'
                    retry_count INTEGER DEFAULT 0,
                    last_attempt TEXT
                )
            ''')

            # 4. [جديد] جدول القاعدة المعرفية لتعلم ووعي المدير (التحكم بالمكونات والأرباح)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manager_knowledge_base (
                    trend_topic TEXT PRIMARY KEY,
                    expected_rpm REAL,
                    actual_profit REAL,
                    video_duration_type TEXT, -- LONG أو SHORT
                    components_used TEXT,     -- قائمة المكونات المدمجة مثل: 'avatar,music,tts'
                    performance_score REAL,
                    last_updated TEXT
                )
            ''')
            
            conn.commit()

    # =========================================================================
    # الدوال البرمجية الخاصة بجدار الحماية المالي (FinOps) والتحكم بالصرف
    # =========================================================================
    
    def log_api_transaction(self, agent_name, amount):
        """تسجيل تفصيلي لكل سنت يتم صرفه بواسطة الوكلاء"""
        now = datetime.datetime.now()
        billing_month = now.strftime("%Y-%m")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO budget_logs (agent_name, amount_spent, timestamp, billing_month)
                VALUES (?, ?, ?, ?)
            ''', (agent_name, amount, now.isoformat(), billing_month))
            conn.commit()

    def get_total_spent_for_month(self, current_month):
        """حساب إجمالي المجموع المصروف للشهر الحالي للتأكد من مرونة الـ 20 يورو"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(amount_spent) FROM budget_logs WHERE billing_month = ?
            ''', (current_month,))
            result = cursor.fetchone()[0]
            return result if result is not None else 0.0

    # =========================================================================
    # الدوال البرمجية الخاصة ببروتوكول المحاولات الثلاث (3-Retry Cap) والتصفير
    # =========================================================================
    
    def increment_retry_counter(self, process_key):
        """رفع عداد المحاولات بمقدار 1 عند حدوث أي فشل عملي"""
        now = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO retry_counters (process_key, retry_count, last_attempt)
                VALUES (?, 1, ?)
                ON CONFLICT(process_key) DO UPDATE SET 
                    retry_count = retry_count + 1,
                    last_attempt = ?
            ''', (process_key, now, now))
            conn.commit()

    def get_retry_count(self, process_key):
        """قراءة عدد المحاولات الحالي لمنع الحلقات اللانهائية عند رقم 3"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT retry_count FROM retry_counters WHERE process_key = ?', (process_key,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def reset_video_counters(self, process_key):
        """تصفير العداد تماماً (0) فور نجاح النشر لتبدأ الدورة القادمة بصفحة جديدة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM retry_counters WHERE process_key = ?', (process_key,))
            conn.commit()
            print(f"🔄 [Counter Reset] تم تصفير وإغلاق سجلات العملية: {process_key}")

    # =========================================================================
    # الدوال البرمجية الخاصة بذكاء وتعلّم المدير (Manager Machine Learning)
    # =========================================================================
    
    def update_manager_knowledge(self, topic, expected_rpm, actual_profit, duration_type, components):
        """حفظ وتحديث خبرة المدير وتجاربه التجارية ليتعلم منها في الفيديوهات القادمة"""
        now = datetime.datetime.now().isoformat()
        score = (actual_profit / (expected_rpm + 0.01)) * 100 # تقييم ذكي لنجاح توقعاته
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO manager_knowledge_base 
                (trend_topic, expected_rpm, actual_profit, video_duration_type, components_used, performance_score, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trend_topic) DO UPDATE SET
                    actual_profit = ?,
                    performance_score = ?,
                    last_updated = ?
            ''', (topic, expected_rpm, actual_profit, duration_type, components, score, now, actual_profit, score, now))
            conn.commit()

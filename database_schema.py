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
        إنشاء وتحديث الجداول الأساسية للنظام مع ربط أرشفة الفحوصات والامتثال 
        مباشرة بـ video_id (segment_id) لكل فيديو.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. الجدول الأساسي لإدارة المقاطع والفيديو
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS segments (
                    segment_id TEXT PRIMARY KEY,          -- هذا هو الـ video_id المرجعي
                    script_text TEXT,
                    audio_path TEXT,
                    video_path TEXT,
                    status TEXT DEFAULT 'PENDING',        -- الحالة العامة للفيديو
                    fact_check_status TEXT DEFAULT 'PENDING' -- حالة موافقة المدقق المعلوماتي
                )
            ''')

            # 2. أرشفة سجل الامتثال والمسؤولية القانونية مربوطاً بـ video_id حتمياً
            # يحفظ إثبات نجاح فحص كافة الوكلاء والمدقق لكل فيديو قبل مسح الميديا والنصوص
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_signatures_audit (
                    video_id TEXT PRIMARY KEY,         -- مربوط مباشرة بـ segment_id للفيديو المؤرشف
                    video_hash TEXT,                   -- البصمة الرقمية المشفرة SHA-256 للفيديو
                    publish_date TEXT,                 -- تاريخ النشر الناجح
                    platform_url TEXT,                 -- رابط الفيديو على المنصات
                    is_sharia_approved INTEGER DEFAULT 0, -- إثبات موافقة الوكيل الشرعي
                    is_eu_law_approved INTEGER DEFAULT 0,  -- إثبات موافقة وكيل القانون الأوروبي
                    is_fact_checked INTEGER DEFAULT 0     -- إثبات موافقة المدقق المعلوماتي ومصداقية المحتوى
                )
            ''')

            # 3. جدول جدار الحماية المالي لمراقبة المصاريف الشهرية واليومية (الـ 20 يورو المرنة)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budget_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT,
                    amount_spent REAL,
                    timestamp TEXT,
                    billing_month TEXT 
                )
            ''')

            # 4. جدول تعقب العدادات والمحاولات الثلاث (منع الحلقات اللانهائية وتصفيرها)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retry_counters (
                    process_key TEXT PRIMARY KEY, 
                    retry_count INTEGER DEFAULT 0,
                    last_attempt TEXT
                )
            ''')

            # 5. جدول القاعدة المعرفية لتعلم المدير (التحكم بالمكونات والأرباح)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manager_knowledge_base (
                    trend_topic TEXT PRIMARY KEY,
                    expected_rpm REAL,
                    actual_profit REAL,
                    video_duration_type TEXT, 
                    components_used TEXT,     
                    performance_score REAL,
                    last_updated TEXT
                )
            ''')
            
            conn.commit()

    # =========================================================================
    # دالة تسجيل إيصال الامتثال القانوني المؤرشف بالـ video_id
    # =========================================================================
    def register_compliance_receipt(self, video_id, video_hash, platform_url, sharia, eu_law, fact_check):
        """أرشفة حالة الفحوصات لكل فيديو مربوطاً بالـ video_id لحمايتك قانونياً وتوثيق النجاح"""
        now = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO compliance_signatures_audit 
                (video_id, video_hash, publish_date, platform_url, is_sharia_approved, is_eu_law_approved, is_fact_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (video_id, video_hash, platform_url, 1 if sharia else 0, 1 if eu_law else 0, 1 if fact_check else 0))
            conn.commit()
            print(f"🔒 [Audit Archived] تم حفظ أرشفة فحوصات الفيديو بنجاح للـ ID: {video_id}")

    # =========================================================================
    # الدوال البرمجية الخاصة بجدار الحماية المالي (FinOps)
    # =========================================================================
    def log_api_transaction(self, agent_name, amount):
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(amount_spent) FROM budget_logs WHERE billing_month = ?', (current_month,))
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0.0

    # =========================================================================
    # الدوال البرمجية الخاصة ببروتوكول المحاولات الثلاث والتصفير
    # =========================================================================
    def increment_retry_counter(self, process_key):
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT retry_count FROM retry_counters WHERE process_key = ?', (process_key,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def reset_video_counters(self, process_key):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM retry_counters WHERE process_key = ?', (process_key,))
            conn.commit()
            print(f"🔄 [Counter Reset] تم تصفير وإغلاق سجلات العملية: {process_key}")

    # =========================================================================
    # الدوال البرمجية الخاصة بذكاء وتعلّم المدير
    # =========================================================================
    def update_manager_knowledge(self, topic, expected_rpm, actual_profit, duration_type, components):
        now = datetime.datetime.now().isoformat()
        score = (actual_profit / (expected_rpm + 0.01)) * 100
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

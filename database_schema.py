import sqlite3
import datetime
import json

class DatabaseManager:
    """
    إدارة قاعدة البيانات المركزية لـ Ai_Trends (v2 - المترابطة بالكامل).
    تخدم هؤلاء الوكلاء الخمسة، بوابات الرقابة، جدار الميزانية، وتوثيق C2PA.
    """
    def __init__(self, db_name="ai_trends.db"):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """إنشاء الجداول لتدعم دورة حياة الفيديو كاملة وحالة الامتثال والتعلم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. الجدول الرئيسي لإدارة مقاطع وفيديوهات خط الإنتاج (Pipeline)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS segments (
                segment_id TEXT PRIMARY KEY,
                trend_topic TEXT,
                script_text TEXT,
                visual_keywords TEXT,
                audio_path TEXT,
                video_path TEXT,
                c2pa_manifest_path TEXT,
                status TEXT DEFAULT 'DRAFT',                -- DRAFT, SCRIPT_GENERATED, APPROVED, PRODUCED, TELEGRAM_HOLD, PUBLISHED, REJECTED
                sharia_status TEXT DEFAULT 'PENDING',        -- PENDING, APPROVED, REJECTED
                sharia_feedback TEXT,                         -- لتخزين سبب الرفض والتعديل الموضعي
                eu_law_status TEXT DEFAULT 'PENDING',        -- PENDING, APPROVED, REJECTED
                eu_law_feedback TEXT,                        -- لتخزين ملاحظات القانون الأوروبي
                fact_check_status TEXT DEFAULT 'PENDING',     -- PENDING, APPROVED, REJECTED
                telegram_sent_at TEXT,                       -- لتتبع نافذة الـ 6 ساعات
                is_human_approved INTEGER DEFAULT 0,          -- 1 = موافقة، -1 = رفض بشري، 0 = انتظار
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 2. جدول أرشفة وتدقيق الامتثال (Compliance & Legal Sign-off) بعد النشر
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_signatures_audit (
                video_id TEXT PRIMARY KEY,
                video_hash TEXT,
                publish_date TEXT,
                platform_url TEXT,
                is_sharia_approved INTEGER DEFAULT 0,
                is_eu_law_approved INTEGER DEFAULT 0,
                is_fact_checked INTEGER DEFAULT 0,
                c2pa_verified INTEGER DEFAULT 0,
                FOREIGN KEY(video_id) REFERENCES segments(segment_id)
            )
            ''')

            # 3. الجدار المالي لربط استهلاك الميزانية بكل فيديو ووكيل بدقة
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                segment_id TEXT,
                agent_name TEXT,                             -- اسم الوكيل المستهلك
                amount_spent REAL,                           -- التكلفة بالـ Tokens أو الدولار
                billing_month TEXT,                          -- مثلاً: "2026-08"
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(segment_id) REFERENCES segments(segment_id)
            )
            ''')

            # 4. ذاكرة تعلم وكيل الكتابة (Granular Patching & Learning Repository)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_learning_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                segment_id TEXT,
                agent_type TEXT,                             -- sharia, eu_law, fact_check
                failed_script TEXT,                          -- النص المرفوض
                rejection_reason TEXT,                        -- سبب الرفض
                corrected_script TEXT,                       -- النص المصحح الجديد
                learned_rule TEXT,                           -- القاعدة المستخلصة للتعلم المستقبلي
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(segment_id) REFERENCES segments(segment_id)
            )
            ''')
            
            conn.commit()

    # ==================== دوال التحكم والربط (Pipeline API) ====================

    def create_segment_draft(self, segment_id, trend_topic, script_text, visual_keywords):
        """يستدعيها وكيل الإدارة ووكيل الكتابة لتسجيل مسودة الفيديو"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO segments (segment_id, trend_topic, script_text, visual_keywords, status)
            VALUES (?, ?, ?, ?, 'SCRIPT_GENERATED')
            ''', (segment_id, trend_topic, script_text, visual_keywords))
            conn.commit()

    def update_compliance_status(self, segment_id, agent_type, status, feedback=None):
        """تحديث بوابة الرقابة (الشرعية أو القانونية) وتفعيل بروتوكول التعديل"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if agent_type == 'sharia':
                cursor.execute('''
                UPDATE segments 
                SET sharia_status = ?, sharia_feedback = ? 
                WHERE segment_id = ?
                ''', (status, feedback, segment_id))
            elif agent_type == 'eu_law':
                cursor.execute('''
                UPDATE segments 
                SET eu_law_status = ?, eu_law_feedback = ? 
                WHERE segment_id = ?
                ''', (status, feedback, segment_id))
            elif agent_type == 'fact_check':
                cursor.execute('''
                UPDATE segments 
                SET fact_check_status = ?, sharia_feedback = ? 
                WHERE segment_id = ?
                ''', (status, feedback, segment_id))

            # التحقق التلقائي: إذا تمت الموافقة من جميع الجهات الرقابية، تتغير الحالة الكلية لـ APPROVED
            cursor.execute('''
            UPDATE segments
            SET status = 'APPROVED'
            WHERE segment_id = ? 
              AND sharia_status = 'APPROVED' 
              AND eu_law_status = 'APPROVED' 
              AND fact_check_status = 'APPROVED'
            ''', (segment_id,))
            
            # إذا رفض أحد الوكلاء، يتم تحويل الحالة الكلية إلى REJECTED لبدء التعديل الموضعي
            if status == 'REJECTED':
                cursor.execute("UPDATE segments SET status = 'REJECTED' WHERE segment_id = ?", (segment_id,))
                
            conn.commit()

    def log_learning(self, segment_id, agent_type, failed_script, rejection_reason, corrected_script, learned_rule):
        """تسجيل الأخطاء لبروتوكول التعلم المستمر الخاص بوكيل الكتابة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO agent_learning_memory (segment_id, agent_type, failed_script, rejection_reason, corrected_script, learned_rule)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (segment_id, agent_type, failed_script, rejection_reason, corrected_script, learned_rule))
            conn.commit()

    def log_budget(self, segment_id, agent_name, amount_spent):
        """تسجيل فوري للميزانية لمنع تجاوز الجدار المالي المذكور في budget_telegram_interface"""
        current_month = datetime.datetime.now().strftime("%Y-%m")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO budget_logs (segment_id, agent_name, amount_spent, billing_month)
            VALUES (?, ?, ?, ?)
            ''', (segment_id, agent_name, amount_spent, current_month))
            conn.commit()

    def set_telegram_hold(self, segment_id):
        """تحديث الحالة بعد رندرة الفيديو وبدء نافذة الـ 6 ساعات لبوت التليجرام"""
        now_str = datetime.datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE segments 
            SET status = 'TELEGRAM_HOLD', telegram_sent_at = ? 
            WHERE segment_id = ?
            ''', (now_str, segment_id))
            conn.commit()

    def get_pending_telegram_approvals(self):
        """جلب المقاطع التي تنتظر مراجعة المطور في بوت التليجرام"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM segments WHERE status = 'TELEGRAM_HOLD' AND is_human_approved = 0")
            return [dict(row) for row in cursor.fetchall()]

    def finalize_publishing(self, segment_id, video_hash, platform_url):
        """تسجيل المقطع كـ PUBLISHED ونقل بيانات التوقيع إلى جدول الـ Audit النهائي للتاريخ والتوثيق"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. تحديث الجدول الرئيسي
            cursor.execute("UPDATE segments SET status = 'PUBLISHED' WHERE segment_id = ?", (segment_id,))
            
            # 2. نقل البيانات لجدول تدقيق الامتثال الشامل
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
            INSERT OR REPLACE INTO compliance_signatures_audit 
            (video_id, video_hash, publish_date, platform_url, is_sharia_approved, is_eu_law_approved, is_fact_checked, c2pa_verified)
            SELECT segment_id, ?, ?, ?, 
                   (CASE WHEN sharia_status='APPROVED' THEN 1 ELSE 0 END),
                   (CASE WHEN eu_law_status='APPROVED' THEN 1 ELSE 0 END),
                   (CASE WHEN fact_check_status='APPROVED' THEN 1 ELSE 0 END),
                   (CASE WHEN c2pa_manifest_path IS NOT NULL THEN 1 ELSE 0 END)
            FROM segments WHERE segment_id = ?
            ''', (video_hash, now_str, platform_url, segment_id))
            conn.commit()

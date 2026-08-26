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

            # 1. الجدول الرئيسي لإدارة مقاطع وفيديوهات خط الإنتاج (Pipeline) - الكود الأصلي القديم بالكامل
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

            # 2. جدول أرشفة وتدقيق الامتثال (Compliance & Legal Sign-off) بعد النشر - الكود الأصلي القديم بالكامل
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

            # 3. الجدار المالي لربط استهلاك الميزانية بكل فيديو ووكيل بدقة - الكود الأصلي القديم بالكامل
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

            # 4. ذاكرة تعلم وكيل الكتابة (Granular Patching & Learning Repository) - الكود الأصلي القديم بالكامل
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
            
            # 5. [إضافة جديدة حصراً]: جدول إدارة نافذة الساعتين للتفاعل لوكيل التفاعل (Engagement Windows)
            # يتم تفعيله تلقائياً فور النشر، ويعتمد عليه وكيل التفاعل للاستيقاظ المؤقت عبر الـ Webhook
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_engagement_windows (
                video_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                published_at TEXT NOT NULL,
                window_expiry TEXT NOT NULL,                 -- وقت النشر + ساعتين بالضبط لغلق الـ Webhook تلقائياً
                is_active INTEGER DEFAULT 1,                 -- 1 = النافذة مفتوحة للتفاعل، 0 = مغلقة ومقفلة لحظر التكاليف
                total_comments_replied INTEGER DEFAULT 0,     -- عداد الردود الذكية لـ engagement_agent
                FOREIGN KEY(video_id) REFERENCES segments(segment_id)
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

    # ────── دوال تتبع واستخدام نافذة الساعتين المضافة حديثاً ──────

    def activate_engagement_window(self, segment_id, platform):
        """[دالة جديدة]: يتم استدعاؤها فور النشر لفتح نافذة الساعتين التفاعلية لوكيل التفاعل (engagement_agent)"""
        now = datetime.datetime.now()
        expiry = now + datetime.timedelta(hours=2)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO video_engagement_windows (video_id, platform, published_at, window_expiry, is_active)
            VALUES (?, ?, ?, ?, 1)
            ''', (segment_id, platform, now.isoformat(), expiry.isoformat()))
            conn.commit()

    def verify_and_use_engagement_window(self, segment_id):

import sqlite3
import hashlib
from datetime import datetime

# اسم قاعدة البيانات المركزية للنظام
DATABASE_NAME = "ai_trends_core.db"

def get_db_connection():
    """إنشاء اتصال آمن مع قاعدة البيانات وتفعيل دعم المفاتيح الأجنبية"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    # تفعيل القيود التكاملية للمفاتيح الأجنبية في SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database():
    """
    إنشاء وتجهيز البنية الهيكلية الكاملة لقاعدة البيانات.
    يقوم هذا التابع ببناء الجداول الأربعة الأساسية للنظام لضمان تحقيق النقاط الخمس:
    1. جدول البصمات النصية لمنع التكرار والحظر.
    2. جدول طابور الويب هوك لمنع سقوط الإشارات وأخطاء 5xx.
    3. جدول شهادات الفحص وتوثيق الفحوصات الروباعية.
    4. جدول الذاكرة الجلساتية المؤقتة للكاتب.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    print("[*] جاري تهيئة البنية الهيكلية المحدثة لقاعدة البيانات...")

    # 1. جدول البصمات الرقمية للنصوص المقبولة والمنشورة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS script_hashes (
        hash_id INTEGER PRIMARY KEY AUTOINCREMENT,
        script_hash TEXT NOT NULL UNIQUE,
        video_title TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    print("[+] تم إنشاء جدول بصمات النصوص (SHA-256) بنجاح.")

    # 2. جدول طابور استقبال الإشارات (Webhook Queue) لمنع قفل Nginx
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webhook_queue (
        queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,          -- يوتيوب، تيك توك، إلخ
        comment_id TEXT NOT NULL UNIQUE, -- معرف التعليق الفريد من المنصة
        raw_data TEXT NOT NULL,          -- البيانات الخام المستلمة
        status TEXT NOT NULL,            -- Pending, Processed, Expired
        received_at TEXT NOT NULL,       -- وقت استلام الإشارة الفوري
        processed_at TEXT                -- وقت معالجة الإشارة بواسطة الوكيل
    );
    """)
    print("[+] تم إنشاء جدول طابور الويب هوك (Asynchronous Queue) بنجاح.")

    # 3. جدول شهادات الفحص الموسع (Verification Certificates) للرقابة الرباعية
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_certificates (
        certificate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL UNIQUE,
        video_title TEXT NOT NULL,
        script_hash TEXT NOT NULL,
        islamic_compliance_passed INTEGER NOT NULL, -- 1 = ناجح، 0 = راسب
        eu_law_passed INTEGER NOT NULL,             -- 1 = ناجح، 0 = راسب
        realism_protocol_passed INTEGER NOT NULL,   -- 1 = ناجح، 0 = راسب
        c2pa_validated INTEGER NOT NULL,            -- 1 = ناجح، 0 = راسب
        overall_score REAL NOT NULL,                -- تقييم الجودة الإجمالي
        published_at TEXT NOT NULL,                 -- التاريخ والتوقيع الزمني الكامل
        FOREIGN KEY (script_hash) REFERENCES script_hashes(script_hash)
    );
    """)
    print("[+] تم إنشاء جدول شهادات الفحص والتوثيق الرباعي بنجاح.")

    # 4. جدول الذاكرة الجلساتية المؤقتة لوكيل الكتابة (Session Memory Cache)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS writer_session_cache (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_number INTEGER NOT NULL, -- من 1 إلى 3
        rejected_text TEXT NOT NULL,
        rejection_reason TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    print("[+] تم إنشاء جدول الذاكرة المؤقتة للـ 3 محاولات بنجاح.")

    conn.commit()
    conn.close()
    print("[🎉] اكتمال بناء النظام وتأسيس قواعد البيانات بنجاح.")

# =====================================================================
# الدوال التشغيلية والأدوات المساعدة (مدمجة بالكامل لضمان عدم النقصان)
# =====================================================================

def generate_script_hash(script_text):
    """توليد البصمة الرقمية الفريدة للنص باستخدام SHA-256"""
    return hashlib.sha256(script_text.strip().encode('utf-8')).hexdigest()

def is_script_duplicated(script_text):
    """
    النقطة 1: فحص البصمة لمنع التكرار قبل البدء بالتوليد.
    يعيد True إذا كان النص قد تم إنتاجه سابقاً، و False إذا كان جديداً.
    """
    script_hash = generate_script_hash(script_text)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM script_hashes WHERE script_hash = ?", (script_hash,))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def register_published_video(video_title, script_text):
    """تسجيل النص الناجح في جدول البصمات لضمان عدم تكراره مستقبلاً"""
    script_hash = generate_script_hash(script_text)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO script_hashes (script_hash, video_title, created_at) VALUES (?, ?, ?)",
            (script_hash, video_title, datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        print("[!] تحذير: هذه البصمة مسجلة بالفعل في النظام.")
    finally:
        conn.close()

def push_to_webhook_queue(platform, comment_id, raw_data):
    """
    النقطة 3: استقبال الإشارات الفوري وضخها في الطابور الخلفي.
    تستدعيها دوال الويب هوك لترد مباشرة بـ 200 OK للمنصات.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO webhook_queue (platform, comment_id, raw_data, status, received_at) VALUES (?, ?, ?, 'Pending', ?)",
            (platform, comment_id, raw_data, datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass # الإشارة مسجلة مسبقاً، يتم تجاهلها بصمت لمنع التكرار
    finally:
        conn.close()

def log_writer_attempt(attempt_number, text, reason):
    """تسجيل محاولات الكاتب الفاشلة مؤقتاً لتفادي تكرار الأخطاء في نفس الجلسة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO writer_session_cache (attempt_number, rejected_text, rejection_reason, created_at) VALUES (?, ?, ?, ?)",
        (attempt_number, text, reason, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def clear_writer_session():
    """النقطة 1: تصفير وتطهير الذاكرة السياقية المؤقتة فور النشر الناجح لمنع التلوث"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM writer_session_cache;")
    conn.commit()
    conn.close()
    print("[+] تم تصفير ذاكرة الجلسة للوكيل بنجاح.")

if __name__ == "__main__":
    # تشغيل التهيئة عند استدعاء الملف مباشرة
    initialize_database()

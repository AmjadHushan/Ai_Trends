import time
import requests
from database_schema import get_db_connection

# إعدادات مفاتيح الأمان لبوت التيليجرام
# يتم سحب هذه البيانات تلقائياً من خادمك البيئي لضمان الأمان
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
TELEGRAM_API_URL = f"https://telegram.org{TELEGRAM_BOT_TOKEN}"

def send_alert_to_king(rejected_text, attempts_log):
    """
    النقطة 5: صياغة وإرسال تقرير الأمان الشامل إلى حسابك عند فشل المحاولات الثلاث.
    يقوم ببناء رسالة مفصلة تحتوي على النص المرفوض وتاريخ الأخطاء لتسهيل التعديل البشري.
    """
    formatted_message = (
        "⚠️ **تقرير طوارئ رقابي: تدخل بشري مطلوب فوراً** ⚠️\n\n"
        "مولاي، لقد فشل وكيل الكتابة في صياغة نص مقبول رقابياً وقانونياً "
        "بعد استنفاد **3 محاولات متتالية**.\n\n"
        "📝 **النص المرفوض الأخير:**\n"
        f"```{rejected_text}```\n\n"
        "🔍 **تاريخ محاولات الجلسة الفاشلة:**\n"
    )
    
    # تفصيل الأخطاء السابقة التي ارتكبها الوكيل لكي تكون واضحة أمامك
    for idx, log in enumerate(attempts_log, 1):
        formatted_message += f"❌ المحاولة {idx}: {log['rejection_reason']}\n"
        
    formatted_message += (
        "\n⚙️ **الخيارات المتاحة لمقامكم السامي:**\n"
        "1. قم بالرد على هذه الرسالة بالنص المعدل مباشرة.\n"
        "2. اكتب كلمة 'إلغاء' لإجهاض هذا المشروع نهائياً وتطهير الجلسة."
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": formatted_message,
        "parse_mode": "MarkdownV2"
    }
    
    try:
        response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)
        if response.status_code == 200:
            print("[+] تم إرسال تقرير الطوارئ النصي إلى تيليجرام بنجاح. النظام في وضع الانتظار الصامت...")
            return True
        else:
            print(f"[!] خطأ في إرسال الرسالة إلى تيليجرام: {response.text}")
            return False
    except Exception as e:
        print(f"[!] فشل الاتصال بخادم تيليجرام: {str(e)}")
        return False

def wait_for_king_decision():
    """
    بروتوكول الانتظار الصامت (Polling Loop).
    يجعل السيرفر RTX يدخل في حلقة مراقبة صامتة، مستمعاً فقط لردك البشري.
    لن يعود النظام للعمل أو يولد أي لقطة فيديو حتى تمنحه الإذن.
    """
    last_update_id = 0
    print("[*] النظام معلق الآن. بانتظار مرسوم ملكي عبر التيليجرام...")
    
    while True:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 30}
        
        try:
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                updates = response.json().get("result", [])
                
                for update in updates:
                    last_update_id = update["update_id"]
                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id", ""))
                    
                    # التحقق الصارم من أن الرسالة قادمة من حسابك أنت شخصياً لحماية الأمن
                    if chat_id != TELEGRAM_CHAT_ID:
                        continue
                        
                    user_reply = message.get("text", "").strip()
                    
                    if not user_reply:
                        continue
                        
                    print(f"[+] تم استلام المرسوم الملكي: '{user_reply}'")
                    
                    # الحالة الأولى: إذا قررت إلغاء الفكرة تماماً
                    if user_reply.lower() in ["إلغاء", "cancel", "abort"]:
                        return {"status": "aborted", "text": None}
                    
                    # الحالة الثانية: إذا قمت بإدخال النص المعدل يدوياً
                    return {"status": "approved", "text": user_reply}
                    
        except Exception as e:
            print(f"[!] خطأ أثناء انتظار الرد من تيليجرام: {str(e)}")
            
        # راحة معالجة خفيفة لمنع استهلاك موارد السيرفر أثناء الانتظار
        time.sleep(2)

def execute_human_intervention_protocol():
    """
    الدالة الرئيسية التي يتم استدعاؤها من قبل الوكيل الإداري (Manager Agent) 
    عند وصول عداد محاولات الرفض النصي إلى 3.
    """
    # 1. سحب بيانات المحاولات الفاشلة من قاعدة البيانات التي أسسناها
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT rejected_text, rejection_reason FROM writer_session_cache ORDER BY attempt_number ASC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("[!] خطأ: لا توجد بيانات محاولات فاشلة في ذاكرة الجلسة.")
        return None
        
    attempts_log = [{"rejection_reason": row["rejection_reason"]} for row in rows]
    last_rejected_text = rows[-1]["rejected_text"]
    
    # 2. إرسال البلاغ إلى التيليجرام
    if send_alert_to_king(last_rejected_text, attempts_log):
        # 3. الدخول في وضع التجميد والانتظار حتى ورود ردك البشري
        decision = wait_for_king_decision()
        return decision
    
    return {"status": "failed_to_alert", "text": None}

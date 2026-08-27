import os
import sys
import time
import requests
from database_schema import get_db_connection, log_writer_attempt

# إعدادات الأمان والتوكنز الخاصة بسيرفرك المستأجر RTX
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")
TELEGRAM_API_URL = f"https://telegram.org{TELEGRAM_BOT_TOKEN}"

def send_multitopic_proposal_to_king(proposals_list):
    """
    ميزة عرض قائمة المواضيع المقترحة:
    يرسل قائمة منسقة ومرقمة بالمواضيع الأكثر طلباً التي رصدها المدير لتختار منها.
    """
    formatted_message = (
        "📊 **قائمة المواضيع المقترحة لخط الإنتاج** 📊\n\n"
        "مولاي، إليك التقارير اللحظية لأعلى التريندات طلباً. يرجى اختيار أحد الخيارات:\n\n"
    )
    
    for idx, prop in enumerate(proposals_list, 1):
        formatted_message += (
            f"🎬 **الخيار رقم [{idx}]**\n"
            f"🔹 **العنوان:** {prop['title']}\n"
            f"📝 **ملخص الفكرة:** {prop['preview']}\n"
            f"-----------------------------------\n"
        )
        
    formatted_message += (
        "\n⚙️ **المراسيم الملكية المتاحة عبر الرد:**\n"
        "1. اكتب رقم الموضوع مباشرة (مثال: 1 أو 2) لاعتماده وإطلاق الرندرة.\n"
        "2. اكتب 'تعديل: [ملحوظتك]' لتوجيه الكاتب لإعادة الصياغة.\n"
        "3. اكتب 'دقة: [1080 أو 4K]' لضبط أبعاد الفيديو القادم عن بعد.\n"
        "4. اكتب 'الغاء' لإسقاط الدورة الحالية كلياً وتطهير الكاش."
    )
    
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": formatted_message, "parse_mode": "Markdown"}
    try:
        response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)
        if response.status_code == 200:
            print("[+] تم إرسال قائمة المواضيع المقترحة إلى التيليجرام بنجاح.")
    except Exception as e:
        print(f"[!] خطأ في إرسال قائمة المواضيع: {str(e)}")

def send_alert_to_king(rejected_text, attempts_log):
    """تقرير الطوارئ الرقابي عند فشل المحاولات الثلاث في الفحص المزدوج"""
    formatted_message = (
        "⚠️ **تقرير طوارئ رقابي: تدخل بشري مطلوب** ⚠️\n\n"
        "مولاي، لقد فشل وكيل الكتابة في تعديل النص بعد استنفاد **3 محاولات متتالية**.\n\n"
        "📝 **النص المرفوض الأخير:**\n"
        f"```{rejected_text}```\n\n"
        "⚙️ **الخيارات المتاحة لمقامكم السامي عبر الرد المباشر:**\n"
        "1. اكتب النص المعدل مباشرة هنا لتجاوز الرقابة وبدء الإنتاج.\n"
        "2. اكتب 'الغاء' لإجهاض المشروع نهائياً وتطهير الجلسة."
    )
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": formatted_message, "parse_mode": "Markdown"}
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)

def send_certificate_to_king(video_id):
    """خدمة طلب الشهادة: تسحب شهادة الفحص الشاملة من قاعدة البيانات وترسلها لك"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_certificates WHERE video_id = ?", (video_id,))
    cert = cursor.fetchone()
    conn.close()
    
    if cert:
        msg = (
            "📜 **شهادة فحص وتوثيق فيديو رسمية** 📜\n\n"
            f"🆔 **معرف الفيديو:** {cert['video_id']}\n"
            f"🎬 **العنوان:** {cert['video_title']}\n"
            f"⏱️ **تاريخ النشر:** {cert['published_at']}\n"
            f"🔑 **بصمة SHA-256:** `{cert['script_hash'][:16]}...`\n"
            "-----------------------------------\n"
            f"🕌 الفحص الشرعي: {'✅ ناجح' if cert['islamic_compliance_passed'] else '❌ راسب'}\n"
            f"⚖️ الفحص القانوني: {'✅ ناجح' if cert['eu_law_passed'] else '❌ راسب'}\n"
            f"👁️ الفحص البصري: {'✅ ناجح' if cert['realism_protocol_passed'] else '❌ راسب'}\n"
            f"🔒 ختم C2PA الرقمي: {'✅ ناجح' if cert['c2pa_validated'] else '❌ راسب'}\n"
            "-----------------------------------\n"
            f"📊 **تقييم الجودة الإجمالي:** {cert['overall_score']}/100"
        )
    else:
        msg = f"❌ لم أجد أي شهادة فحص مسجلة للمعرف: {video_id}"
        
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)

def parse_king_command(user_reply):
    """
    محلل الأوامر الذكي والموسع:
    يقوم بفحص وتفكيك نص رسالتك وتحويلها إلى متغيرات برمجية فورية يفهمها السيرفر.
    """
    text_lower = user_reply.strip().lower()
    
    # 1. التقاط رقم الموضوع المختار من القائمة (مثال: "1" أو "2" أو "3")
    if text_lower in ["1", "2", "3", "4", "5"]:
        return {"action": "select_topic_number", "data": text_lower}
        
    # 2. التقاط وتحديث دقة الفيديوهات عن بعد (تحديث ملفات الحقن والإنتاج)
    if text_lower.startswith("دقة:") or text_lower.startswith("resolution:"):
        resolution_val = user_reply.split(":", 1)[1].strip().lower()
        print(f"[+] تم التقاط أمر الدقة السامي: {resolution_val}")
        return {"action": "set_resolution", "data": resolution_val}

    # 3. أوامر الرفض أو الإلغاء الكلي للموضوع أو الجلسة الطارئة
    if text_lower in ["إلغاء", "الغاء", "رفض", "cancel", "reject"]:
        return {"action": "abort", "data": None}
        
    # 4. خدمة طلب شهادة فيديو محدد
    if text_lower.startswith("شهادة:") or text_lower.startswith("cert:"):
        video_id = user_reply.split(":", 1)[1].strip()
        send_certificate_to_king(video_id)
        return {"action": "system_command_executed", "data": None}
        
    # 5. خدمة تحديد مدة الفيديو
    if text_lower.startswith("مدة:") or text_lower.startswith("duration:"):
        duration_val = user_reply.split(":", 1)[1].strip()
        return {"action": "set_duration", "data": duration_val}
        
    # 6. خدمة توجيه تعديل مخصص للأفكار أو النصوص
    if text_lower.startswith("تعديل:") or text_lower.startswith("edit:"):
        edit_instruction = user_reply.split(":", 1)[1].strip()
        return {"action": "custom_edit_request", "data": edit_instruction}
        
    # 7. إذا أرسلت نصاً حراً مباشراً، يعتبره النظام السيناريو البديل المعتمد يدوياً من قبلك
    return {"action": "approve_with_new_script", "data": user_reply}

def check_telegram_for_response():
    """فحص الاتصال الصامت وقراءة آخر الرسائل الواردة من حساب الملك"""
    last_update_id = 0
    url = f"{TELEGRAM_API_URL}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 1}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            updates = response.json().get("result", [])
            if updates:
                last_update = updates[-1]
                message = last_update.get("message", {})
                chat_id = str(message.get("chat", {}).get("id", ""))
                
                # التحقق الصارم من هوية الحساب لمنع أي اختراق خارجي
                if chat_id == TELEGRAM_CHAT_ID:
                    user_reply = message.get("text", "").strip()
                    if user_reply:
                        return parse_king_command(user_reply)
    except Exception as e:
        print(f"[!] خطأ في جلب تحديثات تيليجرام: {str(e)}")
    return None

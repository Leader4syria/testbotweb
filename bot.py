# -*- coding: utf-8 -*-
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, jsonify
import sqlite3
import os
# لا حاجة لـ 'threading' هنا لأن Render ستدير الـ web و الـ worker بشكل منفصل.

# *************** هام جداً ***************
# استبدل YOUR_BOT_TOKEN_HERE بالتوكن الخاص بك الذي تحصل عليه من BotFather.
# من الأفضل استخدام متغير بيئة (Environment Variable) لتخزين التوكن.
# Render ستسمح لك بضبط هذا المتغير.
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7834007989:AAHuV-pMgYTC2fv3x56_4_UT42qVB7VLMgU") # تم تحديث التوكن!
if TOKEN == "7834007989:AAHuV-pMgYTC2fv3x56_4_UT42qVB7VLMgU":
    logging.warning("TELEGRAM_BOT_TOKEN لم يتم ضبطه كمتغير بيئة. يرجى ضبطه في Render (إذا لم يكن هذا التوكن حساسًا وترغب في تضمينه مباشرةً).")
# ***************************************

# *************** هام جداً ***************
# استبدل هذا الرابط برابط GitHub Pages الحقيقي الخاص بتطبيق الويب الخاص بك.
# الذي قمت بنشره مسبقًا.
WEB_APP_URL = "https://leader4syria.github.io/testbotweb/" # هذا هو الرابط الذي أرسلته لي!
# ***************************************

# إعدادات تسجيل الدخول (Logging) لتتبع ما يحدث في البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- إعداد قاعدة البيانات SQLite ---
DATABASE_NAME = 'services.db'

def init_db():
    """تهيئة قاعدة البيانات وإنشاء جدول الخدمات إذا لم يكن موجودًا."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price TEXT
        )
    ''')
    # إضافة بعض البيانات التجريبية إذا كانت القاعدة فارغة
    cursor.execute('SELECT COUNT(*) FROM services')
    if cursor.fetchone()[0] == 0:
        services_data = [
            ('استشارة تقنية', 'مساعدة في حل المشاكل التقنية وتوجيه المشاريع.', '50 دولار/ساعة'),
            ('تصميم شعار', 'تصميم شعارات احترافية للشركات والأفراد.', '150 دولار'),
            ('تطوير تطبيقات الويب', 'بناء تطبيقات ويب مخصصة باحترافية عالية.', 'تبدأ من 500 دولار'),
            ('دعم فني 24/7', 'دعم فني على مدار الساعة لجميع مشاكلك.', '30 دولار/شهر')
        ]
        cursor.executemany('INSERT INTO services (name, description, price) VALUES (?, ?, ?)', services_data)
        logger.info("تم إضافة بيانات تجريبية إلى قاعدة البيانات.")
    conn.commit()
    conn.close()
    logger.info("تم تهيئة قاعدة البيانات SQLite.")

def get_services():
    """جلب جميع الخدمات من قاعدة البيانات."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT name, description, price FROM services')
    services = [{'name': row[0], 'description': row[1], 'price': row[2]} for row in cursor.fetchall()]
    conn.close()
    return services

# --- وظائف البوت (Telegram Bot Handlers) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة ترحيبية وزر لفتح تطبيق الويب."""
    # إنشاء زر يفتح Web App
    keyboard = [[
        InlineKeyboardButton(
            "افتح خدماتنا",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "مرحباً بك في بوت الخدمات لدينا! 👋\nاضغط على الزر أدناه لاستكشاف الخدمات المتاحة:",
        reply_markup=reply_markup
    )
    logger.info(f"تم إرسال رسالة الترحيب إلى {update.effective_user.id}")

# --- إعداد تطبيق Flask لـ API ---
app = Flask(__name__)

@app.route('/api/services', methods=['GET'])
def api_services():
    """نقطة نهاية API لجلب الخدمات من قاعدة البيانات."""
    services = get_services()
    logger.info(f"تم طلب خدمات API: تم إرجاع {len(services)} خدمة.")
    return jsonify(services)

# --- وظيفة تشغيل البوت ---
def run_telegram_bot():
    """دالة تشغيل البوت."""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    logger.info("بدء تشغيل بوت التليجرام...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

# هذا الجزء من الكود لن يتم تشغيله مباشرةً كما هو في Render،
# حيث سيقوم Render بتشغيل "web" و "worker" بشكل منفصل بناءً على ملف Procfile.
# ولكن، دالة `init_db()` في الأعلى ستضمن تهيئة القاعدة عند بدء أي من العمليتين.
if __name__ == "__main__":
    # هذا الجزء مخصص للاختبار المحلي فقط!
    # لا تستخدم هذا في الإنتاج على Render.
    # في Render، سيتم تشغيل البوت والـ Flask API كعمليات منفصلة.
    logger.warning("تشغيل محلي: سيبدأ البوت وخادم Flask. للتوزيع، استخدم Render Procfile.")
    from threading import Thread
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=5000)

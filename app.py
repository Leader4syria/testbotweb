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
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7834007989:AAHuV-pMgYTC2fv3x56_4_UT42qVB7VLMgU") # التوكن المضمّن
if TOKEN == "7834007989:AAHuV-pMgYTC2fv3x56_4_UT42qVB7VLMgU":
    logging.warning("TELEGRAM_BOT_TOKEN لم يتم ضبطه كمتغير بيئة في Render. يوصى بضبطه هناك.")
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


# ************************************************************
# التغييرات الرئيسية هنا:
# 1. سيتم استدعاء `init_db()` عند بدء تشغيل أي من العمليتين (web أو worker).
# 2. عندما يتم تشغيل الملف كـ `worker` (أي عن طريق `python bot.py` من Procfile)،
#    سيتم استدعاء `run_telegram_bot()` مباشرة.
# 3. إزالة الكتلة `if __name__ == "__main__":` التي كانت مخصصة للاختبار المحلي فقط.
# ************************************************************

# تهيئة قاعدة البيانات عند بدء التشغيل
# هذا السطر سيكون خارج أي دالة، لذا سيتم تشغيله عند استيراد الملف أو تشغيله.
init_db()

# هذا الجزء سيتم تنفيذه فقط عندما يتم تشغيل الملف بواسطة عملية الـ worker
# (أي عندما يكون `python bot.py` هو أمر البدء).
# يجب أن يتأكد هذا الجزء من أن البوت يبدأ بالعمل.
try:
    # لتشغيل البوت كـ worker
    # سيتم تشغيل هذه الدالة مباشرة عندما يتم استدعاء "python bot.py"
    # في عملية الـ worker التي تحددها في Procfile.
    if os.getenv("RENDER_SERVICE_TYPE") == "worker": # محاولة اكتشاف بيئة Render worker
        run_telegram_bot()
    else:
        # إذا لم يكن worker (على الأرجح web service)، فلا تفعل شيئًا هنا.
        # Gunicorn سيتولى تشغيل تطبيق Flask.
        logger.info("يبدو أن هذا ليس worker. لم يتم تشغيل بوت التليجرام.")
except Exception as e:
    logger.error(f"حدث خطأ في بدء تشغيل البوت: {e}")


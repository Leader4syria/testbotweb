# -*- coding: utf-8 -*-
import logging
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from flask import Flask, jsonify
import sqlite3
import os

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
logging.getLogger("httpx").setLevel(logging.WARNING) # httpx تستخدمها Flask أو مكتبات أخرى
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

# --- إعداد تطبيق Flask لـ API ---
app = Flask(__name__)

@app.route('/api/services', methods=['GET'])
def api_services():
    """نقطة نهاية API لجلب الخدمات من قاعدة البيانات."""
    services = get_services()
    logger.info(f"تم طلب خدمات API: تم إرجاع {len(services)} خدمة.")
    return jsonify(services)

# ************************************************************
# التغييرات الرئيسية لـ Telebot
# ************************************************************

# تهيئة بوت Telebot
bot = telebot.TeleBot(TOKEN)

# وظائف البوت (Telegram Bot Handlers) باستخدام Telebot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """إرسال رسالة ترحيبية وزر لفتح تطبيق الويب."""
    # إنشاء زر يفتح Web App
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="افتح خدماتنا",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    keyboard.add(button)

    bot.send_message(
        message.chat.id,
        "مرحباً بك في بوت الخدمات لدينا! 👋\nاضغط على الزر أدناه لاستكشاف الخدمات المتاحة:",
        reply_markup=keyboard
    )
    logger.info(f"تم إرسال رسالة الترحيب إلى {message.chat.id}")


# ************************************************************
# جزء تشغيل البوت (Worker)
# ************************************************************

# تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

# هذا الجزء سيتم تنفيذه مباشرة عندما يتم تشغيل الملف بواسطة عملية الـ worker
# (أي عندما يكون `python bot.py` هو أمر البدء).
# يجب أن يتأكد هذا الجزء من أن البوت يبدأ بالعمل.
try:
    logger.info("بدء تشغيل بوت التليجرام (باستخدام Telebot)...")
    # هذا الأمر يشغل البوت في وضع الاستطلاع (polling)
    bot.polling(none_stop=True)
except Exception as e:
    logger.error(f"حدث خطأ فادح في بدء تشغيل البوت: {e}", exc_info=True) # exc_info=True لطباعة traceback الكامل


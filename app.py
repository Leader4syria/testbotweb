import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# إنشاء مثيل لتطبيق Flask
app = Flask(__name__)
# تفعيل CORS
CORS(app)

# اسم ملف قاعدة البيانات SQLite
DATABASE = 'bot_data_backup_20250725_170311.db'

def get_db_connection():
    """
    يقوم بإنشاء اتصال بقاعدة بيانات SQLite.
    يقوم بتعيين خاصية row_factory لتمكين الوصول إلى الأعمدة بالاسم، مما يجعل النتائج أسهل في التعامل.
    """
    if not os.path.exists(DATABASE):
        # التحقق من وجود ملف قاعدة البيانات وإبلاغ إذا كان مفقوداً
        print(f"خطأ: ملف قاعدة البيانات '{DATABASE}' غير موجود. يرجى التأكد من وضعه في نفس مجلد 'app.py'.")
        # بدلاً من رفع استثناء، سنحاول الاستمرار لتقديم الصفحة HTML على الأقل
        # ولكن وظائف الـ API ستفشل.
        return None # Return None if DB file is not found
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# نقطة نهاية (Endpoint) لجلب معلومات المستخدم
@app.route('/api/user_info', methods=['GET'])
def get_user_info():
    """
    يقوم بجلب وعرض معلومات المستخدم (المعرف والرصيد) من قاعدة البيانات.
    لأغراض هذا المثال، سنقوم بجلب أول مستخدم في جدول 'users'.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({
            'user_id': 'DB_ERROR',
            'balance': 0.00,
            'message': 'Database file not found.'
        }), 500
    try:
        user = conn.execute('SELECT telegram_id, balance FROM users LIMIT 1').fetchone()
        conn.close()

        if user:
            return jsonify({
                'user_id': str(user['telegram_id']),
                'balance': user['balance']
            })
        else:
            print("لم يتم العثور على مستخدم في قاعدة البيانات. يتم إرجاع بيانات افتراضية.")
            return jsonify({
                'user_id': 'معرف_افتراضي',
                'balance': 0.00
            })
    except Exception as e:
        print(f"خطأ في جلب معلومات المستخدم: {e}")
        return jsonify({
            'user_id': 'خطأ_API',
            'balance': 0.00,
            'message': f'خطأ في الخادم عند جلب معلومات المستخدم: {str(e)}'
        }), 500

# نقطة نهاية لجلب جميع التصنيفات (الرئيسية والفرعية)
@app.route('/api/categories', methods=['GET'])
def get_all_categories():
    """
    يقوم بجلب وعرض قائمة بجميع التصنيفات المتاحة من جدول 'categories'،
    بما في ذلك معرفات التصنيفات الأبوية (parent_id) لبناء الهيكل الهرمي في الواجهة الأمامية.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database file not found.'}), 500
    try:
        categories = conn.execute('SELECT id, name, parent_id FROM categories').fetchall()
        conn.close()
        categories_list = [{'id': str(c['id']), 'name': c['name'], 'parent_id': str(c['parent_id']) if c['parent_id'] else None} for c in categories]
        return jsonify(categories_list)
    except Exception as e:
        print(f"خطأ في جلب التصنيفات: {e}")
        return jsonify({'message': f'خطأ في الخادم عند جلب التصنيفات: {str(e)}'}), 500

# نقطة نهاية لجلب الخدمات، مع إمكانية التصفية حسب category_id
@app.route('/api/services', methods=['GET'])
def get_services():
    """
    يقوم بجلب وعرض قائمة بجميع الخدمات من جدول 'services'.
    يمكن تمرير parameter 'category_id' لتصفية الخدمات حسب تصنيف معين.
    """
    category_id = request.args.get('category_id')
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database file not found.'}), 500
    try:
        if category_id and category_id != 'all':
            services = conn.execute('SELECT id, name, description, base_price, category_id FROM services WHERE category_id = ?', (category_id,)).fetchall()
        else:
            services = conn.execute('SELECT id, name, description, base_price, category_id FROM services').fetchall()
        conn.close()

        services_list = []
        for s in services:
            service_dict = {
                'id': str(s['id']),
                'name': s['name'],
                'description': s['description'],
                'price': s['base_price'],
                'category_id': str(s['category_id']),
                # استخدام الصورة المحددة لجميع الخدمات
                'image_url': 'https://f.top4top.io/p_3493hixol1.jpg',
                'fallback_image_url': 'https://placehold.co/400x250/B0B0B0/FFFFFF?text=صورة+غير+متاحة'
            }
            services_list.append(service_dict)
        return jsonify(services_list)
    except Exception as e:
        print(f"خطأ في جلب الخدمات: {e}")
        return jsonify({'message': f'خطأ في الخادم عند جلب الخدمات: {str(e)}'}), 500

# نقطة نهاية لمحاكاة عملية تعبئة الرصيد
@app.route('/api/topup', methods=['POST'])
def top_up_balance():
    """
    محاكاة عملية تعبئة الرصيد. تستقبل مبلغ التعبئة، وتضيفه إلى رصيد المستخدم
    في قاعدة البيانات.
    """
    data = request.get_json()
    amount = data.get('amount')

    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({'message': 'المبلغ المدخل غير صالح. يرجى إدخال مبلغ موجب.'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': 'Database file not found.'}), 500
    try:
        user = conn.execute('SELECT telegram_id, balance FROM users LIMIT 1').fetchone()
        if not user:
            return jsonify({'message': 'لم يتم العثور على المستخدم في قاعدة البيانات لتعبئة الرصيد.'}), 404

        current_balance = user['balance']
        new_balance = current_balance + amount

        conn.execute('UPDATE users SET balance = ? WHERE telegram_id = ?',
                     (new_balance, user['telegram_id']))
        conn.commit()

        return jsonify({
            'message': 'تمت تعبئة الرصيد بنجاح!',
            'new_balance': new_balance
        })
    except Exception as e:
        conn.rollback()
        print(f"خطأ في قاعدة البيانات أثناء تعبئة الرصيد: {e}")
        return jsonify({'message': f'خطأ في الخادم أثناء تعبئة الرصيد: {str(e)}'}), 500
    finally:
        conn.close()

# نقطة نهاية للصفحة الرئيسية التي تعرض الواجهة الأمامية بالكامل
@app.route('/', methods=['GET'])
def home():
    """
    نقطة نهاية الصفحة الرئيسية.
    تعرض صفحة HTML الكاملة مع التصميم والوظائف.
    الآن، عند زيارة http://127.0.0.1:5000/ في المتصفح، سترى الصفحة كاملة.
    """
    html_content = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>صفحة التصنيفات والخدمات</title>
    <!--
        تضمين خط "Tajawal" من Google Fonts.
        هذا الخط يوفر مظهراً عصرياً واحترافياً ويتناسب بشكل جيد مع التصميم العربي.
        تم تضمين وزنين للخط (عادي وسميك) لمرونة أكبر في التصميم.
    -->
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <!--
        تضمين مكتبة Tailwind CSS من CDN لتطبيق التنسيقات بسهولة وسرعة.
        Tailwind CSS توفر مجموعة واسعة من الفئات الجاهزة لتصميم واجهة المستخدم المتجاوبة.
    -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        // تهيئة إعدادات Tailwind CSS لتخصيص الألوان والخطوط.
        // هنا نقوم بتعريف الألوان المخصصة المطلوبة: الأخضر الغابي، الذهبي، والأبيض.
        // كما تم إضافة خط "Tajawal" إلى قائمة الخطوط الممتدة.
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        'emerald-green': '#005C54', // اللون الأخضر الزمردي الغامق الجديد
                        'gold': '#FFD700',        // اللون الذهبي المستخدم في الأيقونات، النصوص المميزة، والأزرار (تم الإبقاء عليه للعناصر الذهبية)
                        'white': '#FFFFFF',         // اللون الأبيض الأساسي للخلفيات وبعض النصوص
                        'light-gray': '#F5F5F5',    // لون رمادي فاتح للخلفية العامة للصفحة لراحة العين
                        'dark-gray': '#333333',     // لون رمادي غامق للنصوص الأساسية لتحقيق تباين جيد
                        'medium-gray': '#6B7280',   // لون رمادي متوسط للنصوص الثانوية والوصف
                    },
                    fontFamily: {
                        // تعريف خط Tajawal كخط أساسي لضمان مظهر عصري وواضح ومناسب للعربية.
                        // "sans-serif" هو خط احتياطي في حال عدم تحميل Tajawal.
                        'tajawal': ['Tajawal', 'sans-serif'],
                    }
                }
            }
        }
    </script>
    <style>
        /*
            تنسيقات CSS مخصصة إضافية.
            تحديد خط الجسم الافتراضي إلى Tajawal لضمان تناسق الخطوط عبر الصفحة بأكملها.
            تعيين لون خلفية الجسم ليتناسب مع لوحة الألوان المحددة.
        */
        body {
            font-family: 'Tajawal', sans-serif; /* استخدام خط Tajawal كخط أساسي */
            background-color: #F5F5F5; /* استخدام رمادي فاتح للخلفية العامة للصفحة */
        }
        /*
            إخفاء شريط التمرير الافتراضي في المتصفحات المختلفة لتوفير مظهر أنظف.
            وظيفة التمرير تبقى موجودة، فقط الشريط المرئي هو الذي يتم إخفاؤه.
        */
        ::-webkit-scrollbar {
            display: none; /* لإخفاء شريط التمرير في متصفحات WebKit (مثل Chrome و Safari) */
        }
        /* لإخفاء شريط التمرير في متصفح Firefox */
        html {
            scrollbar-width: none;
        }
    </style>
</head>
<body class="bg-light-gray text-dark-gray min-h-screen flex flex-col">
    <!-- مؤشر تحميل بسيط، سيختفي عند انتهاء تهيئة JavaScript -->
    <div id="loadingIndicator" class="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        <div class="flex flex-col items-center">
            <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-gold"></div>
            <p class="mt-4 text-lg text-emerald-green">جاري التحميل...</p>
        </div>
    </div>

    <!--
        قسم الرأس (Header Section):
        يحتوي على شعار التطبيق أو اسمه ومعلومات المستخدم (المعرف والرصيد).
        يتم تثبيت الرأس في الأعلى (sticky) ليبقى مرئياً عند التمرير.
        يتم تطبيق تنسيقات الألوان (الأخضر الزمردي، الذهبي، والأبيض) والظلال.
    -->
    <header class="bg-emerald-green shadow-lg py-4 px-6 flex items-center justify-between sticky top-0 z-50 rounded-b-lg">
        <!-- قسم الشعار أو اسم التطبيق -->
        <div class="flex items-center space-x-3 rtl:space-x-reverse">
            <!-- أيقونة SVG تمثل الشعار، بتلوين ذهبي لتبرز -->
            <svg class="w-8 h-8 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m7 0V5a2 2 0 012-2h2a2 2 0 012 2v6m-6 0h-2"></path>
            </svg>
            <!-- اسم التطبيق "خدماتي" بخط كبير وسميك ولون أبيض -->
            <h1 class="text-white text-2xl font-bold">خدماتي</h1>
        </div>

        <!-- معلومات المستخدم (معرف المستخدم والرصيد) -->
        <div class="flex items-center space-x-6 rtl:space-x-reverse">
            <div class="text-right">
                <!-- عرض معرف المستخدم، مع جزء منه بلون ذهبي للتميز -->
                <p class="text-white text-sm">مرحباً، <span id="userIdDisplay" class="font-semibold text-gold"></span></p>
                <!-- عرض رصيد المستخدم، بخط أكبر وسميك ولون ذهبي بارز -->
                <p class="text-white text-lg font-bold">رصيدك: <span id="userBalanceDisplay" class="text-gold">0.00</span> ل.س</p>
            </div>
            <!-- صورة رمزية للمستخدم (Avatar) بلون ذهبي وخضراء -->
            <div class="w-12 h-12 bg-gold rounded-full flex items-center justify-center text-emerald-green font-bold text-xl border-2 border-white">
                أ.ع <!-- أحرف أولية لاسم المستخدم -->
            </div>
        </div>
    </header>

    <!--
        المنطقة الرئيسية للمحتوى (Main Content Area):
        تحتوي على نظام التبويبات للتصنيفات وقسم عرض الخدمات وقسم تعبئة الرصيد.
        يتم تحديد عرضها لتكون متجاوبة وتتمركز في الصفحة.
    -->
    <main class="flex-grow container mx-auto p-4 md:p-8">
        <!--
            شريط التنقل (Navigation) للتصنيفات / التبويبات:
            يسمح للمستخدم باختيار تصنيف معين لعرض الخدمات المتعلقة به.
            مصمم ببطاقة بيضاء ذات حواف دائرية وظل.
        -->
        <nav class="bg-white p-4 rounded-lg shadow-md mb-8">
            <ul id="categoryTabs" class="flex flex-wrap justify-center gap-4 text-dark-gray font-medium text-lg">
                <!-- تبويبات التصنيفات سيتم إنشاؤها ديناميكياً بواسطة JavaScript هنا -->
            </ul>
        </nav>

        <!--
            منطقة عرض الخدمات (Services Display Area):
            هذه الشبكة ستعرض بطاقات الخدمات المختلفة.
            تنسيق الشبكة يتغير تلقائياً بناءً على حجم الشاشة (متجاوب).
        -->
        <section id="servicesSection" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-12">
            <!-- بطاقات الخدمات سيتم إنشاؤها ديناميكياً بواسطة JavaScript هنا -->
        </section>

        <!--
            قسم تعبئة الرصيد (Top-up Balance Section):
            يحتوي على حقل إدخال للمبلغ وزر لتعبئة الرصيد عبر "شام كاش".
            مصمم ببطاقة بيضاء ذات حواف دائرية وظل، مع تنسيق مركزي.
        -->
        <section class="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 class="text-2xl font-bold text-emerald-green mb-4 text-center">تعبئة الرصيد عبر شام كاش</h2>
            <div class="flex flex-col md:flex-row items-center justify-center gap-4">
                <!-- حقل إدخال للمبلغ، بتصميم أنيق ومظهر رمادي فاتح -->
                <input type="number" id="topUpAmount" placeholder="أدخل المبلغ هنا (ل.س)"
                       class="flex-grow w-full md:w-auto p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gold text-lg text-dark-gray bg-light-gray">
                <!-- زر تعبئة الرصيد، بلون ذهبي ونصوص خضراء غابية، مع تأثيرات تحويل عند التمرير -->
                <button id="topUpButton"
                        class="bg-gold text-emerald-green font-bold py-3 px-8 rounded-md hover:bg-opacity-90 transition duration-300 transform hover:scale-105 shadow-lg w-full md:w-auto text-lg">
                    تعبئة الرصيد
                </button>
            </div>
            <!-- رسالة عرض بعد تعبئة الرصيد، مخفية افتراضياً -->
            <p id="topUpMessage" class="text-center mt-4 text-sm text-gray-600 hidden">
                سيتم معالجة طلبك لتعبئة الرصيد.
            </p>
        </section>
    </main>

    <!--
        قسم التذييل (Footer Section):
        يحتوي على معلومات حقوق الطبع والنشر وروابط سريعة.
        مصمم بخلفية خضراء زمردية ونصوص بيضاء، مع حواف دائرية علوية.
    -->
    <footer class="bg-emerald-green text-white py-6 text-center rounded-t-lg shadow-inner">
        <p>&copy; 2025 جميع الحقوق محفوظة لخدماتي. تصميم رائع مع الألوان الزمردية والذهبية.</p>
        <div class="flex justify-center space-x-4 rtl:space-x-reverse mt-2">
            <!-- روابط سريعة مع تأثيرات تحويل عند التمرير -->
            <a href="#" class="hover:text-gold transition duration-300">الخصوصية</a>
            <a href="#" class="hover:text-gold transition duration-300">شروط الاستخدام</a>
            <a href="#" class="hover:text-gold transition duration-300">اتصل بنا</a>
        </div>
    </footer>

    <!--
        النافذة المنبثقة (Modal) لتأكيد أو حالة تعبئة الرصيد:
        تظهر لتوفير ردود فعل للمستخدم (نجاح تعبئة الرصيد أو رسالة خطأ).
        مخفية افتراضياً وتظهر باستخدام JavaScript.
    -->
    <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center hidden z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full text-center">
            <h3 id="modalTitle" class="text-2xl font-bold mb-4 text-emerald-green"></h3>
            <p id="modalMessage" class="text-dark-gray mb-6"></p>
            <button id="modalCloseButton" class="bg-gold text-emerald-green font-bold py-2 px-6 rounded-md hover:bg-opacity-90 transition duration-300">إغلاق</button>
        </div>
    </div>

    <!--
        قسم JavaScript:
        يحتوي على جميع الوظائف الديناميكية للصفحة.
        تم تعديل هذا القسم لدعم التنقل بين التصنيفات الرئيسية والفرعية،
        وجلب الخدمات بناءً على التصنيف المختار من الخادم الخلفي.
    -->
    <script>
        // --- متغيرات عامة لتخزين البيانات وحالة الواجهة ---
        let allCategories = []; // لتخزين جميع التصنيفات (الرئيسية والفرعية) من الـ API
        let services = [];      // لتخزين الخدمات التي يتم جلبها للتصنيف الحالي
        let userId = '';
        let userBalance = 0.00;
        let currentView = 'main_categories'; // لتحديد العرض الحالي: 'main_categories' أو 'sub_categories' أو 'services_view'
        let selectedMainCategory = null; // لتتبع التصنيف الرئيسي المختار عند عرض التصنيفات الفرعية

        // --- مراجع لعناصر DOM (Document Object Model) ---
        // الحصول على عناصر HTML بالمعرفات الخاصة بها للتفاعل معها بواسطة JavaScript.
        const loadingIndicator = document.getElementById('loadingIndicator'); // مؤشر التحميل الجديد
        const userIdDisplay = document.getElementById('userIdDisplay');
        const userBalanceDisplay = document.getElementById('userBalanceDisplay');
        const categoryTabsContainer = document.getElementById('categoryTabs');
        const servicesSection = document.getElementById('servicesSection');
        const topUpAmountInput = document.getElementById('topUpAmount');
        const topUpButton = document.getElementById('topUpButton');
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalMessage = document.getElementById('modalMessage');
        const modalCloseButton = document.getElementById('modalCloseButton');

        // --- عناوين API الافتراضية ---
        // بما أن Flask سيقدم هذا الملف والـ API من نفس النطاق، يمكن استخدام مسارات نسبية.
        const API_BASE_URL = ''; // فارغ للإشارة إلى نفس الأصل

        // --- الدالة لجلب بيانات المستخدم من الـ API ---
        async function fetchUserInfo() {
            console.log('Fetching user info...');
            try {
                const response = await fetch(`${API_BASE_URL}/api/user_info`);
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Failed to fetch user info: ${response.status} - ${errorText}`);
                }
                const data = await response.json();
                userId = data.user_id;
                userBalance = data.balance;
                updateUserInfoDisplay(); // تحديث الواجهة بعد جلب البيانات
                console.log('User info fetched successfully:', data);
            } catch (error) {
                console.error('Error fetching user info:', error);
                showModal('خطأ', 'فشل في جلب معلومات المستخدم. يرجى التأكد من تشغيل الخادم الخلفي.');
                throw error; // إعادة إلقاء الخطأ للسماح لكتلة try/catch الرئيسية بالتقاطه
            }
        }

        // --- الدالة لجلب جميع التصنيفات (الرئيسية والفرعية) من الـ API ---
        async function fetchAllCategories() {
            console.log('Fetching all categories...');
            try {
                const response = await fetch(`${API_BASE_URL}/api/categories`);
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Failed to fetch categories: ${response.status} - ${errorText}`);
                }
                allCategories = await response.json();
                console.log('Categories fetched successfully:', allCategories);
            } catch (error) {
                console.error('Error fetching all categories:', error);
                showModal('خطأ', 'فشل في جلب بيانات التصنيفات. يرجى التأكد من تشغيل الخادم الخلفي.');
                throw error; // إعادة إلقاء الخطأ
            }
        }

        // --- الدالة لجلب الخدمات بناءً على category_id من الـ API ---
        async function fetchServicesByCategoryId(categoryId) {
            console.log(`Fetching services for category: ${categoryId}...`);
            try {
                // استخدام parameter 'category_id' في الـ URL لجلب الخدمات المحددة
                const response = await fetch(`${API_BASE_URL}/api/services?category_id=${categoryId}`);
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Failed to fetch services: ${response.status} - ${errorText}`);
                }
                services = await response.json(); // تحديث مصفوفة الخدمات العالمية
                console.log('Services fetched successfully:', services);
            } catch (error) {
                console.error('Error fetching services:', error);
                showModal('خطأ', 'فشل في جلب بيانات الخدمات. يرجى المحاولة لاحقاً.');
                throw error; // إعادة إلقاء الخطأ
            }
        }

        // --- الدالة لتحديث عرض معلومات المستخدم ---
        function updateUserInfoDisplay() {
            userIdDisplay.textContent = userId; // تعيين نص معرف المستخدم
            userBalanceDisplay.textContent = userBalance.toFixed(2); // تنسيق الرصيد لعدد عشريتين
            console.log('User info display updated.');
        }

        // --- الدالة لعرض التصنيفات الرئيسية ---
        async function renderMainCategories() {
            console.log('Rendering main categories...');
            categoryTabsContainer.innerHTML = ''; // مسح أي تبويبات موجودة مسبقاً
            currentView = 'main_categories';
            selectedMainCategory = null; // لا يوجد تصنيف رئيسي محدد حاليا

            // إضافة تبويب "جميع الخدمات" كخيار أول.
            const allServicesItem = document.createElement('li');
            const allServicesButton = document.createElement('button');
            allServicesButton.textContent = 'جميع الخدمات';
            allServicesButton.dataset.type = 'all_services'; // نوع مخصص
            allServicesButton.className = `category-tab px-6 py-3 rounded-full transition duration-300 hover:bg-gold hover:text-emerald-green focus:outline-none focus:ring-2 focus:ring-gold focus:ring-opacity-75 whitespace-nowrap bg-gold text-emerald-green shadow-md`;
            allServicesItem.appendChild(allServicesButton);
            categoryTabsContainer.appendChild(allServicesItem);

            // تصفية التصنيفات الرئيسية (التي ليس لديها parent_id)
            const mainCategories = allCategories.filter(cat => cat.parent_id === null);

            mainCategories.forEach(category => {
                const listItem = document.createElement('li');
                const button = document.createElement('button');
                button.textContent = category.name;
                button.dataset.categoryId = category.id;
                button.dataset.type = 'main_category'; // نوع مخصص
                // التحقق مما إذا كان هذا التصنيف الرئيسي لديه تصنيفات فرعية
                const hasSubcategories = allCategories.some(subCat => subCat.parent_id === category.id);
                button.dataset.hasSubcategories = hasSubcategories; // تخزين هذه المعلومة
                button.className = `category-tab px-6 py-3 rounded-full transition duration-300 hover:bg-gold hover:text-emerald-green focus:outline-none focus:ring-2 focus:ring-gold focus:ring-opacity-75 whitespace-nowrap bg-light-gray text-dark-gray`;
                listItem.appendChild(button);
                categoryTabsContainer.appendChild(listItem);
            });

            // عند عرض التصنيفات الرئيسية، قم بعرض جميع الخدمات افتراضياً.
            await fetchServicesByCategoryId('all');
            renderServicesDisplay(); // تحديث عرض الخدمات
            console.log('Main categories and initial services rendered.');
        }

        // --- الدالة لعرض التصنيفات الفرعية لتصنيف رئيسي معين ---
        async function renderSubcategories(parentCategoryId) {
            console.log(`Rendering subcategories for parent: ${parentCategoryId}...`);
            categoryTabsContainer.innerHTML = ''; // مسح التبويبات الحالية
            currentView = 'sub_categories';
            selectedMainCategory = parentCategoryId; // تخزين التصنيف الرئيسي

            // إضافة زر "العودة للتصنيفات الرئيسية"
            const backItem = document.createElement('li');
            const backButton = document.createElement('button');
            backButton.textContent = 'العودة للتصنيفات الرئيسية';
            backButton.dataset.type = 'back_to_main';
            backButton.className = `category-tab px-6 py-3 rounded-full transition duration-300 hover:bg-gold hover:text-emerald-green focus:outline-none focus:ring-2 focus:ring-gold focus:ring-opacity-75 whitespace-nowrap bg-gold text-emerald-green shadow-md`;
            backItem.appendChild(backButton);
            categoryTabsContainer.appendChild(backItem);

            // تصفية التصنيفات الفرعية لهذا التصنيف الرئيسي
            const subCategories = allCategories.filter(cat => cat.parent_id === parentCategoryId);

            if (subCategories.length === 0) {
                console.log(`No subcategories found for ${parentCategoryId}. Fetching services directly.`);
                // في حالة عدم وجود تصنيفات فرعية، نقوم بجلب الخدمات مباشرة للتصنيف الأب
                await fetchServicesByCategoryId(parentCategoryId);
                renderServicesDisplay();
                return;
            }

            subCategories.forEach(category => {
                const listItem = document.createElement('li');
                const button = document.createElement('button');
                button.textContent = category.name;
                button.dataset.categoryId = category.id;
                button.dataset.type = 'sub_category'; // نوع مخصص
                button.className = `category-tab px-6 py-3 rounded-full transition duration-300 hover:bg-gold hover:text-emerald-green focus:outline-none focus:ring-2 focus:ring-gold focus:ring-opacity-75 whitespace-nowrap bg-light-gray text-dark-gray`;
                listItem.appendChild(button);
                categoryTabsContainer.appendChild(listItem);
            });
            // عند الانتقال إلى عرض التصنيفات الفرعية، يتم مسح الخدمات المعروضة مبدئياً
            servicesSection.innerHTML = '';
            console.log('Subcategories rendered.');
        }

        // --- الدالة لإنشاء بطاقة خدمة HTML ---
        function createServiceCard(service) {
            const serviceCard = document.createElement('div');
            serviceCard.className = `bg-white rounded-lg shadow-lg overflow-hidden transform transition duration-300 hover:scale-105 hover:shadow-xl relative`;
            serviceCard.innerHTML = `
                <img src="${service.image_url}" alt="${service.name}" class="w-full h-48 object-cover object-center rounded-t-lg"
                     onerror="this.onerror=null;this.src='${service.fallback_image_url || 'https://placehold.co/400x250/B0B0B0/FFFFFF?text=صورة+غير+متاحة'}';">
                <div class="p-6 flex flex-col h-full">
                    <h3 class="text-xl font-bold text-emerald-green mb-2">${service.name}</h3>
                    <p class="text-dark-gray text-sm mb-4 line-clamp-3 flex-grow">${service.description}</p>
                    <div class="flex items-center justify-between mt-auto pt-4 border-t border-light-gray">
                        <span class="text-gold text-2xl font-extrabold">${service.price.toFixed(2)} ل.س</span>
                        <button class="bg-emerald-green text-white px-5 py-2 rounded-full hover:bg-opacity-90 transition duration-300 shadow-md view-details-btn" data-service-id="${service.id}">
                            عرض التفاصيل
                        </button>
                    </div>
                </div>
            `;
            return serviceCard;
        }

        // --- الدالة لعرض الخدمات في منطقة العرض ---
        function renderServicesDisplay() {
            console.log('Rendering services display...');
            servicesSection.innerHTML = '';
            currentView = 'services_view';

            if (services.length === 0) {
                servicesSection.innerHTML = `
                    <p class="col-span-full text-center text-lg text-medium-gray py-10 bg-white rounded-lg shadow-md">
                        لا توجد خدمات متاحة في هذا التصنيف حالياً.
                    </p>
                `;
                console.log('No services to display.');
                return;
            }

            services.forEach(service => {
                const card = createServiceCard(service);
                servicesSection.appendChild(card);
            });

            // إضافة مستمعي أحداث لأزرار "عرض التفاصيل"
            document.querySelectorAll('.view-details-btn').forEach(button => {
                button.addEventListener('click', (event) => {
                    const serviceId = event.target.dataset.serviceId;
                    showServiceDetailsModal(serviceId);
                });
            });
            console.log('Services rendered successfully.');
        }

        // --- الدالة لعرض تفاصيل الخدمة في نافذة منبثقة (Modal) ---
        function showServiceDetailsModal(serviceId) {
            console.log('Showing service details modal for service ID:', serviceId);
            const service = services.find(s => s.id === serviceId);
            if (service) {
                modalTitle.textContent = service.name;
                modalMessage.innerHTML = `
                    <p class="text-lg font-medium mb-2">${service.description}</p>
                    <p class="text-xl font-bold text-emerald-green mt-4">السعر: ${service.price.toFixed(2)} ل.س</p>
                    <img src="${service.image_url}" alt="${service.name}" class="w-full h-40 object-cover object-center mt-4 rounded-md"
                         onerror="this.onerror=null;this.src='${service.fallback_image_url || 'https://placehold.co/400x250/B0B0B0/FFFFFF?text=صورة+غير+متاحة'}';">
                `;
                modal.classList.remove('hidden');
                console.log('Modal displayed for service:', service.name);
            } else {
                console.warn('Service not found for modal display:', serviceId);
            }
        }

        // --- الدالة لإغلاق النافذة المنبثقة ---
        function closeModal() {
            modal.classList.add('hidden');
            console.log('Modal closed.');
        }

        // --- مستمع الأحداث الرئيسي لتبويبات التصنيفات ---
        categoryTabsContainer.addEventListener('click', async (event) => {
            const target = event.target;
            // التأكد أن العنصر الذي تم النقر عليه هو زر تبويب التصنيف
            if (target.classList.contains('category-tab')) {
                console.log('Category tab clicked:', target.textContent);
                // إزالة التحديد من جميع التبويبات
                document.querySelectorAll('.category-tab').forEach(btn => {
                    btn.classList.remove('bg-gold', 'text-emerald-green', 'shadow-md');
                    btn.classList.add('bg-light-gray', 'text-dark-gray');
                });
                // إضافة التحديد للتبويب الذي تم النقر عليه
                target.classList.remove('bg-light-gray', 'text-dark-gray');
                target.classList.add('bg-gold', 'text-emerald-green', 'shadow-md');

                const type = target.dataset.type; // نوع التبويب (مثل 'all_services', 'main_category', 'sub_category', 'back_to_main')
                const categoryId = target.dataset.categoryId; // معرف التصنيف
                const hasSubcategories = target.dataset.hasSubcategories === 'true'; // هل التصنيف الرئيسي لديه تصنيفات فرعية

                if (type === 'all_services') {
                    await fetchServicesByCategoryId('all');
                    renderServicesDisplay();
                } else if (type === 'back_to_main') {
                    await renderMainCategories();
                    // جعل تبويب "جميع الخدمات" نشطاً بعد العودة
                    const allServicesButton = categoryTabsContainer.querySelector('[data-type="all_services"]');
                    if (allServicesButton) {
                        allServicesButton.classList.remove('bg-light-gray', 'text-dark-gray');
                        allServicesButton.classList.add('bg-gold', 'text-emerald-green', 'shadow-md');
                    }
                } else if (type === 'main_category' && hasSubcategories) {
                    await renderSubcategories(categoryId);
                } else {
                    await fetchServicesByCategoryId(categoryId);
                    renderServicesDisplay();
                }
            }
        });

        // --- مستمع الأحداث لزر تعبئة الرصيد ---
        topUpButton.addEventListener('click', async () => {
            console.log('Top-up button clicked.');
            const amount = parseFloat(topUpAmountInput.value);

            if (isNaN(amount) || amount <= 0) {
                showModal('خطأ في الإدخال', 'الرجاء إدخال مبلغ صحيح وموجب لتعبئة الرصيد.');
                console.warn('Invalid top-up amount entered.');
                return;
            }

            // استدعاء API لتعبئة الرصيد
            try {
                const response = await fetch(`${API_BASE_URL}/api/topup`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ amount: amount })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'فشل في تعبئة الرصيد');
                }

                const result = await response.json();
                userBalance = result.new_balance; // تحديث الرصيد بناءً على استجابة الخادم
                updateUserInfoDisplay(); // تحديث الواجهة

                showModal('تمت تعبئة الرصيد بنجاح!', `
                    <p>تمت إضافة <span class="font-bold text-emerald-green">${amount.toFixed(2)} ل.س</span> إلى رصيدك.</p>
                    <p>رصيدك الجديد هو: <span class="font-bold text-gold">${userBalance.toFixed(2)} ل.س</span></p>
                    <p class="mt-2 text-sm text-medium-gray">تمت المعالجة بنجاح عبر نظام شام كاش الافتراضي.</p>
                `);
                topUpAmountInput.value = ''; // مسح حقل الإدخال
                console.log('Top-up successful, new balance:', userBalance);
            } catch (error) {
                console.error('Error during top-up:', error);
                showModal('خطأ في التعبئة', `حدث خطأ: ${error.message}. يرجى المحاولة مرة أخرى.`);
            }
        });

        // --- الدالة المساعدة لعرض النماذج (Modals) ---
        function showModal(title, message) {
            modalTitle.textContent = title;
            modalMessage.innerHTML = message;
            modal.classList.remove('hidden');
            console.log(`Modal shown: ${title}`);
        }

        // --- مستمع الأحداث لزر إغلاق النافذة المنبثقة ---
        modalCloseButton.addEventListener('click', closeModal);

        // --- مستمع الأحداث لإغلاق النافذة المنبثقة عند النقر خارجها ---
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal();
            }
        });

        // --- مستمع الأحداث لإغلاق النافذة المنبثقة عند الضغط على مفتاح Escape ---
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeModal();
            }
        });

        // --- وظائف التحميل الأولي للصفحة ---
        // يتم استدعاء هذه الوظائف عند تحميل الصفحة لأول مرة لتهيئة الواجهة
        // يتم جلب البيانات من الخادم الخلفي وتحديث الواجهة.
        document.addEventListener('DOMContentLoaded', async () => {
            console.log('DOMContentLoaded fired. Starting initial data fetch.');
            try {
                // إظهار مؤشر التحميل
                loadingIndicator.classList.remove('hidden');

                await fetchUserInfo();       // جلب معلومات المستخدم
                await fetchAllCategories();  // جلب جميع التصنيفات (الرئيسية والفرعية)
                await renderMainCategories(); // عرض التصنيفات الرئيسية في البداية
                console.log('Initial data fetch and rendering complete.');
            } catch (error) {
                console.error('Critical error during initial page load:', error);
                // إذا فشل أي من الطلبات الأولية بشكل كامل، نعرض رسالة عامة
                showModal('خطأ فادح في التحميل', 'حدث خطأ غير متوقع أثناء تحميل البيانات الأولية. يرجى مراجعة وحدة تحكم المتصفح للخبير.');
            } finally {
                // إخفاء مؤشر التحميل سواء نجحت العملية أم فشلت
                loadingIndicator.classList.add('hidden');
            }
        });
    </script>
</body>
</html>
"""
    return html_content

# تشغيل خادم Flask
if __name__ == '__main__':
    # لتشغيل الخادم:
    # 1. تأكد من أن ملف 'bot_data_backup_20250725_170311.db' موجود في نفس المجلد مع 'app.py'.
    # 2. افتح الطرفية (Terminal) في هذا المجلد وقم بتشغيل الأمر: flask run
    # سيتم تشغيل الخادم على http://127.0.0.1:5000 افتراضياً.
    app.run(debug=True)

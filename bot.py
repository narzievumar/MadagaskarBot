import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Loglarni sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokeni
TOKEN = "7237180635:AAEj_PRgvSSvhn9K_168Wpz703-lPIPG6W4"

# Xodimlar guruhining chat ID si (bu yerda o'zingizning guruh ID ni qo'ying)
GROUP_CHAT_ID = "-1002414904019"  # O'zingizning guruh ID ni bu yerga qo'ying, masalan: "-123456789"

# Yandex Maps API kaliti
YANDEX_API_KEY = "8cca7b48-8cf1-44ec-94fc-a5e4b22edb96"

# Foydalanuvchi ma'lumotlarini saqlash uchun lug'at
user_data = {}

# Buyurtma ID uchun global hisoblagich
order_counter = 0

# Holatlar (ConversationHandler uchun)
SELECTING_LANGUAGE, MAIN_MENU, MENU_CATEGORY, PRODUCT_SELECTION, ADDRESS_INPUT, PHONE_INPUT, PAYMENT_METHOD, CONFIRM_ORDER = range(8)

# Tillarni va matnlarni saqlash
texts = {
    "uz": {
        "welcome": "Assalomu alaykum! Madagaskar Land yetkazib berish xizmatiga xush kelibsiz.",
        "choose_language": "Tilni tanlang:",
        "menu": "🍽 Menyu",
        "cart": "🛒 Savat",
        "address": "📍 Manzil",
        "contact": "📞 Aloqa",
        "info": "ℹ️ Ma'lumot",
        "settings": "⚙️ Sozlamalar",
        "back": "🔙 Orqaga",
        "empty_cart": "Savatingiz bo'sh!",
        "cart_items": "🛒 Savatingizdagi mahsulotlar:",
        "total": "Umumiy summa:",
        "clear_cart": "🧹 Savatni tozalash",
        "checkout": "✅ Buyurtma berish",
        "enter_address": "Iltimos, yetkazib berish manzilingizni kiriting (faqat Navoiy shahar va Karmana tumani bo'yicha yetkazib berish mavjud):",
        "address_saved": "Manzil saqlandi:",
        "address_invalid": "Kechirasiz, faqat Navoiy shahar va Karmana tumani bo'yicha yetkazib berish mavjud. Iltimos, manzilingizni qayta kiriting:",
        "location_invalid": "Kechirasiz, bu joylashuv Navoiy shahar yoki Karmana tumanida emas. Iltimos, aniq manzil kiriting:",
        "location_error": "Joylashuvni aniqlashda xatolik yuz berdi. Iltimos, aniq manzil kiriting:",
        "enter_phone": "Iltimos, telefon raqamingizni kiriting yoki 'Raqamni ulashish' tugmasini bosing:",
        "phone_saved": "Telefon raqami saqlandi:",
        "contact_info": "📞 Biz bilan bog'lanish:",
        "phone": "☎️ Telefon:",
        "telegram": "📱 Telegram:",
        "website": "🌐 Veb-sayt:",
        "location": "📍 Manzil:",
        "about_bot": "ℹ️ Bot haqida ma'lumot:",
        "about_text": "Bu bot Madagaskar Land restorani uchun yaratilgan. Bot orqali siz quyidagilarni amalga oshirishingiz mumkin:\n\n- Menyu ko'rish va buyurtma berish\n- Savatingizni boshqarish\n- Manzil va aloqa ma'lumotlarini ko'rish",
        "select_language": "⚙️ Tilni tanlang:",
        "price": "💰 Narxi:",
        "description": "📝 Tavsif:",
        "add_to_cart": "🛒 Savatga qo'shish",
        "added_to_cart": "savatga qo'shildi!",
        "categories": "Kategoriyani tanlang:",
        "order_success": "Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        "order_to_group": "Yangi buyurtma (ID: {order_id}):\n\n{details}",
        "unknown_command": "Tushunarsiz buyruq. Iltimos, menyudan foydalaning.",
        "share_location": "📍 Joylashuvni yuborish",
        "share_contact": "📱 Raqamni ulashish",
        "location_saved": "Joylashuvingiz saqlandi! ✅",
        "order_details": "📋 Buyurtma tafsilotlari (ID: {order_id}):",
        "confirm_order": "✅ Buyurtmani tasdiqlash",
        "cancel_order": "❌ Bekor qilish",
        "select_payment": "To'lov usulini tanlang:",
        "payment_cash": "💵 Naqd pul",
        "payment_click": "💳 Click",
        "payment_payme": "💸 Payme",
        "payment": "To'lov usuli:"
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в службу доставки Madagaskar Land.",
        "choose_language": "Выберите язык:",
        "menu": "🍽 Меню",
        "cart": "🛒 Корзина",
        "address": "📍 Адрес",
        "contact": "📞 Контакты",
        "info": "ℹ️ Информация",
        "settings": "⚙️ Настройки",
        "back": "🔙 Назад",
        "empty_cart": "Ваша корзина пуста!",
        "cart_items": "🛒 Товары в вашей корзине:",
        "total": "Общая сумма:",
        "clear_cart": "🧹 Очистить корзину",
        "checkout": "✅ Оформить заказ",
        "enter_address": "Пожалуйста, введите адрес доставки (доставка доступна только по городу Навои и району Кармана):",
        "address_saved": "Адрес сохранен:",
        "address_invalid": "Извините, доставка доступна только по городу Навои и району Кармана. Пожалуйста, введите адрес снова:",
        "location_invalid": "Извините, это местоположение не находится в Навои или Кармане. Пожалуйста, введите точный адрес:",
        "location_error": "Ошибка при определении местоположения. Пожалуйста, введите точный адрес:",
        "enter_phone": "Пожалуйста, введите ваш номер телефона или нажмите кнопку 'Поделиться контактом':",
        "phone_saved": "Номер телефона сохранен:",
        "contact_info": "📞 Связаться с нами:",
        "phone": "☎️ Телефон:",
        "telegram": "📱 Телеграм:",
        "website": "🌐 Веб-сайт:",
        "location": "📍 Адрес:",
        "about_bot": "ℹ️ Информация о боте:",
        "about_text": "Этот бот создан для ресторана Madagaskar Land. С помощью бота вы можете:\n\n- Просматривать меню и делать заказы\n- Управлять корзиной\n- Просматривать адрес и контактную информацию",
        "select_language": "⚙️ Выберите язык:",
        "price": "💰 Цена:",
        "description": "📝 Описание:",
        "add_to_cart": "🛒 Добавить в корзину",
        "added_to_cart": "добавлен в корзину!",
        "categories": "Выберите категорию:",
        "order_success": "Ваш заказ принят! Мы свяжемся с вами в ближайшее время.",
        "order_to_group": "Новый заказ (ID: {order_id}):\n\n{details}",
        "unknown_command": "Непонятная команда. Пожалуйста, воспользуйтесь меню.",
        "share_location": "📍 Отправить местоположение",
        "share_contact": "📱 Поделиться контактом",
        "location_saved": "Ваше местоположение сохранено! ✅",
        "order_details": "📋 Детали заказа (ID: {order_id}):",
        "confirm_order": "✅ Подтвердить заказ",
        "cancel_order": "❌ Отменить",
        "select_payment": "Выберите способ оплаты:",
        "payment_cash": "💵 Наличные",
        "payment_click": "💳 Click",
        "payment_payme": "💸 Payme",
        "payment": "Способ оплаты:"
    },
    "en": {
        "welcome": "Hello! Welcome to Madagaskar Land delivery service.",
        "choose_language": "Choose language:",
        "menu": "🍽 Menu",
        "cart": "🛒 Cart",
        "address": "📍 Address",
        "contact": "📞 Contact",
        "info": "ℹ️ Info",
        "settings": "⚙️ Settings",
        "back": "🔙 Back",
        "empty_cart": "Your cart is empty!",
        "cart_items": "🛒 Items in your cart:",
        "total": "Total amount:",
        "clear_cart": "🧹 Clear cart",
        "checkout": "✅ Checkout",
        "enter_address": "Please enter your delivery address (delivery is available only in Navoi city and Karmana district):",
        "address_saved": "Address saved:",
        "address_invalid": "Sorry, delivery is available only in Navoi city and Karmana district. Please enter your address again:",
        "location_invalid": "Sorry, this location is not in Navoi city or Karmana district. Please enter your exact address:",
        "location_error": "Error determining location. Please enter your exact address:",
        "enter_phone": "Please enter your phone number or press 'Share Contact' button:",
        "phone_saved": "Phone number saved:",
        "contact_info": "📞 Contact us:",
        "phone": "☎️ Phone:",
        "telegram": "📱 Telegram:",
        "website": "🌐 Website:",
        "location": "📍 Location:",
        "about_bot": "ℹ️ About this bot:",
        "about_text": "This bot is created for Madagaskar Land restaurant. With this bot you can:\n\n- Browse menu and place orders\n- Manage your cart\n- View address and contact information",
        "select_language": "⚙️ Select language:",
        "price": "💰 Price:",
        "description": "📝 Description:",
        "add_to_cart": "🛒 Add to cart",
        "added_to_cart": "added to cart!",
        "categories": "Select a category:",
        "order_success": "Your order has been received! We will contact you soon.",
        "order_to_group": "New order (ID: {order_id}):\n\n{details}",
        "unknown_command": "Unknown command. Please use the menu.",
        "share_location": "📍 Share location",
        "share_contact": "📱 Share contact",
        "location_saved": "Your location has been saved! ✅",
        "order_details": "📋 Order details (ID: {order_id}):",
        "confirm_order": "✅ Confirm order",
        "cancel_order": "❌ Cancel",
        "select_payment": "Select payment method:",
        "payment_cash": "💵 Cash",
        "payment_click": "💳 Click",
        "payment_payme": "💸 Payme",
        "payment": "Payment method:"
    }
}

# Kategoriyalar
categories = {
    "uz": [["🍔 Burgerlar", "🍕 Pitsa"], ["🥗 Salatlar", "🍹 Ichimliklar"], ["🔙 Orqaga"]],
    "ru": [["🍔 Бургеры", "🍕 Пицца"], ["🥗 Салаты", "🍹 Напитки"], ["🔙 Назад"]],
    "en": [["🍔 Burgers", "🍕 Pizza"], ["🥗 Salads", "🍹 Drinks"], ["🔙 Back"]]
}

# Mahsulotlar
products = {
    "uz": {
        "🍔 Burgerlar": [
            {"name": "Chizburger", "price": 30000, "description": "Klassik chizburger, mol go'shti, pishloq, pomidor va salat bilan"},
            {"name": "Doubl burger", "price": 45000, "description": "Ikki qavatli burger, maxsus sous bilan"}
        ],
        "🍕 Pitsa": [
            {"name": "Margarita", "price": 60000, "description": "Pomidor, pishloq va rayhon bilan"},
            {"name": "Pepperoni", "price": 75000, "description": "Pepperoni kolbasa va pishloq bilan"}
        ],
        "🥗 Salatlar": [
            {"name": "Sezar salati", "price": 35000, "description": "Tovuq, romano salati, sarimsoq va pishloq bilan"},
            {"name": "Yunon salati", "price": 30000, "description": "Bodring, pomidor, zaytun va feta pishlog'i bilan"}
        ],
        "🍹 Ichimliklar": [
            {"name": "Coca-Cola", "price": 12000, "description": "0.5L shishada"},
            {"name": "Mineral suv", "price": 8000, "description": "0.5L shishada"}
        ]
    },
    "ru": {
        "🍔 Бургеры": [
            {"name": "Чизбургер", "price": 30000, "description": "Классический чизбургер с говядиной, сыром, помидорами и салатом"},
            {"name": "Дабл бургер", "price": 45000, "description": "Двойной бургер со специальным соусом"}
        ],
        "🍕 Пицца": [
            {"name": "Маргарита", "price": 60000, "description": "С помидорами, сыром и базиликом"},
            {"name": "Пепперони", "price": 75000, "description": "С колбасой пепперони и сыром"}
        ],
        "🥗 Салаты": [
            {"name": "Салат Цезарь", "price": 35000, "description": "С курицей, салатом романо, чесноком и сыром"},
            {"name": "Греческий салат", "price": 30000, "description": "С огурцами, помидорами, оливками и сыром фета"}
        ],
        "🍹 Напитки": [
            {"name": "Кока-Кола", "price": 12000, "description": "В бутылке 0.5Л"},
            {"name": "Минеральная вода", "price": 8000, "description": "В бутылке 0.5Л"}
        ]
    },
    "en": {
        "🍔 Burgers": [
            {"name": "Cheeseburger", "price": 30000, "description": "Classic cheeseburger with beef, cheese, tomatoes and lettuce"},
            {"name": "Double burger", "price": 45000, "description": "Double burger with special sauce"}
        ],
        "🍕 Pizza": [
            {"name": "Margherita", "price": 60000, "description": "With tomatoes, cheese and basil"},
            {"name": "Pepperoni", "price": 75000, "description": "With pepperoni sausage and cheese"}
        ],
        "🥗 Salads": [
            {"name": "Caesar salad", "price": 35000, "description": "With chicken, romaine lettuce, garlic and cheese"},
            {"name": "Greek salad", "price": 30000, "description": "With cucumber, tomatoes, olives and feta cheese"}
        ],
        "🍹 Drinks": [
            {"name": "Coca-Cola", "price": 12000, "description": "0.5L bottle"},
            {"name": "Mineral water", "price": 8000, "description": "0.5L bottle"}
        ]
    }
}

# Yandex Maps API orqali geolokatsiyadan manzil olish
def get_address_from_coords(lat, lon):
    url = f"https://geocode-maps.yandex.ru/1.x/?format=json&geocode={lon},{lat}&apikey={YANDEX_API_KEY}&lang=ru_RU"
    try:
        response = requests.get(url)
        data = response.json()
        if data["response"]["GeoObjectCollection"]["metaDataProperty"]["GeocoderResponseMetaData"]["found"] > 0:
            address = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
            return address
        else:
            return None
    except Exception as e:
        logger.error(f"Yandex API xatolik: {e}")
        return None

# /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_data:
        user_data[user_id] = {
            "language": None,
            "cart": [],
            "address": "",
            "phone": "",
            "payment_method": ""
        }
    
    welcome_message = (
        "Assalomu alaykum! Madagaskar Land yetkazib berish xizmatiga xush kelibsiz.\n"
        "Здравствуйте! Добро пожаловать в службу доставки Madagaskar Land.\n"
        "Hello! Welcome to Madagaskar Land delivery service."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])
    
    await update.message.reply_text(welcome_message, reply_markup=keyboard)
    return SELECTING_LANGUAGE

# Tugma bosilishini qayta ishlash
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("lang_"):
        language = data.split("_")[1]
        user_data[user_id]["language"] = language
        await show_main_menu(query.message, language)
        return MAIN_MENU
    
    elif data == "clear_cart":
        user_data[user_id]["cart"] = []
        language = user_data[user_id]["language"]
        await query.message.reply_text(texts[language]["empty_cart"])
        return MAIN_MENU
    
    elif data == "checkout":
        language = user_data[user_id]["language"]
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton(texts[language]["share_location"], request_location=True)],
             [KeyboardButton(texts[language]["back"])]],
            resize_keyboard=True
        )
        await query.message.reply_text(texts[language]["enter_address"], reply_markup=keyboard)
        return ADDRESS_INPUT
    
    elif data.startswith("add_"):
        language = user_data[user_id]["language"]
        _, category, product_index = data.split("_")
        product_index = int(product_index)
        product = products[language][category][product_index]
        user_data[user_id]["cart"].append(product)
        await query.message.reply_text(f"{product['name']} {texts[language]['added_to_cart']}")
        return MAIN_MENU
    
    elif data == "confirm_order":
        global order_counter
        order_counter += 1
        order_id = order_counter
        language = user_data[user_id]["language"]
        cart = user_data[user_id]["cart"]
        total = sum(item["price"] for item in cart)
        order_message = f"*{texts[language]['order_details'].format(order_id=order_id)}*\n\n"
        for i, product in enumerate(cart, 1):
            order_message += f"{i}. {product['name']} - {product['price']} so'm\n"
        order_message += f"\n*{texts[language]['total']}* {total} so'm\n"
        order_message += f"*{texts[language]['address']}* {user_data[user_id]['address']}\n"
        order_message += f"*{texts[language]['phone']}* {user_data[user_id]['phone']}\n"
        order_message += f"*{texts[language]['payment']}* {user_data[user_id]['payment_method']}"
        
        # Foydalanuvchiga xabar
        await query.message.reply_text(texts[language]["order_success"])
        
        # Xodimlar guruhiga yuborish
        try:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=texts[language]["order_to_group"].format(order_id=order_id, details=order_message),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xatolik: {e}")
        
        user_data[user_id]["cart"] = []
        await show_main_menu(query.message, language)
        return MAIN_MENU
    
    elif data == "cancel_order":
        language = user_data[user_id]["language"]
        await show_main_menu(query.message, language)
        return MAIN_MENU
    
    elif data in ["payment_cash", "payment_click", "payment_payme"]:
        language = user_data[user_id]["language"]
        payment_methods = {
            "payment_cash": texts[language]["payment_cash"],
            "payment_click": texts[language]["payment_click"],
            "payment_payme": texts[language]["payment_payme"]
        }
        user_data[user_id]["payment_method"] = payment_methods[data]
        
        # Buyurtma tasdiqlash
        cart = user_data[user_id]["cart"]
        total = sum(item["price"] for item in cart)
        order_message = f"*{texts[language]['order_details'].format(order_id='Temporary')}*\n\n"
        for i, product in enumerate(cart, 1):
            order_message += f"{i}. {product['name']} - {product['price']} so'm\n"
        order_message += f"\n*{texts[language]['total']}* {total} so'm\n"
        order_message += f"*{texts[language]['address']}* {user_data[user_id]['address']}\n"
        order_message += f"*{texts[language]['phone']}* {user_data[user_id]['phone']}\n"
        order_message += f"*{texts[language]['payment']}* {user_data[user_id]['payment_method']}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(texts[language]["confirm_order"], callback_data="confirm_order")],
            [InlineKeyboardButton(texts[language]["cancel_order"], callback_data="cancel_order")]
        ])
        await query.message.reply_text(order_message, reply_markup=keyboard, parse_mode="Markdown")
        return CONFIRM_ORDER

# Asosiy menyu ko'rsatish
async def show_main_menu(message, language):
    keyboard = ReplyKeyboardMarkup([
        [texts[language]["menu"], texts[language]["cart"]],
        [texts[language]["address"], texts[language]["contact"]],
        [texts[language]["info"], texts[language]["settings"]]
    ], resize_keyboard=True)
    
    await message.reply_text(
        f"{texts[language]['welcome']}\n\nMadagaskar Land",
        reply_markup=keyboard
    )

# Menyu kategoriyalari
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    keyboard = ReplyKeyboardMarkup(categories[language], resize_keyboard=True)
    await update.message.reply_text(texts[language]["categories"], reply_markup=keyboard)
    return MENU_CATEGORY

# Kategoriyadagi mahsulotlarni inline tugmalar sifatida ko'rsatish
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    category = update.message.text
    
    if category == texts[language]["back"]:
        await show_main_menu(update.message, language)
        return MAIN_MENU
    
    if category in products[language]:
        buttons = []
        for i, product in enumerate(products[language][category]):
            buttons.append([InlineKeyboardButton(
                f"{product['name']} - {product['price']} so'm",
                callback_data=f"add_{category}_{i}"
            )])
        keyboard = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            f"{category}\n\nMahsulotlarni tanlang:",
            reply_markup=keyboard
        )
        return PRODUCT_SELECTION
    
    await update.message.reply_text(texts[language]["unknown_command"])
    return MENU_CATEGORY

# Savatni ko'rsatish
async def cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    cart = user_data[user_id]["cart"]
    
    if not cart:
        await update.message.reply_text(texts[language]["empty_cart"])
        return MAIN_MENU
    
    total = sum(item["price"] for item in cart)
    message = f"*{texts[language]['cart_items']}*\n\n"
    for i, product in enumerate(cart, 1):
        message += f"{i}. {product['name']} - {product['price']} so'm\n"
    message += f"\n*{texts[language]['total']}* {total} so'm"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(texts[language]["clear_cart"], callback_data="clear_cart")],
        [InlineKeyboardButton(texts[language]["checkout"], callback_data="checkout")]
    ])
    
    await update.message.reply_text(message, reply_markup=keyboard, parse_mode="Markdown")
    return MAIN_MENU

# Manzil kiritish
async def address_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    
    if update.message.location:
        location = update.message.location
        lat, lon = location.latitude, location.longitude
        # Yandex Maps Geocoder orqali manzil olish
        address = get_address_from_coords(lat, lon)
        if address:
            address_lower = address.lower()
            # Navoiy yoki Karmana so'zlari manzilda borligini tekshirish
            if "navoiy" in address_lower or "karmana" in address_lower:
                user_data[user_id]["address"] = address
                await update.message.reply_text(f"{texts[language]['address_saved']} {address}")
            else:
                await update.message.reply_text(texts[language]["location_invalid"])
                return ADDRESS_INPUT
        else:
            await update.message.reply_text(texts[language]["location_error"])
            return ADDRESS_INPUT
    else:
        text = update.message.text
        if text == texts[language]["back"]:
            await show_main_menu(update.message, language)
            return MAIN_MENU
        text_lower = text.lower()
        if "navoiy" in text_lower or "karmana" in text_lower:
            user_data[user_id]["address"] = text
            await update.message.reply_text(f"{texts[language]['address_saved']} {text}")
        else:
            await update.message.reply_text(texts[language]["address_invalid"])
            return ADDRESS_INPUT
    
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(texts[language]["share_contact"], request_contact=True)],
         [KeyboardButton(texts[language]["back"])]],
        resize_keyboard=True
    )
    await update.message.reply_text(texts[language]["enter_phone"], reply_markup=keyboard)
    return PHONE_INPUT

# Telefon raqamini kiritish
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    
    if update.message.contact:
        phone = update.message.contact.phone_number
        user_data[user_id]["phone"] = phone
    else:
        text = update.message.text
        if text == texts[language]["back"]:
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton(texts[language]["share_location"], request_location=True)],
                 [KeyboardButton(texts[language]["back"])]],
                resize_keyboard=True
            )
            await update.message.reply_text(texts[language]["enter_address"], reply_markup=keyboard)
            return ADDRESS_INPUT
        user_data[user_id]["phone"] = text
    
    await update.message.reply_text(f"{texts[language]['phone_saved']} {user_data[user_id]['phone']}")
    
    # To'lov usulini tanlash
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(texts[language]["payment_cash"], callback_data="payment_cash")],
        [InlineKeyboardButton(texts[language]["payment_click"], callback_data="payment_click")],
        [InlineKeyboardButton(texts[language]["payment_payme"], callback_data="payment_payme")]
    ])
    await update.message.reply_text(texts[language]["select_payment"], reply_markup=keyboard)
    return PAYMENT_METHOD

# Aloqa ma'lumotlari
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    await update.message.reply_text(
        f"*{texts[language]['contact_info']}*\n\n"
        f"{texts[language]['phone']} +998 99 159 22 22\n"
        f"{texts[language]['telegram']} @madagaskarland\n"
        f"{texts[language]['website']} www.madagaskarland.uz\n"
        f"{texts[language]['location']} Navoiy sh., Karmana tumani",
        parse_mode="Markdown"
    )
    return MAIN_MENU

# Bot haqida ma'lumot
async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    await update.message.reply_text(
        f"*{texts[language]['about_bot']}*\n\n"
        f"{texts[language]['about_text']}",
        parse_mode="Markdown"
    )
    return MAIN_MENU

# Sozlamalar
async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = user_data[user_id]["language"]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ])
    await update.message.reply_text(texts[language]["select_language"], reply_markup=keyboard)
    return SELECTING_LANGUAGE

# Xabarlarni qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id not in user_data or user_data[user_id]["language"] is None:
        await start(update, context)
        return SELECTING_LANGUAGE
    
    language = user_data[user_id]["language"]
    text = update.message.text
    
    if text == texts[language]["menu"]:
        return await menu_handler(update, context)
    elif text == texts[language]["cart"]:
        return await cart_handler(update, context)
    elif text == texts[language]["address"]:
        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton(texts[language]["share_location"], request_location=True)],
             [KeyboardButton(texts[language]["back"])]],
            resize_keyboard=True
        )
        await update.message.reply_text(texts[language]["enter_address"], reply_markup=keyboard)
        return ADDRESS_INPUT
    elif text == texts[language]["contact"]:
        return await contact_handler(update, context)
    elif text == texts[language]["info"]:
        return await info_handler(update, context)
    elif text == texts[language]["settings"]:
        return await settings_handler(update, context)
    
    for row in categories[language]:
        if text in row:
            return await category_handler(update, context)
    
    await update.message.reply_text(texts[language]["unknown_command"])
    return MAIN_MENU

# Xatolarni qayta ishlash
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_user:
        user_id = update.effective_user.id
        if user_id in user_data and user_data[user_id]["language"]:
            language = user_data[user_id]["language"]
            await update.message.reply_text("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
        else:
            await update.message.reply_text("An error occurred. Please try again.")

# Botni ishga tushirish
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_LANGUAGE: [CallbackQueryHandler(button_handler, pattern="^lang_")],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
                        CallbackQueryHandler(button_handler)],
            MENU_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler)],
            PRODUCT_SELECTION: [CallbackQueryHandler(button_handler, pattern="^add_"),
                               MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            ADDRESS_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, address_handler),
                           MessageHandler(filters.LOCATION, address_handler)],
            PHONE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler),
                         MessageHandler(filters.CONTACT, phone_handler)],
            PAYMENT_METHOD: [CallbackQueryHandler(button_handler, pattern="^payment_")],
            CONFIRM_ORDER: [CallbackQueryHandler(button_handler, pattern="^(confirm_order|cancel_order)")]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    logger.info("Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Iltimos, BOT_TOKEN ni o'rnating!")
    if GROUP_CHAT_ID == "GURUH_CHAT_ID":
        raise ValueError("Iltimos, GROUP_CHAT_ID ni o'rnating!")
    if not YANDEX_API_KEY:
        raise ValueError("Iltimos, YANDEX_API_KEY ni o'rnating!")
    main()
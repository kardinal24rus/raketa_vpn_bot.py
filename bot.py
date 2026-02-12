"""
Telegram бот для поиска информации из открытых источников
"""
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from database import Database
from search_engine import SearchEngine

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_NAME, WAITING_ADDITIONAL_INFO, SELECTING_LANGUAGE = range(3)

# Инициализация
db = Database()
search_engine = SearchEngine()

# Тексты на разных языках
TEXTS = {
    'ru': {
        'welcome': """🕵️ Личность:
Трамп Дональд Анатольевич 04.06.1976 - ФИО
📲 Контакты:
79999688666 – номер телефона
79999688666@mail.ru – email
🚘 Транспорт:
В777ОК777 – номер автомобиля
XTA211440C5106924 – VIN автомобиля
💬 Социальные сети:
vk.com/shepert – Вконтакте
tiktok.com/@gazock – Tik Tok
instagram.com/fffggh – Instagram
ok.ru/profile/58460 – Одноклассники
📟 Telegram:
@spasibo, tg123456 – логин или ID
📄 Документы:
/vu 1234567890 – водительские права
/passport 1234567890 – паспорт
/snils 12345678901 – СНИЛС
/inn 123456789012 – ИНН
🌐 Онлайн-следы:
/tag хирург москва – поиск по телефонным книгам
sherlock.com или 1.1.1.1 – домен или IP
🏚 Недвижимость:
/adr Москва, Патриарши Пруды, 9к4, 94
77:01:0004042:6987 - кадастровый номер
🏢 Юридическое лицо:
/inn 2540214547 – ИНН
1107449004464 – ОГРН или ОГРНИП
📸 Отправьте лицо человека, чтобы попробовать найти его.""",
        'btn_partial_search': '🔍 Поиск по неполным данным',
        'btn_profile': '👤 Мой профиль',
        'btn_bots': '🤖 Мои боты',
        'btn_partner': '💰 Партнерская программа',
        'help_text': 'Справка на русском языке',
        'searching': '🔄 Поиск в открытых источниках...\n⏳ Это может занять до 60 секунд',
        'no_results': '❌ По указанным данным ничего не найдено.',
        'enter_name': '🔍 Введите ФИО человека (или имя и фамилию):\n\nПример: Иванов Иван Петрович',
    },
    'en': {
        'welcome': """🕵️ Identity:
Trump Donald Anatolyevich 04.06.1976 - Full Name
📲 Contacts:
79999688666 – phone number
79999688666@mail.ru – email
🚘 Transport:
В777ОК777 – car number
XTA211440C5106924 – VIN number
💬 Social Networks:
vk.com/shepert – VKontakte
tiktok.com/@gazock – Tik Tok
instagram.com/fffggh – Instagram
ok.ru/profile/58460 – Odnoklassniki
📟 Telegram:
@spasibo, tg123456 – username or ID
📄 Documents:
/vu 1234567890 – driver's license
/passport 1234567890 – passport
/snils 12345678901 – SNILS
/inn 123456789012 – INN
🌐 Online Traces:
/tag surgeon moscow – phone directory search
sherlock.com or 1.1.1.1 – domain or IP
🏚 Real Estate:
/adr Moscow, Patriarshie Prudy, 9k4, 94
77:01:0004042:6987 - cadastral number
🏢 Legal Entity:
/inn 2540214547 – INN
1107449004464 – OGRN or OGRNIP
📸 Send a person's face to try to find them.""",
        'btn_partial_search': '🔍 Search by Partial Data',
        'btn_profile': '👤 My Profile',
        'btn_bots': '🤖 My Bots',
        'btn_partner': '💰 Partner Program',
        'help_text': 'Help in English',
        'searching': '🔄 Searching in open sources...\n⏳ This may take up to 60 seconds',
        'no_results': '❌ No results found for the specified data.',
        'enter_name': '🔍 Enter the person\'s full name:\n\nExample: John Smith',
    }
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - выбор языка"""
    user = update.effective_user
    
    # Сохраняем пользователя в БД
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Кнопки выбора языка
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выберите язык / Choose language:",
        reply_markup=reply_markup
    )


async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка выбора языка"""
    query = update.callback_query
    await query.answer()
    
    # Сохраняем выбранный язык
    language = query.data.replace('lang_', '')
    context.user_data['language'] = language
    
    # Сохраняем в БД
    db.set_user_language(query.from_user.id, language)
    
    # Показываем приветственное сообщение
    await show_main_menu(query.message, context)


async def show_main_menu(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать главное меню"""
    lang = context.user_data.get('language', 'ru')
    texts = TEXTS[lang]
    
    # Создаем inline кнопки, прикрепленные к сообщению
    keyboard = [
        [InlineKeyboardButton(texts['btn_partial_search'], callback_data='menu_search')],
        [
            InlineKeyboardButton(texts['btn_profile'], callback_data='menu_profile'),
            InlineKeyboardButton(texts['btn_bots'], callback_data='menu_bots')
        ],
        [InlineKeyboardButton(texts['btn_partner'], callback_data='menu_partner')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем приветственное сообщение
    await message.reply_text(
        texts['welcome'],
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    lang = context.user_data.get('language', 'ru')
    
    help_texts = {
        'ru': (
            "🔍 Как искать информацию:\n\n"
            "1. Нажмите кнопку '🔍 Поиск по неполным данным'\n"
            "2. Введите данные в нужном формате\n"
            "3. Получите результаты поиска\n\n"
            "📊 Источники поиска:\n"
            "• Социальные сети (VK, OK, Instagram*)\n"
            "• Публичные базы данных\n"
            "• Открытые реестры\n"
            "• Поисковые системы\n\n"
            "⚠️ Важно:\n"
            "• Используются только легальные открытые источники\n"
            "• Чем больше информации укажете, тем точнее результат\n"
            "• Поиск может занять 30-60 секунд\n\n"
            "*продукты Meta, признанной экстремистской организацией в РФ"
        ),
        'en': (
            "🔍 How to search:\n\n"
            "1. Click the '🔍 Search by Partial Data' button\n"
            "2. Enter data in the required format\n"
            "3. Get search results\n\n"
            "📊 Search sources:\n"
            "• Social networks (VK, OK, Instagram*)\n"
            "• Public databases\n"
            "• Open registries\n"
            "• Search engines\n\n"
            "⚠️ Important:\n"
            "• Only legal open sources are used\n"
            "• More information = better results\n"
            "• Search may take 30-60 seconds\n\n"
            "*Meta products, recognized as extremist organization in Russia"
        )
    }
    
    await update.message.reply_text(help_texts[lang])


async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на inline кнопки меню"""
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('language', 'ru')
    
    if query.data == 'menu_search':
        # Начать поиск
        await query.message.reply_text(
            TEXTS[lang]['enter_name']
        )
        # Здесь можно добавить запуск ConversationHandler
    
    elif query.data == 'menu_profile':
        # Мой профиль
        user = query.from_user
        profile_text = {
            'ru': f"👤 Ваш профиль:\n\n"
                  f"ID: {user.id}\n"
                  f"Имя: {user.first_name or 'Не указано'}\n"
                  f"Username: @{user.username or 'Не указан'}\n"
                  f"Язык: {'🇷🇺 Русский' if lang == 'ru' else '🇬🇧 English'}",
            'en': f"👤 Your Profile:\n\n"
                  f"ID: {user.id}\n"
                  f"Name: {user.first_name or 'Not specified'}\n"
                  f"Username: @{user.username or 'Not specified'}\n"
                  f"Language: {'🇷🇺 Russian' if lang == 'ru' else '🇬🇧 English'}"
        }
        await query.message.reply_text(profile_text[lang])
    
    elif query.data == 'menu_bots':
        # Мои боты
        bots_text = {
            'ru': "🤖 Мои боты:\n\nЗдесь будет список ваших ботов.",
            'en': "🤖 My Bots:\n\nYour bots list will be here."
        }
        await query.message.reply_text(bots_text[lang])
    
    elif query.data == 'menu_partner':
        # Партнерская программа
        partner_text = {
            'ru': "💰 Партнерская программа:\n\nПриглашайте друзей и получайте бонусы!",
            'en': "💰 Partner Program:\n\nInvite friends and get bonuses!"
        }
        await query.message.reply_text(partner_text[lang])


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало поиска - запрос данных"""
    lang = context.user_data.get('language', 'ru')
    texts = TEXTS[lang]
    
    keyboard = [[InlineKeyboardButton("❌ Отмена" if lang == 'ru' else "❌ Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        texts['enter_name'],
        reply_markup=reply_markup
    )
    
    return WAITING_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение ФИО от пользователя"""
    name = update.message.text.strip()
    
    if len(name) < 3:
        await update.message.reply_text(
            "⚠️ Слишком короткое имя. Введите хотя бы имя и фамилию."
        )
        return WAITING_NAME
    
    # Сохраняем имя в контекст
    context.user_data['search_name'] = name
    
    keyboard = [
        [InlineKeyboardButton("✅ Искать сейчас", callback_data='search_now')],
        [InlineKeyboardButton("➕ Добавить информацию", callback_data='add_info')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Ищем: {name}\n\n"
        "Хотите добавить дополнительную информацию для более точного поиска?\n"
        "(город, возраст, место работы/учебы)",
        reply_markup=reply_markup
    )
    
    return WAITING_ADDITIONAL_INFO


async def receive_additional_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение дополнительной информации"""
    additional_info = update.message.text.strip()
    context.user_data['additional_info'] = additional_info
    
    keyboard = [
        [InlineKeyboardButton("🔍 Начать поиск", callback_data='search_now')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Дополнительная информация сохранена:\n{additional_info}\n\n"
        "Нажмите 'Начать поиск'",
        reply_markup=reply_markup
    )
    
    return WAITING_ADDITIONAL_INFO


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel':
        await query.edit_message_text("❌ Поиск отменен.")
        return ConversationHandler.END
    
    elif query.data == 'add_info':
        await query.edit_message_text(
            "📝 Введите дополнительную информацию:\n\n"
            "Например:\n"
            "• Город: Москва\n"
            "• Возраст: 25-30 лет\n"
            "• Работает в IT\n"
            "• Учился в МГУ"
        )
        return WAITING_ADDITIONAL_INFO
    
    elif query.data == 'search_now':
        await perform_search(query, context)
        return ConversationHandler.END
    
    return WAITING_ADDITIONAL_INFO


async def perform_search(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выполнение поиска"""
    search_name = context.user_data.get('search_name', '')
    additional_info = context.user_data.get('additional_info', '')
    
    # Показываем статус поиска
    status_message = await query.edit_message_text(
        "🔄 Поиск в открытых источниках...\n"
        "⏳ Это может занять до 60 секунд"
    )
    
    try:
        # Выполняем поиск
        results = await search_engine.search(search_name, additional_info)
        
        # Сохраняем запрос в БД
        user_id = query.from_user.id
        db.add_search_query(
            user_id=user_id,
            search_name=search_name,
            additional_info=additional_info,
            results_count=len(results)
        )
        
        # Формируем ответ
        if results:
            response = f"✅ Найдено результатов: {len(results)}\n\n"
            response += format_results(results)
        else:
            response = (
                "❌ По указанным данным ничего не найдено.\n\n"
                "Попробуйте:\n"
                "• Указать больше информации\n"
                "• Проверить правильность написания\n"
                "• Использовать другие варианты ФИО"
            )
        
        await status_message.edit_text(response, disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await status_message.edit_text(
            "❌ Произошла ошибка при поиске. Попробуйте позже."
        )


def format_results(results: list) -> str:
    """Форматирование результатов поиска"""
    formatted = ""
    
    for i, result in enumerate(results[:10], 1):  # Первые 10 результатов
        source = result.get('source', 'Unknown')
        name = result.get('name', 'N/A')
        url = result.get('url', '')
        info = result.get('info', '')
        
        formatted += f"{i}. 📍 {source}\n"
        formatted += f"   Имя: {name}\n"
        if info:
            formatted += f"   {info}\n"
        if url:
            formatted += f"   🔗 {url}\n"
        formatted += "\n"
    
    if len(results) > 10:
        formatted += f"\n... и еще {len(results) - 10} результатов"
    
    return formatted


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /history - история поисков"""
    user_id = update.effective_user.id
    history = db.get_user_history(user_id, limit=10)
    
    if not history:
        await update.message.reply_text("📋 История поисков пуста.")
        return
    
    response = "📋 История ваших поисков:\n\n"
    
    for i, record in enumerate(history, 1):
        date = record['created_at']
        name = record['search_name']
        results = record['results_count']
        
        response += f"{i}. {date}\n"
        response += f"   Поиск: {name}\n"
        response += f"   Результатов: {results}\n\n"
    
    await update.message.reply_text(response)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена текущей операции"""
    await update.message.reply_text("❌ Операция отменена.")
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ошибок"""
    logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    """Запуск бота"""
    # Получаем токен из переменной окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Обработчик поиска (ConversationHandler)
    search_conv = ConversationHandler(
        entry_points=[
            CommandHandler('search', start_search),
        ],
        states={
            WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name),
                CallbackQueryHandler(button_handler),
            ],
            WAITING_ADDITIONAL_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_additional_info),
                CallbackQueryHandler(button_handler),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CallbackQueryHandler(button_handler, pattern='^cancel$'),
        ],
    )
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(language_selected, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(handle_menu_buttons, pattern='^menu_'))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('history', history_command))
    application.add_handler(search_conv)
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

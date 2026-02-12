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
WAITING_NAME, WAITING_ADDITIONAL_INFO = range(2)

# Инициализация
db = Database()
search_engine = SearchEngine()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - приветствие"""
    user = update.effective_user
    
    # Сохраняем пользователя в БД
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я помогу найти информацию о людях из открытых источников.\n\n"
        "📋 Доступные команды:\n"
        "/search - Начать поиск\n"
        "/history - История запросов\n"
        "/help - Помощь\n\n"
        "⚖️ Работаю только с публичными данными в соответствии с законом."
    )
    
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help"""
    help_text = (
        "🔍 Как искать информацию:\n\n"
        "1. Используй команду /search\n"
        "2. Введи ФИО или имя/фамилию человека\n"
        "3. При необходимости добавь город, дату рождения, место работы\n\n"
        "📊 Источники поиска:\n"
        "• Социальные сети (VK, OK, Instagram*)\n"
        "• Публичные базы данных\n"
        "• Открытые реестры\n"
        "• Поисковые системы\n\n"
        "⚠️ Важно:\n"
        "• Используются только легальные открытые источники\n"
        "• Чем больше информации укажешь, тем точнее результат\n"
        "• Поиск может занять 30-60 секунд\n\n"
        "*продукты Meta, признанной экстремистской организацией в РФ"
    )
    
    await update.message.reply_text(help_text)


async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало поиска - запрос ФИО"""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 Введите ФИО человека (или имя и фамилию):\n\n"
        "Пример: Иванов Иван Петрович",
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
        entry_points=[CommandHandler('search', start_search)],
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

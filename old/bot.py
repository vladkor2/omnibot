import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота (замените на ваш)
BOT_TOKEN = "8552175450:AAHCU5F0QK2knfeuDpM3BEhaO5Lw91BeZ0w"

# Username пользователя, сообщения которого нужно записывать
TARGET_USERNAME = "Gelmgoltz"  # Замените на реальный username (без @)

# Файл для записи сообщений
LOG_FILE = "user_messages.txt"

def save_message(user_id: int, username: str, message_text: str):
    """Сохраняет сообщение в файл"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"User ID: {user_id}, Username: @{username}, Message: {message_text}\n")
    print(f"Сообщение от @{username} сохранено: {message_text}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все сообщения в чате"""
    user = update.message.from_user
    
    # Проверяем username (приводим к нижнему регистру для надежности)
    if user.username and user.username.lower() == TARGET_USERNAME.lower():
        message_text = update.message.text or "Нет текста"
        
        # Сохраняем сообщение
        save_message(user.id, user.username, message_text)

def main():
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчик для всех текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print(f"Бот запущен... Отслеживаем сообщения от @{TARGET_USERNAME}")
    application.run_polling()

if __name__ == "__main__":
    main()
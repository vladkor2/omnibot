import json
import logging
import re
from datetime import datetime, timedelta, time as dt_time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from telegram.ext import JobQueue

# --- Configuration ---
CONFIG_FILE = 'secrets.json'
DATA_FILE = 'sleep_data.json' # Файл для хранения данных о сне
TOKEN_KEY = 'tg_bot_token'
USERNAME_KEY = 'target_username'
CHAT_IDS_KEY = 'chat_ids'

# --- Global Variables ---
TARGET_USERNAME = None
TARGET_USER_ID = None
BROADCAST_CHAT_IDS = []

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def load_config():
    global TARGET_USERNAME, BROADCAST_CHAT_IDS
    try:
        # Добавим отладочную информацию
        logger.info(f"Попытка открыть файл конфигурации: {CONFIG_FILE}")
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"Содержимое файла: {content}") # Логгируем содержимое
            config = json.loads(content) # Явно вызываем json.loads
        logger.info(f"JSON успешно распознан: {config}")

        # Проверим наличие ключей
        if TOKEN_KEY not in config:
            raise KeyError(f"Ключ '{TOKEN_KEY}' не найден в {CONFIG_FILE}")
        if USERNAME_KEY not in config:
            raise KeyError(f"Ключ '{USERNAME_KEY}' не найден в {CONFIG_FILE}")
        if CHAT_IDS_KEY not in config:
            raise KeyError(f"Ключ '{CHAT_IDS_KEY}' не найден в {CONFIG_FILE}")

        token = config[TOKEN_KEY]
        TARGET_USERNAME = config[USERNAME_KEY].lstrip('@')
        BROADCAST_CHAT_IDS = config[CHAT_IDS_KEY] # Не используем get, чтобы сразу получить KeyError если ключа нет
        if not isinstance(BROADCAST_CHAT_IDS, list):
            raise ValueError(f"Ключ '{CHAT_IDS_KEY}' должен содержать список ID чатов.")
        
        logger.info(f"Конфигурация успешно загружена. Token: {'*' * len(token)}, Username: {TARGET_USERNAME}, Chat IDs: {BROADCAST_CHAT_IDS}")
        return token
    except FileNotFoundError:
        logger.error(f"Файл {CONFIG_FILE} не найден!")
        exit(1)
    except KeyError as e:
        logger.error(f"Ошибка ключа: {e}")
        logger.error("Пожалуйста, проверьте структуру файла secrets.json")
        exit(1)
    except ValueError as e:
        logger.error(f"Ошибка значения: {e}")
        exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        logger.error("Пожалуйста, проверьте синтаксис файла secrets.json")
        exit(1)

def load_sleep_data():
    """Загружает данные о сне из файла."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info(f"Файл {DATA_FILE} не найден, создаётся новый.")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Ошибка чтения {DATA_FILE}, создаётся новый.")
        return {}

def save_sleep_data(data):
    """Сохраняет данные о сне в файл."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def set_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Настраивает ежедневные напоминания."""
    now = datetime.now()
    first_reminder_time = dt_time(9, 30)
    next_run = now.replace(hour=first_reminder_time.hour, minute=first_reminder_time.minute, second=0, microsecond=0)
    if now.time() > first_reminder_time:
        next_run += timedelta(days=1)
    if next_run < now:
        next_run = now.replace(hour=9, minute=30, second=0, microsecond=0) + timedelta(days=1)
        
    context.job_queue.run_daily(
        callback=send_reminder,
        time=first_reminder_time,
        days=tuple(range(7)),
        name="daily_reminder"
    )
    logger.info("Ежедневное напоминание запланировано.")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет первое напоминание пользователю."""
    if TARGET_USER_ID is None:
        logger.warning("TARGET_USER_ID не установлен, невозможно отправить напоминание.")
        return

    await context.bot.send_message(
        chat_id=TARGET_USER_ID,
        text=f"@{TARGET_USERNAME}, напиши, во сколько ты лег и во сколько встал сегодня.\n\nФормат: `Лёг: HH:MM, Встал: HH:MM`\n(например, Лёг: 23:15, Встал: 07:45)"
    )
    logger.info(f"Отправлено первое напоминание пользователю {TARGET_USERNAME}.")

    for hour in range(10, 24):
        job_time = dt_time(hour, 0)
        job_datetime = datetime.combine(datetime.now().date(), job_time)
        if job_datetime <= datetime.now():
             job_datetime += timedelta(days=1)
        context.job_queue.run_once(
            callback=send_reminder_follow_up,
            when=job_datetime,
            data={'hour': hour},
            name=f"follow_up_{hour}"
        )

async def send_reminder_follow_up(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет повторное напоминание пользователю."""
    if TARGET_USER_ID is None:
        logger.warning("TARGET_USER_ID не установлен, невозможно отправить повторное напоминание.")
        return

    hour = context.job.data['hour']
    await context.bot.send_message(chat_id=TARGET_USER_ID, text=f"@{TARGET_USERNAME}, пора сообщить режим сна! (Повторное напоминание в {hour}:00)")
    logger.info(f"Отправлено повторное напоминание пользователю {TARGET_USERNAME} в {hour}:00.")

async def broadcast_message(context: ContextTypes.DEFAULT_TYPE, text: str):
    """Транслирует сообщение во все группы из списка BROADCAST_CHAT_IDS."""
    for chat_id in BROADCAST_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            logger.info(f"Сообщение транслировано в чат {chat_id}.")
        except Exception as e:
            logger.error(f"Не удалось отправить в чат {chat_id}: {e}")

# --- Command Handlers ---
async def check_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь целевым. Возвращает True, если да."""
    user = update.effective_user
    if user.id == TARGET_USER_ID or (user.username and user.username.lower() == TARGET_USERNAME.lower()):
        TARGET_USER_ID = user.id
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    if not await check_target_user(update, context):
        return
    await update.message.reply_text("Привет! Бот запомнит вас как целевого пользователя.")

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /id."""
    if not await check_target_user(update, context):
        return
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"ID этого чата: <code>{chat_id}</code>")

# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает входящие сообщения только от целевого пользователя."""
    user = update.effective_user
    message = update.effective_message

    if not await check_target_user(update, context):
        return

    # Получаем текст сообщения
    raw_text = message.text
    if not raw_text:
        # Игнорируем сообщения без текста (например, фото, голосовые)
        return

    # Отменяем все запланированные напоминания на текущий день
    follow_up_jobs = [job for job in context.job_queue.jobs() if job.name and job.name.startswith("follow_up_")]
    today = datetime.now().date()
    for job in follow_up_jobs:
        if isinstance(job.next_t, datetime) and job.next_t.date() == today:
            job.schedule_removal()
            logger.info(f"Отменено повторное напоминание '{job.name}' после получения ответа.")

    # --- Парсинг сообщения ---
    # Паттерн для поиска "Лёг: HH:MM, Встал: HH:MM"
    # (?i) - нечувствительно к регистру
    # \d{1,2} - 1 или 2 цифры для часа/минуты
    pattern = r"(?i)\bлёг:\s*(\d{1,2}):(\d{2})\s*,\s*встал:\s*(\d{1,2}):(\d{2})\b"
    match = re.search(pattern, raw_text)

    if match:
        sleep_hour, sleep_min, wake_hour, wake_min = match.groups()
        sleep_time_str = f"{int(sleep_hour):02d}:{sleep_min}"
        wake_time_str = f"{int(wake_hour):02d}:{wake_min}"

        # Сохраняем данные
        today_str = datetime.now().strftime('%Y-%m-%d')
        data = load_sleep_data()
        data[today_str] = {
            "user_id": user.id,
            "username": user.username,
            "went_to_bed": sleep_time_str,
            "woke_up": wake_time_str,
            "timestamp": datetime.now().isoformat()
        }
        save_sleep_data(data)
        logger.info(f"Сохранены данные о сне для {today_str}: Лёг {sleep_time_str}, Встал {wake_time_str}")

        # Формируем сообщение для рассылки
        broadcast_msg = (
            f"📊 <b>Отчёт о сне @{user.username or user.first_name}</b>\n"
            f"<b>Дата:</b> {today_str}\n"
            f"<b>Лёг:</b> {sleep_time_str}\n"
            f"<b>Встал:</b> {wake_time_str}"
        )
    else:
        # Если формат не распознан, отправляем как есть и логгируем
        logger.warning(f"Сообщение от {user.username or user.id} не соответствует формату: '{raw_text}'")
        broadcast_msg = f"⚠️ <b>Предупреждение:</b> @{user.username or user.first_name} прислал(а) сообщение в неверном формате: \n<code>{raw_text}</code>"

    # Рассылаем сообщение
    await broadcast_message(context, broadcast_msg)

if __name__ == '__main__':
    TOKEN = load_config()
    application = ApplicationBuilder().token(TOKEN).job_queue(JobQueue()).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.job_queue.run_once(set_daily_reminder, when=1)

    logger.info("Бот запущен.")
    application.run_polling()
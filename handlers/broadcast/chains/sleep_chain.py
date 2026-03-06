from ..base_chain import BaseChain
from ..steps import ButtonStep
import json
from datetime import datetime
from babel.dates import format_date

def years_since_simple(date_str, date_format="%d.%m.%Y"):
    """Вычисляет количество лет с точностью до сотых"""
    start_date = datetime.strptime(date_str, date_format)
    end_date = datetime.now()
    
    # Разница в днях
    days_diff = (end_date - start_date).days
    
    # Переводим в годы (учитывая високосные)
    years = days_diff / 365.25
    
    return round(years, 2)



class SleepChain(BaseChain):
    """Команда /sleep - трекер сна"""
    
    command = "sleep"
    description = "😴 Записать время сна"
    
    steps = [
        ButtonStep(
            name="hour_first",
            prompt="🛏 Во сколько лег? (выбери час):",
            buttons=[(f"{h:02d}", f"hour_{h}") for h in range(0, 24, 1)]
        ),
        ButtonStep(
            name="minute_first",
            prompt="Выбери минуты:",
            buttons=[
                ("00", "minute_0"), ("10", "minute_10"), ("20", "minute_20"),
                ("30", "minute_30"), ("40", "minute_40"), ("50", "minute_50")
            ]
        ),
        ButtonStep(
            name="hour_second",
            prompt="🛏 Во сколько встал? (выбери час):",
            buttons=[(f"{h:02d}", f"hour_{h}") for h in range(0, 24, 1)]
        ),
        ButtonStep(
            name="minute_second",
            prompt="Выбери минуты:",
            buttons=[
                ("00", "minute_0"), ("10", "minute_10"), ("20", "minute_20"),
                ("30", "minute_30"), ("40", "minute_40"), ("50", "minute_50")
            ]
        ),
        ButtonStep(
            name="feeling",
            prompt="Как самочувствие после сна?",
            buttons=[
                ("😊 Отлично", "feeling_good"),
                ("😐 Нормально", "feeling_ok"),
                ("😫 Плохо", "feeling_bad")
            ]
        )
    ]
    
    async def execute(self, update, context):
        """Отправка данных о сне в чаты рассылки"""
        data = context.user_data['chain_data']
        
        # Парсим данные
        hour_first = int(data['hour_first'].replace('hour_', ''))
        minute_first = int(data['minute_first'].replace('minute_', ''))
        hour_second = int(data['hour_second'].replace('hour_', ''))
        minute_second = int(data['minute_second'].replace('minute_', ''))
        feeling = data['feeling'].replace('feeling_', '')
        
        sleep_time_first = f"{hour_first:02d}:{minute_first:02d}"
        sleep_time_second = f"{hour_second:02d}:{minute_second:02d}"

        # Переводим всё в минуты от полуночи
        sleep_minutes = hour_first * 60 + minute_first
        wake_minutes = hour_second * 60 + minute_second

        # Вычисляем разницу
        if wake_minutes >= sleep_minutes:
            # Проснулись в тот же день (после полуночи)
            diff_minutes = wake_minutes - sleep_minutes
        else:
            # Проснулись после полуночи, но в пределах 13 часов
            diff_minutes = (24*60 - sleep_minutes) + wake_minutes

        # Переводим обратно в часы и минуты
        hours = diff_minutes // 60
        minutes = diff_minutes % 60

        sleep_duration = f"{hours}ч {minutes}мин"
        
        # Словарь для перевода feeling на русский
        feeling_text = {
            'good': '😊 Отлично',
            'ok': '😐 Нормально',
            'bad': '😫 Плохо'
        }.get(feeling, feeling)

        date_str = format_date(datetime.now(), format='d MMMM y', locale='ru')
        age = years_since_simple("10.09.2002")
        
        # Формируем сообщение для рассылки
        report_message = (
            f"📅 #ВД {date_str}, мне {age}\n"
            f"🛏 Время отхода ко сну: `{sleep_time_first}`\n"
            f"⏰ Время подъема: `{sleep_time_second}`\n"
            f"💤 Время сна `{sleep_duration}`\n"
            f"📊 Самочувствие после сна: {feeling_text}\n"
        )
        
        # Получаем список чатов для рассылки
        chats = context.bot_data.get('broadcast_chats', [])
        
        if not chats:
            # Если чатов нет, просто сохраняем локально
            try:
                with open('sleep_data.json', 'r') as f:
                    records = json.load(f)
            except:
                records = []
            
            records.append({
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'sleep_time': sleep_time_first,
                'feeling': feeling
            })
            
            with open('sleep_data.json', 'w') as f:
                json.dump(records, f, indent=2)
            
            return f"✅ Данные сохранены локально (нет чатов для рассылки)\n\n{report_message}"
        
        # Рассылаем отчет по чатам
        success = 0
        failed = 0
        
        for chat_id in chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=report_message,
                    parse_mode='Markdown'
                )
                success += 1
            except Exception as e:
                failed += 1
                print(f"Ошибка отправки сна в чат {chat_id}: {e}")
        
        # Сохраняем в файл (на всякий случай)
        try:
            with open('sleep_data.json', 'r') as f:
                records = json.load(f)
        except:
            records = []
        
        records.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'sleep_time': sleep_time_first,
            'feeling': feeling
        })
        
        with open('sleep_data.json', 'w') as f:
            json.dump(records, f, indent=2)
        
        # Формируем отчет о рассылке
        result = f"✅ Данные сохранены и разосланы!\n\n{report_message}\n\n"
        result += f"📊 Статистика рассылки:\n✓ Успешно: {success}\n✗ Ошибок: {failed}"
        
        return result
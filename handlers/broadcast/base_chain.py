from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from functools import wraps
from ..common import private
from .steps import StepType, ConfirmStep
import logging

logger = logging.getLogger(__name__)

class BaseChain:
    """Базовый класс для всех цепочек команд"""
    
    # Поля для переопределения в наследниках
    command = None           # /r, /r2, /sleep
    description = None       # Описание для /help
    steps = []               # Список шагов (без ConfirmStep - добавится автоматически)
    
    def __init__(self):
        self.states = {}
        self._build_states()
    
    def _build_states(self):
        """Строит состояния для ConversationHandler"""
        # Добавляем ConfirmStep в конец, если его нет
        all_steps = self.steps.copy()
        if not any(step.type == StepType.CONFIRM for step in all_steps):
            all_steps.append(ConfirmStep())
        
        # Создаем состояния для каждого шага
        for i, step in enumerate(all_steps):
            state_num = i + 1
            self.states[state_num] = step
    
    @property
    def total_steps(self):
        return len(self.states)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало цепочки"""
        # Инициализируем данные пользователя
        context.user_data['chain_data'] = {}
        context.user_data['current_step'] = 1
        
        first_step = self.states[1]
        markup = first_step.get_markup()
        
        await update.message.reply_text(
            f"🔄 {first_step.prompt}",
            reply_markup=markup
        )
        return 1  # первое состояние
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода"""
        current_step_num = context.user_data.get('current_step', 1)
        step = self.states[current_step_num]
        
        # Валидация если есть
        if step.validator:
            is_valid, error_msg = step.validator(update.message.text)
            if not is_valid:
                await update.message.reply_text(error_msg or step.error_message)
                return current_step_num  # остаемся на том же шаге
        
        # Сохраняем ответ
        context.user_data['chain_data'][step.name] = update.message.text
        
        # Переходим к следующему шагу
        return await self._go_to_next_step(update, context, current_step_num)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        current_step_num = context.user_data.get('current_step', 1)
        step = self.states[current_step_num]
        
        # Сохраняем выбор
        context.user_data['chain_data'][step.name] = query.data
        
        # Если это подтверждение
        if step.type == StepType.CONFIRM:
            if query.data == "confirm_yes":
                # Всё ок - отправляем
                result = await self.execute(update, context)
                await query.edit_message_text(result or "✅ Готово!")
                context.user_data.clear()
                return ConversationHandler.END
            else:  # confirm_again
                # Начинаем заново
                context.user_data['chain_data'] = {}
                context.user_data['current_step'] = 1
                first_step = self.states[1]
                markup = first_step.get_markup()
                await query.edit_message_text(
                    f"🔄 {first_step.prompt}",
                    reply_markup=markup
                )
                return 1
        
        # Обычный шаг с кнопками - идем дальше
        return await self._go_to_next_step(update, context, current_step_num, is_callback=True)
    
    async def _go_to_next_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                              current_step: int, is_callback: bool = False):
        """Переход к следующему шагу"""
        next_step_num = current_step + 1
        
        if next_step_num <= self.total_steps:
            # Есть следующий шаг
            context.user_data['current_step'] = next_step_num
            next_step = self.states[next_step_num]
            markup = next_step.get_markup()
            
            message = f"📌 {next_step.prompt}"
            
            if is_callback:
                await update.callback_query.edit_message_text(message, reply_markup=markup)
            else:
                await update.message.reply_text(message, reply_markup=markup)
            
            return next_step_num
        else:
            # Если вдруг нет ConfirmStep (на всякий случай)
            context.user_data.clear()
            return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции"""
        context.user_data.clear()
        await update.message.reply_text("❌ Операция отменена.")
        return ConversationHandler.END
    
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Метод, который нужно переопределить в наследниках
        Получает данные из context.user_data['chain_data']
        Должен вернуть текст результата
        """
        raise NotImplementedError("Каждая цепочка должна реализовать метод execute")
    
    def get_conversation_handler(self):
        """Создает ConversationHandler для этой цепочки"""
        from telegram.ext import ConversationHandler
        
        # Словарь состояний
        states = {}
        for state_num, step in self.states.items():
            if step.type == StepType.TEXT:
                states[state_num] = [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)]
            elif step.type in [StepType.BUTTON, StepType.CONFIRM]:
                # Для кнопок создаем обработчик callback'ов
                states[state_num] = [CallbackQueryHandler(self.handle_callback)]
        
        return ConversationHandler(
            entry_points=[CommandHandler(self.command, private(self.start))],
            states=states,
            fallbacks=[CommandHandler("cancel", private(self.cancel))],
            per_message=False
        )
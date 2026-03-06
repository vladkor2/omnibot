from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class StepType(Enum):
    TEXT = "text"           # Ввод текста
    BUTTON = "button"        # Выбор из кнопок
    CONFIRM = "confirm"      # Подтверждение (ок/again)
    MEDIA = "media"         # Загрузка медиа (фото/видео)

@dataclass
class Step:
    """Базовый класс шага"""
    name: str                    # Имя поля в user_data
    type: StepType               # Тип шага
    prompt: str                   # Вопрос пользователю
    buttons: List[Tuple[str, str]] = None  # Список (текст, callback_data)
    validator: Optional[Callable] = None   # Валидатор ввода
    error_message: str = "❌ Неверный ввод. Попробуйте снова."
    
    def get_markup(self):
        """Создает клавиатуру для шага"""
        if self.buttons:
            keyboard = []
            for text, callback in self.buttons:
                keyboard.append([InlineKeyboardButton(text, callback_data=callback)])
            return InlineKeyboardMarkup(keyboard)
        return None

class TextStep(Step):
    """Шаг для ввода текста"""
    def __init__(self, name: str, prompt: str, validator=None, error_message=None):
        super().__init__(
            name=name,
            type=StepType.TEXT,
            prompt=prompt,
            validator=validator,
            error_message=error_message or "❌ Некорректный текст. Попробуйте снова."
        )

class ButtonStep(Step):
    """Шаг для выбора из кнопок"""
    def __init__(self, name: str, prompt: str, buttons: List[Tuple[str, str]]):
        super().__init__(
            name=name,
            type=StepType.BUTTON,
            prompt=prompt,
            buttons=buttons
        )

class ConfirmStep(Step):
    """Финальный шаг подтверждения"""
    def __init__(self):
        super().__init__(
            name="confirmation",
            type=StepType.CONFIRM,
            prompt="✅ Всё верно?",
            buttons=[
                ("✅ Да, отправить", "confirm_yes"),
                ("🔄 Заполнить заново", "confirm_again")
            ]
        )
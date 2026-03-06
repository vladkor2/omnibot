import json
from pathlib import Path

class Config:
    """Класс для хранения всей конфигурации"""
    
    def __init__(self):
        self.secrets = {}
        self.settings = {}
        self._load_configs()
    
    def _load_configs(self):
        """Загружает все конфигурационные файлы"""
        root_dir = Path(__file__).parent
        
        # Загружаем secrets.json
        secrets_path = root_dir / 'secrets.json'
        if secrets_path.exists():
            with open(secrets_path, 'r', encoding='utf-8') as f:
                self.secrets = json.load(f)
        else:
            raise FileNotFoundError("secrets.json не найден!")
        
        # Загружаем config.json
        config_path = root_dir / 'config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            # Создаем с настройками по умолчанию
            self.settings = {
                "bot": {
                    "name": "MyPersonalBot",
                    "debug": True,
                    "admin_id": 0  # Замените на свой ID
                }
            }
            self.save_config()
    
    def save_config(self):
        """Сохраняет настройки"""
        config_path = Path(__file__).parent / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
    
    @property
    def tg_bot_token(self):
        return self.secrets.get('tg_bot_token')
    
    @property
    def admin_id(self):
        return self.settings.get('bot', {}).get('admin_id', 0)
    
    @property
    def debug(self):
        return self.settings.get('bot', {}).get('debug', False)

# Создаем единственный экземпляр при первом импорте
config = Config()
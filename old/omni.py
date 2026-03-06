import os
import json
from typing import Dict, Callable, Any, Optional



class MManager():
    def __init__(self, config_path = "./config.json", secrets_path = "./secrets.json"):
        # Saving files paths
        self.config_path = config_path
        self.secrets_path = secrets_path
        

        # Loading config file
        self.config = None
        self.load_config()

        # Loading secrets file
        self.bot_token = None
        self.target_username = None
        self.credentials_path = None
        self.load_secrets()

        # Dict of command handlers
        self._handlers: Dict[str, Callable] = {}


    def load_config(self):
        """ Loading config file """
        try:
            with open(self.config_path) as f:
                self.config = json.load(f)
                print("The config has been read")
                print(self.config)
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            self.config = None
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in config file: {e}")
            self.config = None
            return None
        except Exception as e:
            print(f"Unexpected error reading config: {e}")
            self.config = None
            return None

    def load_secrets(self):
        """ Loading secrets file """
        try:
            with open(self.secrets_path) as f:
                secrets = json.load(f)
                self.bot_token = secrets['tg_bot_token']
                self.target_username = secrets['target_username']
                self.credentials_path = secrets['credentials_path']
                print("The secrets have been read")
        except FileNotFoundError:
            print(f"Secrets file not found: {self.secrets_path}")
            self.bot_token = None
            self.target_username = None
            self.credentials_path = None
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in secrets file: {e}")
            self.bot_token = None
            self.target_username = None
            self.credentials_path = None
            return None
        except KeyError as e:
            print(f"Missing required key in secrets file: {e}")
            self.bot_token = None
            self.target_username = None
            self.credentials_path = None
            return None
        except Exception as e:
            print(f"Unexpected error reading secrets: {e}")
            self.bot_token = None
            self.target_username = None
            self.credentials_path = None
            return None

    def register_handler(self, name: str, handler: Callable) -> None:
        """Регистрация обработчика"""
        if name in self._handlers:
            raise ValueError(f"Handler '{name}' already registered")
        
        self._handlers[name] = handler
        print(f"Registered handler: {name}")

    def list_handlers(self) -> list:
        """Список зарегистрированных обработчиков"""
        return list(self._handlers.keys())

    def exe(self, target: str, command: str, **kwargs) -> dict:
        """Выполнение команды через менеджер"""
        if target not in self._handlers:
            return {
                "status": "error", 
                "message": f"Unknown target: {target}",
                "available_handlers": list(self._handlers.keys())
            }
        
        try:
            # Вызываем обработчик с командой и аргументами
            result = self._handlers[target](command, **kwargs)
            
            # Стандартизируем ответ
            if isinstance(result, dict) and "status" in result:
                return result
            else:
                return {"status": "success", "data": result}
                
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Handler execution failed: {str(e)}",
                "target": target,
                "command": command
            }


class TelegramBot():
    def __init__(self, mm: MManager):
        self.mm = mm

    def run(self):
        self.mm.exe("gsheets", "add_data", user_id=17, data="hello world")

        self.mm.exe("gsheets", "add_data", user_id=18)

        self.mm.exe("gsheets0", "add_data", user_id=19, data="hello world")

        self.mm.exe("gsheets", "add_data0", user_id=20, data="hello world")

        result = self.mm.exe("gsheets", "add_data", user_id=21, data="hello world")

        print(result)
        print(result['status'])


class GoogleSheets():
    def __init__(self, mm: MManager):
        self.mm = mm
        self.mm.register_handler("gsheets", self.process_request)

    def process_request(self, command, **kwargs):  
        command_handlers = {
            "add_data": self._add_data
        }
        
        if command not in command_handlers:
            return {"status": "error", "message": f"Unknown command: {command}"}
        
        handler = command_handlers[command]
        return handler(**kwargs)

        
    def _add_data(self, **kwargs):
        required = ['user_id', 'data']
        if not all(req in kwargs for req in required):
            print("error in arguments")
            return {"status": "error", "message": f"Missing: {required}"}
        
        user_id = kwargs['user_id']
        data = kwargs['data']
        print(f"{user_id} add '{data}'")
        return {"status": "success", "message": "fo"}


def main():
    mm = MManager()
    tgbot = TelegramBot(mm)
    gsheets = GoogleSheets(mm)

    tgbot.run()




if __name__ == "__main__":
    main()
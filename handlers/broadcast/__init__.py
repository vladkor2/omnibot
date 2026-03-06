from .chains.r_chain import RChain
from .chains.sleep_chain import SleepChain

# Список всех доступных цепочек
CHAINS = [
    RChain,
    SleepChain,
]

def get_handlers():
    """Возвращает все ConversationHandler'ы"""
    handlers = []
    for chain_class in CHAINS:
        chain = chain_class()
        handlers.append(chain.get_conversation_handler())
    return handlers

def get_commands_description():
    """Возвращает описания команд для /help"""
    return "\n".join([
        f"/{chain_class.command} - {chain_class.description}"
        for chain_class in CHAINS
    ])
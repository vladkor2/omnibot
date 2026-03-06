FROM ubuntu:20.04

# Устанавливаем переменные окружения для избежания интерактивных диалогов
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/bin/python

# Устанавливаем полный набор пакетов для разработки Telegram бота
RUN pip3 install --no-cache-dir \
    python-telegram-bot[webhook]==20.7 \
    python-dotenv \
    requests \
    aiohttp \
    cryptography \
    pillow

# Создаем рабочую директорию
WORKDIR /app

# Команда по умолчанию (будет переопределена в docker-compose)
CMD ["tail", "-f", "/dev/null"]
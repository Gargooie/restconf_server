FROM python:3.9-slim

WORKDIR /app

# Копируем файлы требований и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем пользователя для безопасности
RUN useradd -m restconf && chown -R restconf:restconf /app
USER restconf

# Открываем порт
EXPOSE 8080

# Запускаем сервер
CMD ["python3", "main.py"]

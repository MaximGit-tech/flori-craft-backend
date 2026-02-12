FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Собираем статику
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Запускаем с Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "FloriCraft.wsgi:application"]

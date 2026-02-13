#!/bin/bash
# docker_quick_fix.sh - Быстрое исправление для Docker окружения

set -e

echo "🐳 Быстрое исправление Posiflora для Docker"
echo "==========================================="
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Проверка текущей директории
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Ошибка: manage.py не найден${NC}"
    echo "Запустите скрипт из корневой директории проекта"
    exit 1
fi

echo -e "${GREEN}✓ Найден manage.py${NC}"

# 2. Проверка Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker найден${NC}"

# 3. Проверка запущенных контейнеров
if ! docker ps | grep -q "flori"; then
    echo -e "${YELLOW}⚠ Контейнеры не запущены${NC}"
    echo "Запускаем контейнеры..."
    docker-compose up -d
    sleep 5
fi

BACKEND_CONTAINER=$(docker ps --filter "name=backend" --format "{{.Names}}" | head -n 1)

if [ -z "$BACKEND_CONTAINER" ]; then
    echo -e "${RED}❌ Backend контейнер не найден${NC}"
    echo "Доступные контейнеры:"
    docker ps
    exit 1
fi

echo -e "${GREEN}✓ Backend контейнер: $BACKEND_CONTAINER${NC}"

# 4. Создание резервной копии
echo ""
echo "📦 Создание резервных копий..."

BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp apps/posiflora/views.py "$BACKUP_DIR/views.py.bak" 2>/dev/null || true
cp apps/posiflora/models.py "$BACKUP_DIR/models.py.bak" 2>/dev/null || true

echo -e "${GREEN}✓ Резервные копии созданы в $BACKUP_DIR${NC}"

# 5. Применение исправлений к models.py
echo ""
echo "🔧 Применение исправлений..."

echo "  - Обновление models.py (добавление buffer к is_expired)"

cat > apps/posiflora/models.py << 'EOF'
from django.db import models
from django.utils import timezone
from datetime import timedelta


class PosifloraSession(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self, buffer_minutes=15):
        """Проверить истечение с буфером 15 минут"""
        buffer = timedelta(minutes=buffer_minutes)
        return timezone.now() >= (self.expires_at - buffer)
    
    def time_until_expiry(self):
        """Время до истечения"""
        return self.expires_at - timezone.now()
    
    def time_until_expiry_minutes(self):
        """Время до истечения в минутах"""
        delta = self.time_until_expiry()
        return int(delta.total_seconds() / 60)
EOF

echo -e "${GREEN}✓ models.py обновлен${NC}"

# 6. Увеличение timeout в products.py
echo "  - Увеличение timeout в products.py"
sed -i 's/timeout=10/timeout=30/g' apps/posiflora/services/products.py
echo -e "${GREEN}✓ Timeout увеличен до 30 секунд${NC}"

# 7. Перезапуск контейнера backend для применения изменений
echo ""
echo "🔄 Перезапуск backend контейнера..."
docker-compose restart backend
sleep 3
echo -e "${GREEN}✓ Backend перезапущен${NC}"

# 8. Проверка токена через Docker
echo ""
echo "🔑 Проверка токена Posiflora..."

docker exec -it $BACKEND_CONTAINER python manage.py check_posiflora_session

echo ""
read -p "Обновить токен сейчас? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Обновление токена..."
    docker exec -it $BACKEND_CONTAINER python manage.py refresh_posiflora_session
    echo -e "${GREEN}✓ Токен обновлен${NC}"
fi

# 9. Настройка cron для автообновления токена (опционально)
echo ""
read -p "Добавить cron задачу для автообновления токена? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CRON_CMD="*/30 * * * * cd $(pwd) && docker exec $BACKEND_CONTAINER python manage.py refresh_posiflora_session >> /var/log/floricraft_cron.log 2>&1"
    
    if ! crontab -l 2>/dev/null | grep -q "refresh_posiflora_session"; then
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo -e "${GREEN}✓ Cron задача добавлена${NC}"
    else
        echo -e "${YELLOW}⚠ Cron задача уже существует${NC}"
    fi
fi

# 10. Итоговая информация
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Быстрое исправление завершено!${NC}"
echo "=========================================="
echo ""
echo "Что было сделано:"
echo "  ✓ Добавлен buffer 15 минут к проверке токена"
echo "  ✓ Увеличен timeout запросов до 30 секунд"
echo "  ✓ Backend контейнер перезапущен"
echo ""
echo "Резервные копии: $BACKUP_DIR"
echo ""
echo -e "${YELLOW}📊 Мониторинг:${NC}"
echo "  Логи backend:  docker-compose logs -f backend"
echo "  Логи всех:     docker-compose logs -f"
echo "  Статус:        docker-compose ps"
echo ""
echo -e "${BLUE}🔍 Проверка:${NC}"
echo "  Токен:  docker exec $BACKEND_CONTAINER python manage.py check_posiflora_session"
echo "  API:    curl http://localhost:8000/api/v1/bouquets"
echo ""
echo -e "${YELLOW}⚠ ВАЖНО:${NC}"
echo "Это временное решение. Для полного кеширования"
echo "запустите: ./deploy_docker.sh"
echo ""

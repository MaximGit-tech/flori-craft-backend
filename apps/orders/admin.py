from django.contrib import admin
from apps.orders.models import Order, OrderItem, TelegramAdmin


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'sender_name', 'total_amount', 'delivery_cost', 'date', 'time', 'created_at', 'paid_at']
    list_filter = ['status', 'district', 'time', 'created_at']
    search_fields = ['id', 'sender_name', 'sender_phone', 'recipent_name', 'recipent_phone', 'payment_id']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'paid_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'status', 'payment_id', 'total_amount', 'delivery_cost')
        }),
        ('Отправитель', {
            'fields': ('sender_name', 'sender_phone')
        }),
        ('Получатель', {
            'fields': ('recipent_name', 'recipent_phone')
        }),
        ('Доставка', {
            'fields': ('full_address', 'apartment', 'entrance', 'floor', 'intercom', 'district', 'date', 'time')
        }),
        ('Открытка', {
            'fields': ('postcart',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'name', 'size', 'price', 'product_id']
    list_filter = ['size']
    search_fields = ['name', 'product_id', 'order__id']


@admin.register(TelegramAdmin)
class TelegramAdminAdmin(admin.ModelAdmin):
    list_display = ['chat_id', 'username', 'first_name', 'last_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['chat_id', 'username', 'first_name', 'last_name']
    readonly_fields = ['chat_id', 'username', 'first_name', 'last_name', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        # Запрещаем добавление через админку, администраторы добавляются только через бота
        return False

"""
Views для Telegram интеграции
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from apps.orders.models import TelegramAdmin, Order
from apps.orders.serializers import TelegramAdminSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_register_admin(request):
    """
    Регистрация администратора через Telegram бота
    
    POST /api/orders/telegram/register/
    
    Body:
    {
        "chat_id": 123456789,
        "username": "john_doe",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    chat_id = request.data.get('chat_id')
    
    if not chat_id:
        return Response(
            {'error': 'chat_id обязателен'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        admin, created = TelegramAdmin.objects.update_or_create(
            chat_id=chat_id,
            defaults={
                'username': request.data.get('username'),
                'first_name': request.data.get('first_name'),
                'last_name': request.data.get('last_name'),
                'is_active': True
            }
        )
        
        action = 'registered' if created else 'updated'
        
        logger.info(
            f"Telegram администратор {action}: "
            f"chat_id={chat_id}, username={admin.username}"
        )
        
        serializer = TelegramAdminSerializer(admin)
        
        return Response({
            'action': action,
            'admin': serializer.data,
            'message': f'Администратор успешно {action}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Ошибка регистрации Telegram администратора: {str(e)}")
        return Response(
            {'error': 'Внутренняя ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def telegram_check_admin(request, chat_id):
    """
    Проверка статуса регистрации администратора
    
    GET /api/orders/telegram/check/{chat_id}/
    """
    try:
        admin = TelegramAdmin.objects.filter(chat_id=chat_id).first()
        
        if admin:
            return Response({
                'is_registered': True,
                'is_active': admin.is_active,
                'username': admin.username,
                'first_name': admin.first_name,
                'registered_at': admin.created_at
            })
        else:
            return Response({
                'is_registered': False,
                'is_active': False
            })
            
    except Exception as e:
        logger.error(f"Ошибка проверки статуса администратора: {str(e)}")
        return Response(
            {'error': 'Внутренняя ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_deactivate_admin(request, chat_id):
    """
    Деактивация администратора
    
    POST /api/orders/telegram/deactivate/{chat_id}/
    """
    try:
        admin = TelegramAdmin.objects.filter(chat_id=chat_id).first()
        
        if not admin:
            return Response(
                {'error': 'Администратор не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        admin.is_active = False
        admin.save()
        
        logger.info(f"Telegram администратор деактивирован: chat_id={chat_id}")
        
        return Response({
            'message': 'Администратор успешно деактивирован',
            'chat_id': chat_id
        })
        
    except Exception as e:
        logger.error(f"Ошибка деактивации администратора: {str(e)}")
        return Response(
            {'error': 'Внутренняя ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def telegram_list_admins(request):
    """
    Список всех Telegram администраторов
    
    GET /api/orders/telegram/admins/
    """
    try:
        admins = TelegramAdmin.objects.all()
        serializer = TelegramAdminSerializer(admins, many=True)
        
        return Response({
            'total': admins.count(),
            'active': admins.filter(is_active=True).count(),
            'admins': serializer.data
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения списка администраторов: {str(e)}")
        return Response(
            {'error': 'Внутренняя ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

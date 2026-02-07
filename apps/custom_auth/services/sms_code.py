import random
from ..models import SmsCode
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

def generate_sms(phone: str) -> str:
    code = str(random.randint(1000, 9999))
    SmsCode.objects.create(phone=phone, code=code)
    return code

def verify_sms(phone: str, code: str) -> bool:
    sms = SmsCode.objects.filter(phone=phone, code=code).order_by('-created_at').first()
    if not sms:
        return False
    if sms.is_expired():
        return False
    return True

def send_sms(phone: str, message: str):
    """
    Отправляет SMS с кодом верификации через SMSC.ru

    Args:
        phone: номер телефона в формате 79991234567 или +79991234567
        message: текст сообщения

    Returns:
        tuple: (success: bool, message: str)
    """

    url = 'https://smsc.ru/sys/send.php'

    cost_params = {
        'login': settings.SMSC_LOGIN,
        'psw': settings.SMSC_PASSWORD,
        'phones': phone,
        'mes': message,
        'charset': 'utf-8',
        'cost': 1,
        'fmt': 3,
    }

    try:
        cost_response = requests.get(url, params=cost_params, timeout=10)
        cost_response.raise_for_status()
        cost_result = cost_response.json()

        if 'error' in cost_result:
            error_msg = cost_result.get('error', 'Неизвестная ошибка')
            error_code = cost_result.get('error_code', '')
            logger.error(f'SMSC cost check error: {error_code} - {error_msg}')
            return False, f'Ошибка проверки стоимости: {error_msg}'

        cost = cost_result.get('cost', 'unknown')
        cnt = cost_result.get('cnt', 1)
        logger.info(f'SMS cost for {phone}: {cost} RUB (parts: {cnt})')

        send_params = {
            'login': settings.SMSC_LOGIN,
            'psw': settings.SMSC_PASSWORD,
            'phones': phone,
            'mes': message,
            'charset': 'utf-8',
            'fmt': 3,
        }

        if settings.SMSC_DEBUG:
            send_params['cost'] = 3
            logger.info(f'SMSC DEBUG mode: simulating SMS send to {phone}')

        response = requests.get(url, params=send_params, timeout=10)
        response.raise_for_status()

        result = response.json()
        logger.info(f'SMSC send response: {result}')

        if 'error' in result:
            error_msg = result.get('error', 'Неизвестная ошибка')
            error_code = result.get('error_code', '')
            logger.error(f'SMSC send error: {error_code} - {error_msg}')
            return False, f'Ошибка отправки: {error_msg}'

        if 'id' in result:
            sms_id = result['id']
            balance = result.get('balance', 'unknown')
            logger.info(f'SMS sent successfully. ID: {sms_id}, Phone: {phone}, Cost: {cost} RUB, Balance: {balance}')
            return True, f'SMS отправлено. ID: {sms_id}'

        return False, 'Неожиданный ответ от SMSC'

    except requests.exceptions.Timeout:
        logger.error('SMSC timeout')
        return False, 'Превышено время ожидания'

    except requests.exceptions.RequestException as e:
        logger.error(f'SMSC request error: {str(e)}')
        return False, f'Ошибка соединения: {str(e)}'

    except Exception as e:
        logger.error(f'SMSC unexpected error: {str(e)}')
        return False, f'Неожиданная ошибка: {str(e)}'

    
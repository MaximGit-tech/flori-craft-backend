import random
from ..models import SmsCode


def generate_sms(phone: str) -> str:
    code = random.randint(100000, 999999)
    SmsCode.objects.create(phone=phone, code=code)
    return code

def verify_sms(phone: str, code: str) -> bool:
    sms = SmsCode.objects.filter(phone=phone, code=code).order_by('-created_at').first()
    if not sms:
        return False
    if sms.is_expired():
        return False
    return True

# пока заглушка
def send_sms(phone: str, message: str):
    # подключить провайдера
    print(f'[SMS] {phone}: {message}')
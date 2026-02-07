from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CustomUser
from .services.sms_code import generate_sms, verify_sms, send_sms
from django.core.signing import Signer, BadSignature

class SendSmsView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Отправить СМС код",
        description="Генерирует и сохраняет СМС код для указанного номера телефона. Код действителен в течение ограниченного времени.",
        request={
            'type': 'object',
            'properties': {
                'phone': {
                    'type': 'string',
                    'description': 'Номер телефона в любом формате',
                    'example': '+79991234567'
                }
            },
            'required': ['phone']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {
                        'type': 'string',
                        'description': 'Статус отправки СМС',
                        'example': 'ok'
                    }
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'description': 'Описание ошибки',
                        'example': 'phone required'
                    }
                }
            }
        },
        tags=['Authentication'],
        examples=[
            OpenApiExample(
                'Успешная отправка',
                value={'status': 'ok'},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: отсутствует телефон',
                value={'error': 'phone required'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Запрос с телефоном',
                value={'phone': '+79991234567'},
                request_only=True
            )
        ]
    )
    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'phone required'}, status=400)

        code = generate_sms(phone)
        success, message = send_sms(phone, f'Ваш код подтверждения FloriCraft: {code}')

        if not success:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send SMS: {message}')

        return Response({'status': 'ok'})


class CheckPhoneView(APIView):

    @extend_schema(
        summary="Проверка номера телефона",
        description="Проверяет существование пользователя с указанным номером телефона в базе данных",
        request={
            'type': 'object',
            'properties': {
                'phone': {
                    'type': 'string',
                    'description': 'Номер телефона в любом формате',
                    'example': '+79991234567'
                }
            },
            'required': ['phone']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'exists': {
                        'type': 'boolean',
                        'description': 'Существует ли пользователь с данным номером в базе данных',
                        'example': True
                    }
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'description': 'Описание ошибки',
                        'example': 'phone is required'
                    }
                }
            }
        },
        tags=['Authentication'],
        examples=[
            OpenApiExample(
                'Пользователь существует',
                value={'exists': True},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Пользователь не найден',
                value={'exists': False},
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: отсутствует телефон',
                value={'error': 'phone is required'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Запрос с телефоном',
                value={'phone': '+79991234567'},
                request_only=True
            )
        ]
    )
    def post(self, request):
        phone = request.data.get('phone')

        if not phone:
            return Response(
                {'error': 'phone is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if CustomUser.objects.filter(phone=phone).exists():
            return Response(
                {'exists': True},
                status=200
            )
        return Response(
            {'exists': False},
            status=200
        )


class VerifySmsRegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Регистрация с верификацией СМС",
        description="Проверяет СМС код и создает нового пользователя. Устанавливает cookie с user_id для последующей авторизации.",
        request={
            'type': 'object',
            'properties': {
                'phone': {
                    'type': 'string',
                    'description': 'Номер телефона пользователя',
                    'example': '+79991234567'
                },
                'code': {
                    'type': 'string',
                    'description': 'СМС код для верификации',
                    'example': '1234'
                },
                'name': {
                    'type': 'string',
                    'description': 'Имя пользователя',
                    'example': 'Иван'
                },
                'gender': {
                    'type': 'string',
                    'description': 'Пол пользователя',
                    'example': 'male'
                }
            },
            'required': ['phone', 'code', 'name', 'gender']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'integer',
                        'description': 'ID созданного пользователя',
                        'example': 42
                    },
                    'phone': {
                        'type': 'string',
                        'description': 'Номер телефона',
                        'example': '+79991234567'
                    },
                    'name': {
                        'type': 'string',
                        'description': 'Имя пользователя',
                        'example': 'Иван'
                    },
                    'gender': {
                        'type': 'string',
                        'description': 'Пол пользователя',
                        'example': 'male'
                    }
                },
                'description': 'Успешная регистрация. Cookie user_id устанавливается автоматически.'
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'description': 'Описание ошибки',
                        'example': 'phone, code, name and gender are required'
                    }
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'internal server error'
                    }
                }
            }
        },
        tags=['Authentication'],
        examples=[
            OpenApiExample(
                'Успешная регистрация',
                value={
                    'id': 42,
                    'phone': '+79991234567',
                    'name': 'Иван',
                    'gender': 'male'
                },
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: отсутствуют обязательные поля',
                value={'error': 'phone, code, name and gender are required'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Ошибка: неверный или истекший код',
                value={'error': 'invalid or expired code'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Запрос регистрации',
                value={
                    'phone': '+79991234567',
                    'code': '1234',
                    'name': 'Иван',
                    'gender': 'male'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        gender = request.data.get('gender')
        name = request.data.get('name')
        phone = request.data.get('phone')
        code = request.data.get('code')

        if not phone or not code or not name or not gender:
            return Response(
                {'error': 'phone, code, name and gender are required'},
                status=400
            )

        if not verify_sms(phone, code):
            return Response(
                {'error': 'invalid or expired code'},
                status=400
            )

        try:
            user, _ = CustomUser.objects.get_or_create(phone=phone, name=name, gender=gender)

            user, _ = CustomUser.objects.get_or_create(phone=phone)

            signer = Signer(salt='user-auth')
            signed_value = signer.sign(str(user.id))

            response = Response({
                'id': user.id,
                'phone': user.phone,
                'name': user.name or '',
                'gender': user.gender or '',
                'cookie_id': signed_value
            })

            return response

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in VerifySmsView: {str(e)}")

            return Response(
                {'error': 'internal server error'},
                status=500
            )


class VerifySmsLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Вход с верификацией СМС",
        description="Проверяет СМС код и выполняет вход существующего пользователя. Устанавливает cookie с user_id для авторизации.",
        request={
            'type': 'object',
            'properties': {
                'phone': {
                    'type': 'string',
                    'description': 'Номер телефона пользователя',
                    'example': '+79991234567'
                },
                'code': {
                    'type': 'string',
                    'description': 'СМС код для верификации',
                    'example': '1234'
                }
            },
            'required': ['phone', 'code']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'id': {
                        'type': 'integer',
                        'description': 'ID пользователя',
                        'example': 42
                    },
                    'phone': {
                        'type': 'string',
                        'description': 'Номер телефона',
                        'example': '+79991234567'
                    },
                    'name': {
                        'type': 'string',
                        'description': 'Имя пользователя (может быть пустым)',
                        'example': 'Иван'
                    },
                    'gender': {
                        'type': 'string',
                        'description': 'Пол пользователя (может быть пустым)',
                        'example': 'male'
                    }
                },
                'description': 'Успешный вход. Cookie user_id устанавливается автоматически.'
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'description': 'Описание ошибки',
                        'example': 'phone and code are required'
                    }
                }
            },
            500: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'internal server error'
                    }
                }
            }
        },
        tags=['Authentication'],
        examples=[
            OpenApiExample(
                'Успешный вход',
                value={
                    'id': 42,
                    'phone': '+79991234567',
                    'name': 'Иван',
                    'gender': 'male'
                },
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: отсутствуют обязательные поля',
                value={'error': 'phone and code are required'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Ошибка: неверный или истекший код',
                value={'error': 'invalid or expired code'},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                'Запрос входа',
                value={
                    'phone': '+79991234567',
                    'code': '1234'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        phone = request.data.get('phone')
        code = request.data.get('code')

        if not phone or not code:
            return Response(
                {'error': 'phone and code are required'},
                status=400
            )

        if not verify_sms(phone, code):
            return Response(
                {'error': 'invalid or expired code'},
                status=400
            )

        try:
            user, _ = CustomUser.objects.get_or_create(phone=phone)

            signer = Signer(salt='user-auth')
            signed_value = signer.sign(str(user.id))

            response = Response({
                'id': user.id,
                'phone': user.phone,
                'name': user.name or '',
                'gender': user.gender or '',
                'cookie_id': signed_value
            })

            return response

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in VerifySmsView: {str(e)}")

            return Response(
                {'error': 'internal server error'},
                status=500
            )


class ProfileView(APIView):
    @extend_schema(
        summary="Получить профиль пользователя",
        description="Возвращает информацию о пользователе по подписанной cookie user_id",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'phone': {
                        'type': 'string',
                        'description': 'Номер телефона пользователя',
                        'example': '+79991234567'
                    },
                    'name': {
                        'type': 'string',
                        'description': 'Имя пользователя',
                        'example': 'Иван'
                    }
                }
            },
            401: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'user_id cookie is required'
                    }
                }
            },
            404: {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'example': 'no users found'
                    }
                }
            }
        },
        tags=['User Profile'],
        examples=[
            OpenApiExample(
                'Успешное получение профиля',
                value={
                    'phone': '+79991234567',
                    'name': 'Иван'
                },
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                'Ошибка: отсутствует cookie',
                value={'error': 'user_id cookie is required'},
                response_only=True,
                status_codes=['401']
            ),
            OpenApiExample(
                'Ошибка: пользователь не найден',
                value={'error': 'no users found'},
                response_only=True,
                status_codes=['404']
            )
        ]
    )
    def get(self, request):
        user_id = request.GET.get('user_id')
        if not user_id:
            return Response(
                {"error": "user_id cookie is required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            signer = Signer(salt='user-auth')
            user_id = signer.unsign(user_id)
        except BadSignature:
            return Response(
                {"error": "invalid signature"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "no users found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "phone": user.phone,
            "name": user.name
        })


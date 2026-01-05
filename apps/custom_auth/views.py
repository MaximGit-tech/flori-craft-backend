from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CustomUser
from .services.sms_code import generate_sms, send_sms, verify_sms


class SendSmsView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return Response({'error': 'phone required'}, status=400)

        code = generate_sms(phone)
        # send_sms(phone, f'Ваш код: {code}')

        return Response({'status': 'ok'})


class VerifySmsView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        phone = request.data.get('phone')
        code = request.data.get('code')

        if not verify_sms(phone, code):
            return Response({'error': 'invalid or expired code'}, status=400)

        user, _ = CustomUser.objects.get_or_create(phone=phone)

        response = Response({
            'id': user.id,
            'phone': user.phone,
            'name': user.name,
        })

        response.set_cookie(
            key='user_id',
            value=user.id,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            secure=False,
            samesite='Lax',
        )

        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({'status': 'ok'})
        response.delete_cookie('user_id')
        return response


class ProfileView(APIView):
    def get(self, request):
        if not request.user:
            return Response({'error': 'unauthorized'}, status=401)

        return Response({
            'phone': request.user.phone,
            'name': request.user.name,
        })
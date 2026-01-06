from rest_framework import status
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
        name = request.data.get('name')
        phone = request.data.get('phone')
        code = request.data.get('code')

        if not phone or not code or not name:
            return Response(
                {'error': 'phone, code and name are required'},
                status=400
            )

        if not verify_sms(phone, code):
            return Response(
                {'error': 'invalid or expired code'},
                status=400
            )

        try:
            user, _ = CustomUser.objects.get_or_create(phone=phone, name=name)

            response = Response({
                'id': user.id,
                'phone': user.phone,
                'name': user.name or '',
            })

            response.set_cookie(
                key='user_id',
                value=str(user.id),
                max_age=60 * 60 * 24 * 7,
                httponly=True,
                secure=True,
                samesite='Lax',
            )

            return response

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in VerifySmsView: {str(e)}")

            return Response(
                {'error': 'internal server error'},
                status=500
            )


class LogoutView(APIView):
    def post(self, request):
        response = Response({'status': 'ok'})
        response.delete_cookie('user_id')
        return response


class ProfileView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")

        if not user_id:
            return Response(
                {"error": "user_id is required"},
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


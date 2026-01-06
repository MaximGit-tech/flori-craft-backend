from rest_framework.views import APIView
from rest_framework.response import Response


class CartView(APIView):
    def get(self, request):
        if not request.user:
            return Response(
                {'error': 'unauthorized'},
                status=401
            )

        from .services.db_cart import get_items
        return Response({
            'items': get_items(request.user)
        })



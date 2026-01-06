from rest_framework.views import APIView
from rest_framework.response import Response
from .services.db_cart import get_items
from apps.cart.serializers import CartItemSerializer


class CartView(APIView):
    def get(self, request):
        if not request.user:
            return Response(
                {'error': 'unauthorized'},
                status=401
            )

        items = get_items(request.user)
        serializer = CartItemSerializer(items, many=True)

        return Response({
            'items': serializer.data
        })


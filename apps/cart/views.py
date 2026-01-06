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


class CartItemView(APIView):
    def post(self, request):
        if not request.user:
            return Response(
                {'error': 'unauthorized'},
                status=401
            )

        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id required'},
                status=400
            )

        from .services.db_cart import add_item
        add_item(request.user, product_id)

        return Response({'status': 'ok'})

    def delete(self, request):
        if not request.user:
            return Response(
                {'error': 'unauthorized'},
                status=401
            )

        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id required'},
                status=400
            )

        from .services.db_cart import remove_item
        remove_item(request.user, product_id)

        return Response({'status': 'ok'})
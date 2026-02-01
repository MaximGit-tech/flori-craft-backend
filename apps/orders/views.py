from rest_framework.views import APIView


class CreateOrder(APIView):
    def post(self, request):
        items = request.data.get('items')
        

from django.shortcuts import render
from .models import Banner
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import BannerSerializer
# Create your views here.
@api_view()
@permission_classes([AllowAny])
def get_banners(request):
    banners=Banner.objects.all()
    serialized_item=BannerSerializer(banners,many=True)
    return Response(serialized_item.data)

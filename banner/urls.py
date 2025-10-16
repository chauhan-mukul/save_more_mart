from django.urls import path
from . import views
urlpatterns = [
    # Cart overview
    path('getbanner/',views.get_banners,name='banner')
]

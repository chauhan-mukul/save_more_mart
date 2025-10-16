from django.urls import path
from .views import SignupView, LoginView, LogoutView,user_detail
from  . import views
from rest_framework.authtoken.views import obtain_auth_token
urlpatterns = [
    path('signup/', SignupView, name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', user_detail, name='user-detail'),  # renamed view function to user_detail
    path('token/', obtain_auth_token, name='token'),
]
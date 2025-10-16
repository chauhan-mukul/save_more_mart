from django.urls import path,include
from . import views
urlpatterns=[
    path('delivery_check/',views.check_delivery_location,name='check_delivery'),
    path('addresses/',views.CustomerAddressView,name='addresses'),
    path('selected_address/',views.selected_address_view,name='selected_address'),
    path('delete/',views.delete_address,name='delete'),
    path('set_default/', views.set_default_address, name='set_default_address'),
    path('set_default/', views.set_default_address, name='set_default_address'),
    path('order_item/',views.add_order_items,name='order_item'),

]

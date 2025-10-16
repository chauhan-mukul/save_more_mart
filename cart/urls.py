from django.urls import path
from . import views

urlpatterns = [
    # Cart overview
    path('', views.get_cart, name='get_cart'),
    path('summary/', views.cart_summary, name='cart_summary'),
    
    # Cart items
    path('items/', views.cart_items, name='cart_items'),
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    
    # Individual item operations
    path('items/<int:item_id>/update/', views.update_cart_item, name='update_cart_item'),
    path('items/<int:item_id>/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('items/<int:item_id>/increase/', views.increase_quantity, name='increase_quantity'),
    path('items/<int:item_id>/decrease/', views.decrease_quantity, name='decrease_quantity'),
    
    # User authentication related
    path('merge/', views.merge_cart, name='merge_cart'),
]


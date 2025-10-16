from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from decimal import Decimal
import json

from .models import Cart, CartItem
from inventory.models import ProductVariant
from .serializers import CartSerializer, CartItemSerializer
from delivery.models import DeliveryLocation


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Allow both authenticated and anonymous users
def get_cart(request):
    """Get current user's cart with all items"""
    try:
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'cart': serializer.data,
            'total_items': cart.total_items,
            'total_amount': float(cart.total_amount),
            'is_empty': cart.is_empty
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_items(request):
    """Get all items in the current user's cart"""
    try:
        cart = get_or_create_cart(request)
        items = CartItem.objects.filter(cart=cart).select_related(
            'variant__product', 'variant__inventory'
        )
        serializer = CartItemSerializer(items, many=True)
        
        return Response({
            'success': True,
            'items': serializer.data,
            'count': len(serializer.data)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Add item to cart or update quantity if item already exists"""
    try:
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
      
        if not variant_id:
            return Response({
                'success': False,
                'error': 'variant_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity < 1:
            return Response({
                'success': False,
                'error': 'Quantity must be at least 1'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get variant and check if it exists
        variant = get_object_or_404(ProductVariant, id=variant_id)
        
        # Check inventory availability
        try:
            if variant.inventory.quantity < quantity:
                return Response({
                    'success': False,
                    'error': f'Only {variant.inventory.quantity} items available in stock'
                }, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({
                'success': False,
                'error': 'Product availability could not be verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart = get_or_create_cart(request)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Item exists, update quantity
            new_quantity = cart_item.quantity + quantity
            if variant.inventory.quantity < new_quantity:
                return Response({
                    'success': False,
                    'error': f'Cannot add {quantity} more items. Only {variant.inventory.quantity - cart_item.quantity} more available'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity = new_quantity
            cart_item.save()
        
        serializer = CartItemSerializer(cart_item)
        
        return Response({
            'success': True,
            'message': 'Item added to cart successfully',
            'item': serializer.data,
            'cart_total_items': cart.total_items,
            'cart_total_amount': float(cart.total_amount)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Update quantity of a specific cart item"""
    try:
        quantity = int(request.data.get('quantity', 1))
        
        if quantity < 1:
            return Response({
                'success': False,
                'error': 'Quantity must be at least 1'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
    
        # Check inventory availability
        if cart_item.variant.inventory.quantity < quantity:
            return Response({
                'success': False,
                'error': f'Only {cart_item.variant.inventory.quantity} items available in stock'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item)
        
        return Response({
            'success': True,
            'message': 'Cart item updated successfully',
            'item': serializer.data,
            'cart_total_items': cart.total_items,
            'cart_total_amount': float(cart.total_amount)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    """Remove a specific item from cart"""
    try:
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        product_name = cart_item.variant.product.name
        cart_item.delete()
        
        return Response({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_total_items': cart.total_items,
            'cart_total_amount': float(cart.total_amount)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def increase_quantity(request, item_id):
    """Increase quantity of a cart item by 1 or specified amount"""
    try:
        amount = int(request.data.get('amount', 1))
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        new_quantity = cart_item.quantity + amount
        
        # Check inventory availability
        if cart_item.variant.inventory.quantity < new_quantity:
            return Response({
                'success': False,
                'error': f'Cannot add {amount} more items. Only {cart_item.variant.inventory.quantity - cart_item.quantity} more available'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.increase_quantity(amount)
        serializer = CartItemSerializer(cart_item)
        
        return Response({
            'success': True,
            'message': 'Quantity increased successfully',
            'item': serializer.data,
            'cart_total_items': cart.total_items,
            'cart_total_amount': float(cart.total_amount)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decrease_quantity(request, item_id):
    """Decrease quantity of a cart item by 1 or specified amount"""
    try:
        amount = int(request.data.get('amount', 1))
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if cart_item.quantity <= amount:
            # If quantity becomes 0 or less, remove item
            product_name = cart_item.variant.product.name
            cart_item.delete()
            
            return Response({
                'success': True,
                'message': f'{product_name} removed from cart',
                'item_removed': True,
                'cart_total_items': cart.total_items,
                'cart_total_amount': float(cart.total_amount)
            }, status=status.HTTP_200_OK)
        
        cart_item.decrease_quantity(amount)
        serializer = CartItemSerializer(cart_item)
        
        return Response({
            'success': True,
            'message': 'Quantity decreased successfully',
            'item': serializer.data,
            'cart_total_items': cart.total_items,
            'cart_total_amount': float(cart.total_amount)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Remove all items from cart"""
    try:
        cart = get_or_create_cart(request)
        items_count = cart.total_items
        cart.clear()
        
        return Response({
            'success': True,
            'message': f'Cart cleared. {items_count} items removed',
            'cart_total_items': 0,
            'cart_total_amount': 0.0
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_summary(request):
    """Get cart summary with totals and item count"""
    pincode=request.GET.get('pincode')
    if not pincode:
        return Response({
            'error': 'Pincode is required',
            'message': 'Please provide a pincode parameter',
            'available': False
        }, status=status.HTTP_400_BAD_REQUEST)
    if not pincode.isdigit() or len(pincode) < 6:
        return Response({
            'error': 'Invalid pincode format',
            'message': 'Pincode should be at least 6 digits',
            'available': False,
            'pincode': pincode
        }, status=status.HTTP_400_BAD_REQUEST)
    
        # Check delivery availability using the model method
    available, location = DeliveryLocation.check_delivery_available(pincode)
        
    try:
        cart = get_or_create_cart(request)
        
        # Calculate additional costs (you can customize these)
        subtotal = cart.total_amount
        tax_rate = Decimal('0.0')  # 8% tax
        tax_amount = subtotal * tax_rate
        
        # Free shipping over $50
        shipping_cost = Decimal(location.delivery_fee) if subtotal < Decimal(location.minimum_order) else Decimal('0.00')
        total_amount = subtotal + tax_amount + shipping_cost
        
        return Response({
            'success': True,
            'summary': {
                'total_items': cart.total_items,
                'subtotal': float(subtotal),
                'tax_rate': float(tax_rate),
                'tax_amount': float(tax_amount),
                'shipping_cost': float(shipping_cost),
                'total_amount': float(total_amount),
                'free_shipping_threshold': location.minimum_order,
                'is_free_shipping': shipping_cost == 0
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def merge_cart(request):
    """Merge anonymous cart with user cart when user logs in"""
    try:
        session_key = request.data.get('session_key')
        
        if not session_key:
            return Response({
                'success': False,
                'error': 'session_key is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find anonymous cart
            anonymous_cart = Cart.objects.get(session_key=session_key, user=None)
            
            # Merge with user's cart
            user_cart = anonymous_cart.merge_with_user_cart(request.user)
            
            serializer = CartSerializer(user_cart)
            
            return Response({
                'success': True,
                'message': 'Cart merged successfully',
                'cart': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Cart.DoesNotExist:
            return Response({
                'success': True,
                'message': 'No anonymous cart found to merge'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_or_create_cart(request):
    """Helper function to get or create cart for authenticated or anonymous users"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key, user=None)
    
    return cart
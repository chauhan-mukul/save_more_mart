from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from decimal import Decimal
from cart.models import Cart,CartItem
from inventory.models import ProductVariant
from .models import DeliveryLocation,CustomerAddress,OrderItem,Order
from .serializers import CustomerAddressSerializer
# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
def check_delivery_location(request):
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
    try:
        # Check delivery availability using the model method
        available, location = DeliveryLocation.check_delivery_available(pincode)
        
        if available:
            # Delivery is available
            return Response({
                'available': True,
                'pincode': pincode,
                'message': f'Delivery available to {location.area_name}',
                'location_details': {
                    'area_name': location.area_name,
                    'city': location.city,
                    'state': location.state,
                    'delivery_fee': Decimal(location.delivery_fee),
                    'minimum_order': Decimal(location.minimum_order),
                    'estimated_delivery_hours': location.estimated_delivery_hours,
                    'free_delivery_above': Decimal(location.minimum_order) if location.delivery_fee > 0 else 0
                },
                'delivery_info': {
                    'fee': f"₹{location.delivery_fee}",
                    'min_order': f"₹{location.minimum_order}",
                    'estimated_time': f"{location.estimated_delivery_hours} hours",
                    'free_delivery_text': f"Free delivery on orders above ₹{location.minimum_order}" if location.delivery_fee > 0 else "Free delivery"
                }
            }, status=status.HTTP_200_OK)
        else:
            # Delivery not available
            return Response({
                'available': False,
                'pincode': pincode,
                'message': 'Sorry, delivery is not available to this location',
                'suggestion': 'Please check nearby pincodes or contact customer support'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        # Handle unexpected errors
        return Response({
            'error': 'Internal server error',
            'message': 'Something went wrong while checking delivery availability',
            'available': False,
            'pincode': pincode
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def CustomerAddressView(request):
    if request.method=='GET':
        user=request.user
        addresses = CustomerAddress.objects.filter(user=user).order_by('-is_default', '-created_at')
        serializer = CustomerAddressSerializer(addresses, many=True)
        return Response({
            'success': True,
            'addresses': serializer.data,
            'count': addresses.count()
        }, status=status.HTTP_200_OK)
    elif request.method=='POST':
        user=request.user
        serializer = CustomerAddressSerializer(data=request.data)
        if serializer.is_valid():
            # Save with authenticated user
            address = serializer.save(user=user)
            
            # If this is set as default, remove default from other addresses
            if address.is_default:
                CustomerAddress.objects.filter(user=user).exclude(id=address.id).update(is_default=False)
            
            return Response({
                'success': True,
                'message': 'Address added successfully',
                'address': CustomerAddressSerializer(address).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def selected_address_view(request):
    id=request.GET.get('id')
    item=CustomerAddress.objects.get(id=id)
    serializer=CustomerAddressSerializer(item)
    return Response(serializer.data,status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_address(request):
    id=request.GET.get('id')
    try:
        address = CustomerAddress.objects.get(id=id, user=request.user)  # safer: only delete user’s own address
        address.delete()
        return Response({"message": "Address deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except CustomerAddress.DoesNotExist:
        return Response({"error": "Address not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def set_default_address(request):
    try:
        id = request.data.get('address_id')  # Use request body, not GET
        
        # Validate user owns the address
        new_address = CustomerAddress.objects.get(id=id, user=request.user)
        
        # Use transaction for consistency
        with transaction.atomic():
            # Unset all defaults for this user
            CustomerAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            # Set new default
            new_address.is_default = True
            new_address.save()  # ✅ Actually save to database
        
        return Response({
            'success': True,
            'message': 'Default address updated successfully',
            'default_address_id': id
        })
    except CustomerAddress.DoesNotExist:
        return Response({'success': False, 'message': 'Address not found'}, status=404)


def create_order(request):
    address_id=request.GET.get('address_id')
    fee=request.GET.get('fee')
    if request.user.is_authenticated:
        customer=get_object_or_404(CustomerAddress,user=request.user,id=address_id)
        delivery_loc=get_object_or_404(DeliveryLocation,pincode=customer.pincode)
        order = Order.objects.create(
        customer=request.user,
        delivery_address=customer
        )
        order.save()
        return (order,delivery_loc)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_order_items(request):
    try:
        with transaction.atomic():  # ensures all-or-nothing
            order,loc = create_order(request)

            items = request.data.get('items', [])
            if not items:
                return Response({'failed': 'No items provided'}, status=400)

            created_items = []
            amount=0
            for item in items:
                variant_id = item.get('variant_id')
                quantity = item.get('quantity', 1)

                variant = get_object_or_404(ProductVariant, id=variant_id)

                order_item = OrderItem.objects.create(
                    order=order,
                    product_name=f"{variant.product.name} {variant.sku}",
                    product_id=variant_id,
                    price_per_item=variant.get_final_price(),
                    quantity=quantity
                )
                amount=amount+variant.get_final_price()*quantity
                created_items.append(order_item.id)
            if amount<loc.minimum_order:
                order.delivery_fee=loc.delivery_fee
            order.total_amount=order.items_total+order.delivery_fee
            order.save()
            return Response({
                'success': True,
                'order_id': str(order.id),
                'items_created': created_items
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'failed': str(e)}, status=500)


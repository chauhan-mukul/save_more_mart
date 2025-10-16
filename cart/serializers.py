from rest_framework import serializers
from .models import Cart, CartItem
from inventory.models import ProductVariant, Product,Best_deals
from inventory.models import InventoryItem
from decimal import Decimal
class ProductSerializer(serializers.ModelSerializer):
    """Basic product serializer for cart items"""
    class Meta:
        model = Product
        fields = ['name','base_price']

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model=InventoryItem
        fields=['varient','quantity']

class ProductVariantSerializer(serializers.ModelSerializer):
    """Product variant serializer for cart items"""
    product = ProductSerializer(read_only=True)
    inventory_quantity = serializers.SerializerMethodField()
    # inventory=InventorySerializer(read_only=True)
    price=serializers.SerializerMethodField()
    class Meta:
        model=ProductVariant
        fields=['id','variant_name','sku','additional_price','is_active','price','inventory_quantity','product']
    def get_price(self, obj):
        base_price = obj.product.base_price + obj.additional_price
        # if obj.deals:
        #     deal = obj.deals  # OneToOne relation
        #     discount_rate = Decimal(deal.discount) / Decimal(100)
        #     return base_price - (base_price * discount_rate)
        # else:
        return base_price
    
    def get_inventory_quantity(self, obj):
        """Get available inventory quantity"""
        try:
            return obj.inventory.quantity
        except:
            return 0


class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer with product and pricing details"""
    variant = ProductVariantSerializer(read_only=True)
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'variant', 'quantity','total_price','availability_status'
            , 'is_available', 'added_at', 'updated_at','unit_price'
        ]
    
    def get_unit_price(self, obj):
        """Get unit price including variant additional price"""
        return float(obj.get_unit_price())
    
    def get_total_price(self, obj):
        """Get total price for this cart item"""
        return float(obj.get_total_price())
    
    def get_availability_status(self, obj):
        """Get availability status message"""
        return obj.get_availability_status()
    
    def get_is_available(self, obj):
        """Check if requested quantity is available"""
        return obj.is_available()


class CartSerializer(serializers.ModelSerializer):
    """Cart serializer with all items and totals"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_amount = serializers.SerializerMethodField()
    is_empty = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items', 'total_amount', 'is_empty',
            'created_at', 'updated_at'
        ]
    
    def get_total_amount(self, obj):
        """Get total cart amount as float"""
        return float(obj.total_amount)


class CartSummarySerializer(serializers.Serializer):
    """Serializer for cart summary with calculations"""
    total_items = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=4)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    free_shipping_threshold = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_free_shipping = serializers.BooleanField()
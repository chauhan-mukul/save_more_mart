from rest_framework import serializers
from .models import Category, Brand, Product, ProductVariant, InventoryItem,Best_deals

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    color=serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'code', 'parent', 'description', 'image',
            'is_active', 'sort_order', 'created_at',
            'subcategories', 'icon','color'
        ]

    def get_subcategories(self, obj):
        children = obj.subcategories.filter(is_active=True)
        return CategorySerializer(children, many=True).data

    def get_icon(self, obj):
        icon_obj = obj.icons.first()
        return icon_obj.icon if icon_obj else None
    def get_color(self, obj):
        icon_obj = obj.icons.first()
        return icon_obj.color if icon_obj else None

    
class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model= Brand
        fields=['id','name','website','logo','description']

class ProductVariationSerializer(serializers.ModelSerializer):
    price=serializers.SerializerMethodField('actual_price')
    class Meta:
        model=ProductVariant
        fields=['id','product','variant_name','sku','additional_price','is_active','price']
    def actual_price(self,obj):
        return obj.get_final_price()

class ProductSerializer(serializers.ModelSerializer):
   
    product_varients = ProductVariationSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id','name', 'code', 'category', 'brand', 'description', 'image', 'base_price', 'created_at', 'is_active', 'product_varients']

class BestdealSerializer(serializers.ModelSerializer):
    originalPrice=serializers.SerializerMethodField()
    salePrice=serializers.SerializerMethodField()
    name=serializers.SerializerMethodField()
    discount=serializers.SerializerMethodField()
    class Meta:
        model=Best_deals
        fields=['id','item','name','originalPrice','salePrice','discount','image_url']
    def get_name(self,obj):
        return obj.item.sku
    def get_salePrice(self,obj):
        actual_price=obj.item.product.base_price +obj.item.additional_price
        discount=obj.discount*actual_price/100
        return "$"+str(actual_price-discount)
    def get_originalPrice(self,obj):
        actual_price=obj.item.product.base_price +obj.item.additional_price
        return "$"+str(actual_price)
    def get_discount(self,obj):
        return str(int(obj.discount))+"% OFF"


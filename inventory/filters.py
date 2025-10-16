# inventory/filters.py
from django_filters import rest_framework as filters
from .models import Category,Product,ProductVariant,Brand

class CategoryFilter(filters.FilterSet):
    parent__isnull = filters.BooleanFilter(field_name='parent', lookup_expr='isnull')

    class Meta:
        model = Category
        fields = ['parent__isnull','parent','id']
        
class ProductFilter(filters.FilterSet):
    class Meta:
        model=Product
        fields=['category','id']
        
class ProductVarientFilter(filters.FilterSet):
    class Meta:
        model=ProductVariant
        fields=['id']

class BrandFilter(filters.FilterSet):
    class Meta:
        model=Brand
        fields=['id']


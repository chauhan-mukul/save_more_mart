from django.shortcuts import render
from .models import Brand,Product,ProductVariant,InventoryItem,Category,Best_deals
from .serializers import CategorySerializer,BrandSerializer,ProductSerializer,ProductVariationSerializer,BestdealSerializer
from rest_framework import generics
from rest_framework import viewsets,response
from rest_framework.decorators import api_view,permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from .filters import CategoryFilter,ProductFilter,BrandFilter
from rest_framework import permissions
from rest_framework.response import Response
from django.db.models import Q


# class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
#     permission_classes = [permissions.AllowAny]
#     queryset = Category.objects.filter(is_active=True)
#     serializer_class = CategorySerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = CategoryFilter

class ParentCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]

    queryset = Category.objects.filter(parent__isnull=True)
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def SingleCategoryViewSet(request):
    id=request.GET.get('categoryId')
    object=Category.objects.get(id=id)
    serialized_item=CategorySerializer(object)
    return Response(serialized_item.data)



# Create your views here.
# class BrandViewSet(viewsets.ReadOnlyModelViewSet):
#     permission_classes = [permissions.AllowAny]

#     queryset=Brand.objects.all()
#     serializer_class=BrandSerializer
#     filter_backends=[DjangoFilterBackend]
#     filterset_class=BrandFilter

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def BrandViewSet(request):
    category_id=request.GET.get('category_id')
    brands = Brand.objects.filter(products__category=category_id).distinct()
    serialized_items=BrandSerializer(brands,many=True)
    return Response({
        "success": True,
        "count": len(serialized_items.data),
        "brands": serialized_items.data
    })


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]

    queryset=Product.objects.filter(is_active=True)
    serializer_class=ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class=ProductFilter


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def ProductVariantsByProductView(request):
    items=ProductVariant.objects.select_related('product').all()
    id=request.GET.get('id')
    product=request.GET.get('product')
    if(id):
        items=items.filter(id=id)
    if(product):
        items=items.filter(product__id=product)
    serialized_item=ProductVariationSerializer(items,many=True)
    return Response(serialized_item.data)
    

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def BestDealView(request):
    items=Best_deals.objects.all()
    serialized_item=BestdealSerializer(items,many=True)
    return Response(serialized_item.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_products(request):
    query=request.GET.get('q','').strip()
    if not query:
        return Response({'products': [], 'message': 'No search query provided'})
        
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)|
        Q(brand__name__icontains=query) |
        Q(category__name__icontains=query)
    ).select_related('category').distinct()[:20]
    serialized_items=ProductSerializer(products,many=True)
    return Response({
        'products': serialized_items.data,  # Important: Add .data
        'total': len(serialized_items.data),
        'query': query
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def AllProductViewSet(request):
    id=request.GET.get('category')
    category=Category.objects.filter(parent=id)
    ids=[i.id for i in category]
    products = Product.objects.filter(category__in=ids)
    serialized_products = ProductSerializer(products, many=True)
    return Response(serialized_products.data)
    

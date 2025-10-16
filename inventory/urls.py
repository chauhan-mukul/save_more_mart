from django.urls import path
from  . import views
urlpatterns = [
 
    path('category/',views.ParentCategoryViewSet.as_view({'get':'list'}),name='category'),
    path('brand/',views.BrandViewSet,name='brand'),
    path('product/',views.ProductViewSet.as_view({'get':'list'}),name='product'),
    path('product_varients/', views.ProductVariantsByProductView, name='product_varient'),
    path('best_deal/',views.BestDealView,name='best_deal'),
    path('search/',views.search_products,name='search_products'),
    path('parent/',views.SingleCategoryViewSet,name='categorysingle'),
    path('all_products/',views.AllProductViewSet,name='all_products'),

]

from django.contrib import admin
from .models import Category,Brand,Product,ProductVariant,InventoryItem,CategoryIcon,Best_deals
# Register your models here.
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(InventoryItem)
admin.site.register(CategoryIcon)
admin.site.register(Best_deals)






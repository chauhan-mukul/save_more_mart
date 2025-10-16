from django.contrib import admin
from .models import DeliveryLocation,CustomerAddress,Payment,Order,OrderItem,DeliveryTracking
# Register your models here.
admin.site.register(DeliveryLocation)
admin.site.register(CustomerAddress)
admin.site.register(Payment)
admin.site.register(Order)
admin.site.register(DeliveryTracking)
admin.site.register(OrderItem)



from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import re
import uuid

# Simple delivery location model
class DeliveryLocation(models.Model):
    """Areas where delivery is available"""
    pincode = models.CharField(max_length=10, unique=True)
    area_name = models.CharField(max_length=100) 
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    estimated_delivery_hours = models.IntegerField(default=2, help_text="Delivery time in hours")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.area_name}, {self.city} - {self.pincode}"
    
    @classmethod
    def check_delivery_available(cls, pincode):
        """Check if delivery is available for a pincode"""
        try:
            location = cls.objects.get(pincode=pincode, is_available=True)
            return True, location
        except cls.DoesNotExist:
            return False, None
    
    class Meta:
        db_table = 'delivery_locations'
        verbose_name = 'Delivery Location'
        verbose_name_plural = 'Delivery Locations'

# Customer address model
class CustomerAddress(models.Model):
    """Customer delivery addresses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_address = models.TextField()
    title=models.CharField(default='Home')
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.pincode}"
    
    def save(self, *args, **kwargs):
        # Make sure only one default address per user
        if self.is_default:
            CustomerAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    def is_delivery_available(self):
        """Check if delivery is available to this address"""
        available, location = DeliveryLocation.check_delivery_available(self.pincode)
        return available
    
    class Meta:
        db_table = 'customer_addresses'
        verbose_name = 'Customer Address'
        verbose_name_plural = 'Customer Addresses'

# Order status choices
class OrderStatus(models.TextChoices):
    CART = 'cart', 'In Cart'
    PLACED = 'placed', 'Order Placed'
    CONFIRMED = 'confirmed', 'Confirmed'
    PREPARING = 'preparing', 'Preparing'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'

# Payment status choices
class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Payment Pending'
    PAID = 'paid', 'Payment Successful'
    FAILED = 'failed', 'Payment Failed'
    REFUNDED = 'refunded', 'Refunded'

# Main order model
class Order(models.Model):
    """Customer orders"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_address = models.ForeignKey(CustomerAddress, on_delete=models.PROTECT)
    
    # Order details
    items_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Status tracking
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.CART)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Special instructions
    delivery_notes = models.TextField(blank=True, help_text="Special delivery instructions")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    placed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer.username}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not exists
        if not self.order_number:
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{str(self.id)[:8]}"
        
        # Set placed_at timestamp when order is placed
        if self.status == OrderStatus.PLACED and not self.placed_at:
            self.placed_at = timezone.now()
        
        # Set delivered_at timestamp when order is delivered
        if self.status == OrderStatus.DELIVERED and not self.delivered_at:
            self.delivered_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def place_order(self):
        """Place the order (change status from cart to placed)"""
        if self.status == OrderStatus.CART:
            # Check if delivery is available
            if not self.delivery_address.is_delivery_available():
                raise ValueError("Delivery not available to this location")
            
            # Calculate delivery fee
            _, location = DeliveryLocation.check_delivery_available(self.delivery_address.pincode)
            self.delivery_fee = location.delivery_fee if location else 0
            
            # Check minimum order amount
            if location and self.items_total < location.minimum_order:
                raise ValueError(f"Minimum order amount is ₹{location.minimum_order}")
            
            # Calculate total
            self.total_amount = self.items_total + self.delivery_fee
            
            # Change status to placed
            self.status = OrderStatus.PLACED
            self.placed_at = timezone.now()
            self.save()
            
            return True
        return False
    
    def is_placed(self):
        """Check if order is placed"""
        return self.status != OrderStatus.CART
    
    def is_paid(self):
        """Check if order payment is completed"""
        return self.payment_status == PaymentStatus.PAID
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PLACED, OrderStatus.CONFIRMED]
    
    @property
    def delivery_location(self):
        """Get delivery location details"""
        _, location = DeliveryLocation.check_delivery_available(self.delivery_address.pincode)
        return location
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

# Order items model (simple product reference)
class OrderItem(models.Model):
    """Items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    product_id = models.CharField(max_length=50, help_text="Product SKU or ID")
    quantity = models.PositiveIntegerField(default=1)
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.price_per_item * self.quantity
        super().save(*args, **kwargs)
        
        # Update order total
        self.update_order_total()
    
    def update_order_total(self):
        """Update the order's items total"""
        order = self.order
        order.items_total = sum(item.total_price for item in order.items.all())
        order.total_amount = order.items_total + order.delivery_fee
        order.save(update_fields=['items_total', 'total_amount'])
    
    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

# Payment tracking model
class Payment(models.Model):
    """Payment records for orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.CharField(max_length=100, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('wallet', 'Wallet'),
    ])
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Payment gateway details
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    gateway_response = models.TextField(blank=True, help_text="Payment gateway response")
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.payment_id} - ₹{self.amount}"
    
    def save(self, *args, **kwargs):
        # Generate payment ID if not exists
        if not self.payment_id:
            self.payment_id = f"PAY{timezone.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:6]}"
        
        # Set completed timestamp
        if self.status == PaymentStatus.PAID and not self.completed_at:
            self.completed_at = timezone.now()
            # Update order payment status
            self.order.payment_status = PaymentStatus.PAID
            self.order.save(update_fields=['payment_status'])
        
        super().save(*args, **kwargs)
    
    def mark_paid(self, transaction_id="", gateway_response=""):
        """Mark payment as successful"""
        self.status = PaymentStatus.PAID
        self.completed_at = timezone.now()
        if transaction_id:
            self.gateway_transaction_id = transaction_id
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()
    
    def mark_failed(self, reason=""):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED
        self.gateway_response = reason
        # Update order payment status
        self.order.payment_status = PaymentStatus.FAILED
        self.order.save(update_fields=['payment_status'])
        self.save()
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-initiated_at']

# Simple delivery tracking
class DeliveryTracking(models.Model):
    """Basic delivery status tracking"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery_tracking')
    current_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PLACED)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivery_person_name = models.CharField(max_length=100, blank=True)
    delivery_person_phone = models.CharField(max_length=15, blank=True)
    tracking_notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Delivery tracking for {self.order.order_number}"
    
    def update_status(self, new_status, notes=""):
        """Update delivery status"""
        self.current_status = new_status
        if notes:
            self.tracking_notes = f"{timezone.now().strftime('%Y-%m-%d %H:%M')} - {notes}\n{self.tracking_notes}"
        
        # Update order status as well
        self.order.status = new_status
        self.order.save(update_fields=['status'])
        self.save()
    
    class Meta:
        db_table = 'delivery_tracking'
        verbose_name = 'Delivery Tracking'
        verbose_name_plural = 'Delivery Tracking'

# Helper functions for common operations
class DeliveryHelper:
    """Helper functions for delivery operations"""
    
    @staticmethod
    def check_delivery_availability(pincode):
        """Check if delivery is available for a pincode"""
        return DeliveryLocation.check_delivery_available(pincode)
    
    @staticmethod
    def get_customer_orders(user):
        """Get all orders for a customer"""
        return Order.objects.filter(customer=user, status__in=[
            OrderStatus.PLACED, OrderStatus.CONFIRMED, 
            OrderStatus.PREPARING, OrderStatus.OUT_FOR_DELIVERY, 
            OrderStatus.DELIVERED
        ]).order_by('-created_at')
    
    @staticmethod
    def get_pending_payments(user):
        """Get orders with pending payments for a customer"""
        return Order.objects.filter(
            customer=user,
            payment_status=PaymentStatus.PENDING,
            status__in=[OrderStatus.PLACED, OrderStatus.CONFIRMED]
        )
    
    @staticmethod
    def create_sample_order(user, address, items_data):
        """Create a sample order with items"""
        # Check delivery availability
        available, location = DeliveryLocation.check_delivery_available(address.pincode)
        if not available:
            raise ValueError("Delivery not available to this location")
        
        # Create order
        order = Order.objects.create(
            customer=user,
            delivery_address=address,
            delivery_fee=location.delivery_fee
        )
        
        # Add items
        total = Decimal('0.00')
        for item in items_data:
            order_item = OrderItem.objects.create(
                order=order,
                product_name=item['name'],
                product_id=item['id'],
                quantity=item['quantity'],
                price_per_item=Decimal(str(item['price']))
            )
            total += order_item.total_price
        
        # Update order total
        order.items_total = total
        order.total_amount = total + order.delivery_fee
        order.save()
        
        return order

# Example usage in views.py or shell
"""
# Check delivery availability
available, location = DeliveryLocation.check_delivery_available('175001')
if available:
    print(f"Delivery available! Fee: ₹{location.delivery_fee}")

# Get customer's previous orders
customer_orders = DeliveryHelper.get_customer_orders(request.user)

# Create and place an order
order = Order.objects.create(
    customer=request.user,
    delivery_address=user_address
)

# Add items to order
OrderItem.objects.create(
    order=order,
    product_name="Organic Apples",
    product_id="APPLE001",
    quantity=2,
    price_per_item=120.00
)

# Place the order
try:
    order.place_order()
    print("Order placed successfully!")
except ValueError as e:
    print(f"Error: {e}")

# Create payment record
payment = Payment.objects.create(
    order=order,
    amount=order.total_amount,
    payment_method='online'
)

# Mark payment as successful
payment.mark_paid(transaction_id="TXN123456")
"""
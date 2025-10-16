from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from inventory.models import ProductVariant  # Import from your inventory app

class Cart(models.Model):
    """Shopping cart for users (both authenticated and anonymous)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='cart'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart ({self.session_key[:8]}...)"
    
    @property
    def total_items(self):
        """Get total quantity of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_amount(self):
        """Calculate total cart value"""
        return sum(item.get_total_price() for item in self.items.all())
    
    @property
    def is_empty(self):
        """Check if cart is empty"""
        return not self.items.exists()
    
    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()
    
    def merge_with_user_cart(self, user):
        """Merge anonymous cart with user's existing cart when they login"""
        try:
            user_cart = Cart.objects.get(user=user)
            # Merge items from this cart to user's cart
            for item in self.items.all():
                existing_item = user_cart.items.filter(variant=item.variant).first()
                if existing_item:
                    existing_item.quantity += item.quantity
                    existing_item.save()
                else:
                    item.cart = user_cart
                    item.save()
            # Delete this anonymous cart
            self.delete()
            return user_cart
        except Cart.DoesNotExist:
            # No existing user cart, just assign this cart to user
            self.user = user
            self.session_key = None
            self.save()
            return self

class CartItem(models.Model):
    """Individual items in a shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'variant']  # One item per variant per cart
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.variant.product.name} ({self.variant.variant_name}) x {self.quantity}"
    
    def get_unit_price(self):
        """Get unit price including variant additional price"""
        return self.variant.get_final_price()
    
    def get_total_price(self):
        """Get total price for this cart item"""
        return self.get_unit_price() * self.quantity
    
    def increase_quantity(self, amount=1):
        """Increase item quantity"""
        self.quantity += amount
        self.save()
    
    def decrease_quantity(self, amount=1):
        """Decrease item quantity"""
        if self.quantity > amount:
            self.quantity -= amount
            self.save()
        else:
            self.delete()
    
    def is_available(self):
        """Check if requested quantity is available in inventory"""
        try:
            inventory = self.variant.inventory
            return inventory.quantity >= self.quantity
        except:
            return False
    
    def get_availability_status(self):
        """Get availability status message"""
        try:
            inventory = self.variant.inventory
            if inventory.quantity == 0:
                return "Out of Stock"
            elif inventory.quantity < self.quantity:
                return f"Only {inventory.quantity} available"
            else:
                return "In Stock"
        except:
            return "Availability Unknown"


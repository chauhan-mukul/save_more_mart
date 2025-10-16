from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Category(models.Model):
    """Hierarchical product categories with unlimited nesting"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='subcategories'
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']
        unique_together = ['name', 'parent']  # Unique name within same parent level
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_full_path(self):
        """Get full category path like 'Electronics > Mobile > Smartphones'"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(path))
    
    def get_all_children(self):
        """Get all descendant categories (recursive)"""
        children = []
        for child in self.subcategories.filter(is_active=True):
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def is_leaf_category(self):
        """Check if this is a leaf category (has no children)"""
        return not self.subcategories.exists()

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_varients')
    variant_name = models.CharField(max_length=100)  # e.g., "Red, XL"
    sku = models.CharField(max_length=50, unique=True)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"
    def get_final_price(self):
        """Calculate the price including deal discount if available"""
        base_price = self.product.base_price + self.additional_price

        # check if Best_deals exists for this variant
        if hasattr(self, "deals"):
            discount_rate = self.deals.discount / Decimal(100)
            return base_price - (base_price * discount_rate)

        return base_price

class InventoryItem(models.Model):
    variant = models.OneToOneField(ProductVariant, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.variant.sku} - {self.quantity} items"


class CategoryIcon(models.Model):
    """Icons associated with product categories"""
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='icons'
    )
    icon = models.CharField(
        max_length=20,
        help_text="Emoji, font-awesome class, or icon name",
        
    )
    color = models.CharField(
        max_length=20,
        choices=[
            ("success", "Success (Green)"),
            ("danger", "Danger (Red)"),
            ("info", "Info (Blue)"),
            ("warning", "Warning (Yellow)"),
            ("primary", "Primary"),
            ("secondary", "Secondary"),
        ],
        default="primary"
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']
        unique_together = ['category', 'icon']

    def __str__(self):
        return f"{self.icon} ({self.category.name})"

class Best_deals(models.Model):
    item=models.OneToOneField(ProductVariant,on_delete=models.CASCADE,related_name='deals')
    discount=models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image_url=models.URLField()
    def __str__(self):
        return f"{self.item}"
    



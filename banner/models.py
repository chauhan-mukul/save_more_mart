# Create your models here.
from django.db import models

class Banner(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    image = models.URLField(help_text="URL of the banner image")
    cta = models.CharField(max_length=100, help_text="Call To Action button text", default="Shop Now")
    created_at = models.DateTimeField(auto_now_add=True)
    route = models.CharField(max_length=200, blank=True, null=True)  # Internal route path

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

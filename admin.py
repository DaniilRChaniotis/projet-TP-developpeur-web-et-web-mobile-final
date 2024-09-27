from django.contrib import admin
from .models import Product, Category, ContactMessage  

admin.site.register(Product)
admin.site.register(Category)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')

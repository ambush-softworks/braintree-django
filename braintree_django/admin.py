from django.contrib import admin

from .models import PaymentMethod, CustomerVault


class PaymentMethodInline(admin.StackedInline):
    model = PaymentMethod


class CustomerVaultAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'owner')
    inlines = [
        PaymentMethodInline
    ]


admin.site.register(CustomerVault, CustomerVaultAdmin)

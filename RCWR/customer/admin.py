from django.contrib import admin
from .models import *

admin.site.register(RiceItem)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderRiceItems)
admin.site.register(OrderDetails)
admin.site.register(LendingStat)
admin.site.register(ShippingMeth)
admin.site.register(Barangay)
admin.site.register(Payment)
admin.site.register(Policy)
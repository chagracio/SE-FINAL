from django.db import models
from django.contrib.auth.models import User

class RiceItem(models.Model):
    name = models.CharField(max_length = 50, null = True)
    price = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True)
    loanPrice = models.DecimalField(max_digits = 10, decimal_places = 2, null = True)
    quantity = models.IntegerField(blank = True)
    description = models.TextField(null = True)
    image = models.ImageField(upload_to = 'rice_images/', null = True)

    def __str__(self):
        return self.name

class Barangay(models.Model):
    name = models.CharField(max_length = 100, null = True)
    shippingFee = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True)

    def __str__(self):
        return self.name

class ShippingMeth(models.Model):
    method= models.CharField(max_length = 20, null = True)
    
    def __str__(self):
        return self.method

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, null = True, blank = True)
    name = models.CharField(max_length = 100, null = True)
    email = models.CharField(max_length = 100, null = True)
    ContactNum = models.CharField(max_length = 11, null = True)
    barangay = models.ForeignKey(Barangay, on_delete = models.SET_NULL, blank = True, null = True )
    street = models.CharField(max_length = 100, null = True, blank = True)
    method = models.ForeignKey(ShippingMeth, on_delete = models.SET_NULL, blank = True, null = True )
    customer_id = models.ImageField(upload_to = 'customer_ids/',  blank=True, null=True)
    loan = models.BooleanField(default = False, null=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.SET_NULL, blank = True, null = True)
    date_ordered = models.DateTimeField(auto_now_add = True)
    complete = models.BooleanField(default = False, null = True, blank = False)
    transaction_id = models.CharField(max_length = 100, null = True)

    def __str__(self):
        return str(self.id)

    @property
    def get_cart_total(self):
        orderitems = self.orderriceitems_set.all()
        total = sum([r.get_total for r in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderriceitems_set.all()
        total = sum([r.quantity for r in orderitems])
        return total
    
    @property
    def get_order_total(self):
        orderitems = self.orderriceitems_set.all()
        sf = 0

        if self.customer.barangay == None and self.customer.method == None:
            total = sum([r.get_total for r in orderitems])
        elif self.customer.method.method == 'Pickup':
            total = sum([r.get_total for r in orderitems])
        else:
            sf = self.customer.barangay.shippingFee
            total = sum([r.get_total for r in orderitems]) + sf
        return total

    @property
    def shipping(self):

        if self.customer.method == None:
            sf = 0
        elif self.customer.method.method == 'Pickup':
            sf = 0
        elif self.customer.method.method == 'Delivery':
            sf = self.customer.barangay.shippingFee
        return sf

    @property
    def get_total_amount(self):
        payment = self.payment_set.all()
        total = sum([r.payment for r in payment])
        return total

class OrderRiceItems(models.Model):
    rice = models.ForeignKey(RiceItem, on_delete = models.SET_NULL, blank = True, null = True)
    order = models.ForeignKey(Order, on_delete = models.SET_NULL, blank = True, null = True)
    quantity = models.IntegerField(default = 0, blank = True, null = True)
    date_added = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.rice.name

#individual rice item total
    @property
    def get_total(self):
        if self.order.customer.loan == None or self.order.customer.loan == False:
            total = self.rice.price * self.quantity
        else:
            total = self.rice.loanPrice * self.quantity
        return total

class OrderDetails(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.SET_NULL, blank = True, null = True)
    order = models.ForeignKey(Order, on_delete = models.SET_NULL, blank = True, null = True)
    rice_ordered = models.ManyToManyField(OrderRiceItems, blank = True, related_name='orders')
    total_payment = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True)
    #address = models.CharField(max_length = 200, null = True)
    #ContactNum = models.CharField(max_length = 11, null = True, blank = True)
    shippingMeth = models.CharField(max_length = 15, null = True)
    loan = models.BooleanField(default = False, null = True)

    shippingStat = (
        ('Preparing', 'Preparing'),
        ('Out for delivery', 'Out for delivery'),
        ('Delivered', 'Delivered'),
        ('Ready for Pick Up', 'Ready for Pick Up'),
        ('Picked Up', 'Picked Up')
    )
    shippingStatus = models.CharField(max_length = 50, blank = True, choices = shippingStat) #Ready for pickup, picked up, on the way, delivered
    
    orderStat = (
        ('Accepted', 'Accepted'),
        ('Denied', 'Denied'),
    ) 
    
    orderStatus = models.CharField(max_length = 50, null=True, blank = True, choices = orderStat) #Accepted or denied
    cancel = models.BooleanField(default = False, null = True, blank = False)
    date_added = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.customer.name

    @property
    def Date_Added(self):
        date = self.date_added.strftime("%B %m, %Y")
        return date

class LendingStat(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.SET_NULL, blank = True, null = True)
    order = models.ForeignKey(Order, on_delete = models.SET_NULL, blank = True, null = True)
    loan = models.BooleanField(default = False, null = True)
    total_payment = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True)
    total_amount_paid = models.DecimalField(max_digits = 10, decimal_places = 2, null = True)
    amount_paid = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True, null = True)
    balance = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True) #updates everytime amount_paid is being updated
    status = models.CharField(max_length = 20, null = True)
    due_date = models.DateTimeField(auto_now_add = False, null = True)
    date_added = models.DateTimeField(auto_now_add = True)
    complete = models.BooleanField(default = False, null = True, blank = False)
    
    def __str__(self):
        return self.customer.name

    @property
    def dueDate(self):
        if self.due_date == None:
            due = "-"
        else:
            due = self.due_date.strftime("%B %m, %Y")
        return due

class Payment(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.SET_NULL, blank = True, null = True)
    order = models.ForeignKey(Order, on_delete = models.SET_NULL, blank = True, null = True)
    amount = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True, null = True)
    total_amount = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True, null = True)
    balance = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True, null = True)
    date_paid = models.DateTimeField(auto_now_add = True, null= True)
    status = models.CharField(max_length = 10, null = True)

    def __str__(self):
        return self.customer.name

    @property
    def date(self):
        return self.date_paid.strftime("%B %m, %Y")

    @property
    def payment(self):
        return self.amount

class Policy(models.Model):
    min_amount = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True, null = True)
    max_amount = models.DecimalField(max_digits = 10, decimal_places = 2, blank = True, null = True)
    num_weeks = models.IntegerField(blank = True, null = True)

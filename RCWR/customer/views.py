from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from c3gUsers.decorators import allowed_users
from django.http import JsonResponse
import json
import datetime
from django.contrib.auth.models import User
from django.db.models import F, Avg, Sum, Count, FloatField
from django.core.exceptions import *
from django.http import HttpResponse
import csv
from django.core.paginator import Paginator
from django.db.models.functions import ExtractMonth
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


#==================INDEX============================
def index (request):
    rice_item = RiceItem.objects.all()
    return render(request, 'index.html', {'rice_item':rice_item})

#==================ADMIN DASHBOARD============================
@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def dashboard (request):
    rice_list = RiceItem.objects.all()

    orders = OrderDetails.objects.all().count()
    new_orders = OrderDetails.objects.filter(orderStatus = 'Owner is Validating your order')
    cancelled = OrderDetails.objects.filter(cancel=True)
    paid = LendingStat.objects.filter(status='Fully paid')
    partial = LendingStat.objects.filter(status='Partially paid')
    unpaid = LendingStat.objects.filter(status='Unpaid')

    # revenue= LendingStat.objects.aggregate(s=Sum('total_amount_paid'))['s']
    # print(revenue)
    monthly_revenue = LendingStat.objects.filter(date_added__year='2023').values_list('date_added__month').aggregate(s=Sum('total_amount_paid'))['s']
 
    context = {
        'orders':orders,
        'rice_list':rice_list,
        'new_orders':new_orders,
        'cancelled':cancelled,
        'paid':paid,
        'partial':partial,
        'unpaid':unpaid,
        'monthly_revenue':monthly_revenue

    }
    return render(request, 'AdminFolder/index.html', context)

#==================RICE LIST============================
@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def RiceList(request):
    rice_list = RiceItem.objects.all()
    return render(request, 'AdminFolder/RiceList.html', {'rice_list':rice_list})

#==================ADDING RICE============================
@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def addRice (request):
    rice_form = RiceItemForm()
    if request.method == 'POST':
        rice_form = RiceItemForm(request.POST, request.FILES)
        if rice_form.is_valid():
            rice_form.save()
        messages.success(request, "Rice Item has been successfully added!")
        return redirect('ricelist')
    return render(request, 'AdminFolder/AddRice.html', {'rice_form':rice_form})

#==================DELETE RICE============================
def deleteRice(request, id):
    rice = RiceItem.objects.get(id=id)
    rice.delete()
    return redirect('ricelist')

#==================UPDATE RICE============================
@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def updateRice(request, id):
    customer = RiceItem.objects.get(id=id)
    rice_form = RiceItemForm(instance=customer)
    if request.method == 'POST':
        rice_form = RiceItemForm(request.POST, request.FILES, instance=customer)
        if rice_form.is_valid():
            rice_form.save()
        messages.success(request, "Rice Item has been updated!")
        return redirect('ricelist')
    return render(request, 'AdminFolder/UpdateRiceItem.html', {'rice_form':rice_form})

#==================CUSTOMER HOMEPAGE============================
@login_required(login_url='login')
def CustomerHomepage(request):

    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    riceitems = order.orderriceitems_set.all()

    rice_item = RiceItem.objects.all()
    context = {
        'rice_item':rice_item,
        'riceitems':riceitems,
        'order':order}
    return render(request, 'Customer.html', context)

#==================CHECK OUT============================
@login_required(login_url='login')
def Checkout(request):
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    riceitems = order.orderriceitems_set.all()

    rice_item = RiceItem.objects.all()
    context = {
        'rice_item':rice_item,
        'riceitems':riceitems,
        'order':order,
        'customer':customer,
        }
    return render(request, 'PlaceorderPage.html', context)

#==================UPDATE CART ITEMS============================
@login_required(login_url='login')
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    rice = RiceItem.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderRiceitem, created = OrderRiceItems.objects.get_or_create(order=order, rice=rice)
    
    if action == 'add':
        orderRiceitem.quantity = (orderRiceitem.quantity + 1)
    elif action == 'remove':
        orderRiceitem.quantity = (orderRiceitem.quantity - 1)

    orderRiceitem.save()

    if action == 'del':
        orderRiceitem.delete()

    # if orderRiceitem.quantity <= 0:
    #     orderRiceitem.delete()
    
    return JsonResponse('Item was added', safe=False)

#==================PROCESSING ORDER============================
def processOrder(request):
    print('Data:', request.body)
    transaction_id = datetime.datetime.now().timestamp()
    data =  json.loads(request.body)
    
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    # rice = RiceItem.objects.all()
    # riceitems = order.orderriceitems_set.all()

    # for r in riceitems:
    #     rice.name.quantity =rice.name.quantity - r.rice.quantity
    #     rice.save()

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True      
    order.save()

    OrderDetails.rice_ordered = OrderRiceItems.objects.all()

    OrderDetails.objects.create(
        customer=customer,
        order=order,
        # rice_ordered = OrderDetails.rice_ordered,
        total_payment=total,
        #address=data['form']['address'],
        ##ContactNum=data['form']['tel'],
        shippingMeth=customer.method.method,
        loan = customer.loan,
        shippingStatus='Order Submitted',
        orderStatus='Owner is Validating your order',
    )

    return JsonResponse('Order Submitted', safe=False)

#==================ORDER STATUS(customer side)============================
def CustomerDashboard(request):
    customer = request.user.customer
    orderdetails = OrderDetails.objects.filter(customer = customer)

    context = {

        'orderdetails':orderdetails,
        }
    return render(request, 'CustomerDashboard.html', context)

def cancel(request, id):
    order = OrderDetails.objects.get(id=id)
    order.cancel = True
    order.orderStatus = "Cancelled"
    order.save()
    return redirect('CustomerDashboard')

#==================INQUIRY/CONTACT US============================
def Inquiry(request):
    return render(request, 'Inquiry.html')

#==================LENDING STATUS(customer side)============================
def LendingStatus(request):
    customer = request.user.customer
    orderdetails = OrderDetails.objects.filter(customer = customer)
    lendingstat = LendingStat.objects.filter(customer = customer)
    
    context = {
        'lendingstat':lendingstat,
        'orderdetails':orderdetails
    }
    return render(request, 'LendingStatus.html', context)

#==================ADMIN ACCESS TO LIST OF ORDERS============================
def orders(request):

    #orderdetails = OrderDetails.objects.all()

    p = Paginator(OrderDetails.objects.all(), 5)
    page = request.GET.get('page')
    orderdetails = p.get_page(page)
    context = {
        'orderdetails':orderdetails,
        }
    return render(request, 'AdminFolder/ListOfOrders.html', context)


#==================ADMIN TO UPDATE CUSTOMER ORDER STATUS============================
def UpdateOrderStatus(request, id):
    orderdeets = OrderDetails.objects.get(id=id)
    orderform = CustomerOrderForm(instance=orderdeets)
    if request.method == 'POST':
        orderform = CustomerOrderForm(request.POST, instance=orderdeets)
        if orderform.is_valid():
            orderform.save()

            orderdetails = OrderDetails.objects.get(id=id)
        
            if orderdeets.orderStatus == 'Accepted' and orderdeets.shippingStatus == 'Preparing':
                if orderdeets.loan == True:

                    if orderdeets.total_payment <= 2999:
                        now = datetime.datetime.now() + datetime.timedelta(weeks=4)
                    elif orderdeets.total_payment > 2999 and orderdeets.total_payment <= 4999:
                        now = datetime.datetime.now() + datetime.timedelta(weeks=6)
                    elif orderdeets.total_payment > 4999 and orderdeets.total_payment <= 9999:
                        now = datetime.datetime.now() + datetime.timedelta(weeks=10)
                    elif orderdeets.total_payment > 9999 and orderdeets.total_payment <= 14999:
                        now = datetime.datetime.now() + datetime.timedelta(weeks=15)
                    elif orderdeets.total_payment > 14999 and orderdeets.total_payment <= 19999:
                        now = datetime.datetime.now() + datetime.timedelta(weeks=20)
                    elif orderdeets.total_payment > 19999 and orderdeets.total_payment <= 29999:
                        now = datetime.datetime.now() + datetime.timedelta(weeks=30)
                    else:
                        now = datetime.datetime.now() + datetime.timedelta(weeks=53)

                    LendingStat.objects.create(
                        customer=orderdetails.customer,
                        order = orderdetails.order,
                        loan= orderdetails.loan,
                        total_payment=orderdetails.total_payment,
                        total_amount_paid=0,
                        amount_paid=0,
                        balance=orderdetails.total_payment,
                        due_date=now,
                        status='Unpaid',
                        date_added = datetime.datetime.now()
                    )
                else:
                    LendingStat.objects.create(
                        customer=orderdetails.customer,
                        order = orderdetails.order,
                        loan= orderdetails.loan,
                        total_payment=orderdetails.total_payment,
                        total_amount_paid=0,
                        amount_paid=0,
                        balance=orderdetails.total_payment,
                        status='Unpaid',
                        date_added = models.DateTimeField(auto_now_add = True)
                    )

        return redirect('orders')

        
    
    context = {
        'orderdeets':orderdeets,
        'orderform':orderform
    }
    return render(request, 'AdminFolder/UpdateOrderStatus.html', context)

#==================ADMIN ACCESS TO CUSTOMER LENDING STATUS============================
def CustomerStatus(request):
    # lendingDeets = LendingStat.objects.all()
    p = Paginator(LendingStat.objects.all(), 10)
    page = request.GET.get('page')
    lendingDeets = p.get_page(page)
    return render(request, 'AdminFolder/lendingStat.html', {'lendingDeets':lendingDeets})

def UpdateLendingStatus(request, id):
    lendingDeets = LendingStat.objects.get(id=id)
    lending_form = LendingForm(instance=lendingDeets)
    if request.method == 'POST':
        lending_form = LendingForm(request.POST, instance=lendingDeets)
        if lending_form.is_valid():
            lending_form.save()
            
            lendingDeets.total_amount_paid = lendingDeets.total_amount_paid + lendingDeets.amount_paid
            lendingDeets.balance = lendingDeets.total_payment - lendingDeets.total_amount_paid

            if lendingDeets.balance == 0:
                lendingDeets.status = 'Fully paid'
            else:
                lendingDeets.status = 'Partially paid'
            
            lendingDeets.save()

            Payment.objects.create(
                customer=lendingDeets.customer,
                order = lendingDeets.order,
                amount = lendingDeets.amount_paid,
                total_amount = lendingDeets.total_amount_paid,
                balance = lendingDeets.balance,
                date_paid = datetime.datetime.now(),
                status = lendingDeets.status
            )
            

        return redirect('customerLendingStatus')

    context = {
        'lending_form':lending_form
    }
    return render(request, 'AdminFolder/UpdateLendingStatus.html', context)

def CustomerInfo(request, id):
    customer = Customer.objects.get(id=id)
    customer_form = CustomerForm(instance=customer)
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST, request.FILES, instance=customer)
        if customer_form.is_valid():
            customer_form.save()
        # messages.success(request, "Rice Item has been updated!")
        return redirect('checkout')
    return render(request, 'customerinfo.html', {'customer_form':customer_form, 'customer':customer})

def OrderDetail(request, id):
    orderdeets = OrderDetails.objects.get(id=id)
    orderform = CustomerOrderForm(instance=orderdeets)
    if request.method == 'POST':
        orderform = CustomerOrderForm(request.POST, instance=orderdeets)
        if orderform.is_valid():
            orderform.save()

            orderdetails = OrderDetails.objects.get(id=id)
                
            i = 1
            if orderdeets.orderStatus == 'Accepted' and orderdeets.shippingStatus == 'Preparing':
                if orderdeets.loan == True:
                    while i < 100:
                        x = Policy.objects.get(id = i)
                        if orderdeets.total_payment > x.min_amount and orderdeets.total_payment <= x.max_amount:
                            print("VERYYYYY IDK ANYMOOOOOOOOOOOOORE!!!!!!")
                            now = timezone.now() + timedelta(weeks= x.num_weeks)   
                            print(now)
                            LendingStat.objects.create(
                                customer=orderdetails.customer,
                                order = orderdetails.order,
                                loan= orderdetails.loan,
                                total_payment=orderdetails.total_payment,
                                total_amount_paid=0,
                                amount_paid=0,
                                balance=orderdetails.total_payment,
                                due_date=now,
                                status='Unpaid',
                                date_added = datetime.datetime.now()
                            )
                            break
                        i = i + 1
                    
                    
                else:
                    LendingStat.objects.create(
                        customer=orderdetails.customer,
                        order = orderdetails.order,
                        loan= orderdetails.loan,
                        total_payment=orderdetails.total_payment,
                        total_amount_paid=0,
                        amount_paid=0,
                        balance=orderdetails.total_payment,
                        status='Unpaid',
                        date_added = models.DateTimeField(auto_now_add = True)
                    )

        return redirect('orders')
    
    context = {
        'orderdeets':orderdeets,
        'orderform':orderform
    }
    return render (request, 'AdminFolder/OrderDetails.html', context)

def LendingDetail(request, id):
    lendingDeets = LendingStat.objects.get(id=id)
    lending_form = LendingForm(instance=lendingDeets)
    if request.method == 'POST':
        lending_form = LendingForm(request.POST, instance=lendingDeets)
        if lending_form.is_valid():
            lending_form.save()
            
            lendingDeets.total_amount_paid = lendingDeets.total_amount_paid + lendingDeets.amount_paid
            lendingDeets.balance = lendingDeets.total_payment - lendingDeets.total_amount_paid

            if lendingDeets.balance == 0:
                lendingDeets.status = 'Fully paid'
            else:
                lendingDeets.status = 'Partially paid'
            
            lendingDeets.save()

            Payment.objects.create(
                customer=lendingDeets.customer,
                order = lendingDeets.order,
                amount = lendingDeets.amount_paid,
                total_amount = lendingDeets.total_amount_paid,
                balance = lendingDeets.balance,
                date_paid = datetime.datetime.now(),
                status = lendingDeets.status
            )
            

        return redirect('customerLendingStatus')
    context = {
        'lendingDeets':lendingDeets,
        'lending_form':lending_form
    }
    return render (request, 'AdminFolder/LendingDetails.html', context)

#FILTERING ORDER PAGE

# def orders(request):

    # orderdetails = OrderDetails.objects.all()
    # context = {
    #     'orderdetails':orderdetails,
    #     }
    # return render(request, 'AdminFolder/ListOfOrders.html', context)

#Filter by new orders
def NewOrders(request):
    #orderdetails = OrderDetails.objects.filter(orderStatus = 'Owner is Validating your order')
    p = Paginator(OrderDetails.objects.filter(orderStatus = 'Owner is Validating your order'), 5)
    page = request.GET.get('page')
    orderdetails = p.get_page(page)
    context = {
        'orderdetails':orderdetails,
    }
    return render(request, 'AdminFolder/ListOfOrders.html', context)

#filter by cancelled
def CancelledOrders(request):
    # orderdetails = OrderDetails.objects.filter(cancel = True)
    p = Paginator(OrderDetails.objects.filter(cancel = True), 5)
    page = request.GET.get('page')
    orderdetails = p.get_page(page)
    context = {
        'orderdetails':orderdetails,
    }
    return render(request, 'AdminFolder/ListOfOrders.html', context)

#filter by loan
def LoanOrders(request):
    # orderdetails = OrderDetails.objects.filter(loan = True)
    p = Paginator(OrderDetails.objects.filter(loan = True), 5)
    page = request.GET.get('page')
    orderdetails = p.get_page(page)

    context = {
        'orderdetails':orderdetails,
    }
    return render(request, 'AdminFolder/ListOfOrders.html', context)
#filter by not loaned
def NotLoanOrders(request):
    p = Paginator(OrderDetails.objects.filter(loan = False), 5)
    page = request.GET.get('page')
    orderdetails = p.get_page(page)
    context = {
        'orderdetails':orderdetails,
    }
    return render(request, 'AdminFolder/ListOfOrders.html', context)

#SORTING ORDER PAGE

#Sort by date ascending
def Date_Desc (request):
    #orderdetails = OrderDetails.objects.order_by('-date_added')
    p = Paginator(OrderDetails.objects.order_by('-date_added'), 5)
    page = request.GET.get('page')
    orderdetails = p.get_page(page)
    context = {
        'orderdetails':orderdetails,
    }
    return render(request, 'AdminFolder/ListOfOrders.html', context)

#sort by alphabet
def Alphabetical(request):
    #orderdetails = OrderDetails.objects.order_by('customer')
    p = Paginator(OrderDetails.objects.order_by('customer'), 5)
    page = request.GET.get('page')
    orderdetails = p.get_page(page)
    context = {
        'orderdetails':orderdetails,
    }
    return render(request, 'AdminFolder/ListOfOrders.html', context)

#FILTERING LENDING PAGE

#filter by paid
def Paid(request):
    lending = LendingStat.objects.filter(status = 'Fully paid')
    p = Paginator(LendingStat.objects.filter(status = 'Fully paid'), 10)
    page = request.GET.get('page')
    lendingDeets = p.get_page(page)
    context = {
        'lendingDeets':lendingDeets,
        'lending':lending,
    }
    return render(request, 'AdminFolder/lendingStat.html', context)

#Download by Paid
def export_paid(request):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['CUSTOMER NAME', 'TOTAL PAYMENT', 'TOTAL AMOUNT PAID', 'BALANCE', 'STATUS'])

    paid = LendingStat.objects.filter(status = 'Fully paid')
    
    for p in paid:
        writer.writerow([p.customer.name, p.total_payment, p.total_amount_paid, p.balance, p.status])
    response['Content-Disposition'] = 'attachment; filename="Paid Lending.csv"'

    return response

#filter by unpaid
def Unpaid(request):
    lending = LendingStat.objects.filter(status = 'Unpaid')
    p = Paginator(LendingStat.objects.filter(status = 'Unpaid'), 10)
    page = request.GET.get('page')
    lendingDeets = p.get_page(page)
    context = {
        'lendingDeets':lendingDeets,
        'lending':lending,
    }
    return render(request, 'AdminFolder/lendingStat.html', context)

#Download by Unpaid
def export_unpaid(request):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['CUSTOMER NAME', 'TOTAL PAYMENT', 'TOTAL AMOUNT PAID', 'BALANCE', 'STATUS'])

    unpaid = LendingStat.objects.filter(status = 'Unpaid')
    
    for p in unpaid:
        writer.writerow([p.customer.name, p.total_payment, p.total_amount_paid, p.balance, p.status])
    response['Content-Disposition'] = 'attachment; filename="Unpaid Lending.csv"'

    return response

#partially paid
def Partially_Paid(request):
    lending = LendingStat.objects.filter(status = 'Partially paid')
    p = Paginator(LendingStat.objects.filter(status = 'Partially Paid'), 10)
    page = request.GET.get('page')
    lendingDeets = p.get_page(page)
    context = {
        'lendingDeets':lendingDeets,
        'lending':lending,
    }
    return render(request, 'AdminFolder/lendingStat.html', context)

def export_partially_paid(request):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['CUSTOMER NAME', 'TOTAL PAYMENT', 'TOTAL AMOUNT PAID', 'BALANCE', 'STATUS'])

    p_paid = LendingStat.objects.filter(status = 'Partially Paid')
    
    for p in p_paid:
        writer.writerow([p.customer.name, p.total_payment, p.total_amount_paid, p.balance, p.status])
    response['Content-Disposition'] = 'attachment; filename="Partially Paid Lending.csv"'

    return response
#SORTING LENDING PAGE

#sort by date ascending
#sort by alphabet
def Alphabetical_Order(request):
    lending = LendingStat.objects.order_by('customer')
    p = Paginator(LendingStat.objects.order_by('customer'), 10)
    page = request.GET.get('page')
    lendingDeets = p.get_page(page)
    context = {
        'lendingDeets':lendingDeets,
        'lending':lending,
    }
    return render(request, 'AdminFolder/lendingStat.html', context)

def export_alpha(request):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    writer.writerow(['CUSTOMER NAME', 'TOTAL PAYMENT', 'TOTAL AMOUNT PAID', 'BALANCE', 'STATUS'])

    alpha = LendingStat.objects.order_by('customer')
    
    for p in alpha:
        writer.writerow([p.customer.name, p.total_payment, p.total_amount_paid, p.balance, p.status])
    response['Content-Disposition'] = 'attachment; filename="Lending Status Alpha.csv"'

    return response
# def export_new_orders(request):
#     response = HttpResponse(content_type='text/csv')
#     writer = csv.writer(response)
#     writer.writerow(['CUSTOMER NAME', 'ORDERS', 'TOTAL PAYMENT', 'RICE LOAN', 'ORDER STATUS'])

#     orders = OrderDetails.objects.all()

    
#     for order in orders:
#         r = []
#         for rice in order.order.orderriceitems_set.all():
#            r.append(F'{rice.rice.name} {rice.quantity}x')

#         writer.writerow([order.customer.name, r, order.total_payment, order.orderStatus])
#     response['Content-Disposition'] = 'attachment; filename="List of Orders.csv"'

#     return response

def Shipping(request):
    shipping = Barangay.objects.order_by('name')
    shipping_form = ShippingForm()
    if request.method == 'POST':
        shipping_form = ShippingForm(request.POST, request.FILES)
        if shipping_form.is_valid():
            shipping_form.save()
    context = {
        'shipping':shipping,
        'shipping_form':shipping_form
    }
    return render(request, 'AdminFolder/shipping.html', context)

def Policies(request):
    policy = Policy.objects.all()
    policy_form = PolicyForm()
    if request.method == 'POST':
        policy_form = PolicyForm(request.POST, request.FILES)
        if policy_form.is_valid():
            policy_form.save()
        # messages.success(request, "Rice Item has been successfully added!")
        # return redirect('Policy')
    context = {
        'policy':policy,
        'policy_form':policy_form
    }
    return render(request, 'AdminFolder/policies.html', context)

def Update_Policy(request, id):
    pol = Policy.objects.get(id=id)
    policy_form = PolicyForm(instance=pol)
    if request.method == 'POST':
        policy_form = PolicyForm(request.POST, instance=pol)
        if policy_form.is_valid():
            policy_form.save()
        # messages.success(request, "Rice Item has been updated!")
        return redirect('Policy')
    context = {
        'policy_form':policy_form,
        'pol':pol
    }
    return render(request, 'AdminFolder/update_policy.html', context)

def Update_Shipping(request, id):
    bar = Barangay.objects.get(id=id)
    shipping_form = ShippingForm(instance=bar)
    if request.method == 'POST':
        shipping_form = ShippingForm(request.POST, instance=bar)
        if shipping_form.is_valid():
            shipping_form.save()
        # messages.success(request, "Rice Item has been updated!")
        return redirect('Shipping')
    context = {
        'shipping_form':shipping_form,
    }
    return render(request, 'AdminFolder/updateShipping.html', context)

def search(request):
    if request.method == "POST":
        searched = request.POST['searched']
        orders = OrderDetails.objects.filter(customer__name__icontains=searched)
        return render(request, 'AdminFolder/search.html', {'searched':searched,
        'orders':orders})
    else:
        return render(request, 'AdminFolder/search.html', {})
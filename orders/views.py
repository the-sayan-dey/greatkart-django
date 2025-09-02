from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from carts.models import CartItem
from orders.models import Order, OrderProduct, Payment
from store.models import Product

from .forms import OrderForm
import datetime

import json

from django.core.mail import EmailMessage
from django.template.loader import render_to_string


# Create your views here.

def payments(request):
    body = json.loads(request.body)
    print(body)

    try:
        order = Order.objects.get(
            user=request.user,
            is_ordered=False,   # get un-ordered one
            order_number=body['orderID']
        )
    except Order.DoesNotExist:
        return HttpResponse("Order not found", status=404)

    # Save payment
    payment = Payment.objects.create(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )

    order.payment = payment
    order.is_ordered = True
    order.save()

    # move the cart items to order product table
    cart_items = CartItem.objects.filter(user=request.user)
    print("Cart items count:", cart_items.count())

    for item in cart_items:
        orderproduct = OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True,
        )
        # copy variations if exist
        orderproduct.variations.set(item.variations.all())
        orderproduct.save()

        # cart_item = CartItem.objects.get(id=item.id)
        # product_variation = cart_item.variations.all()
        # orderproduct = OrderProduct.objects.get(id = OrderProduct.id)
        # orderproduct.variations.set(product_variation)
    



    # reduce the quantity of sold products
        product = Product.objects.get(id = item.product_id)
        product.stock -= item.quantity
        product.save()


    # clear the cart 
    # CartItem.objects.filter(user = request.user).delete()
    cart_items.delete()


    # send order received email to the customer

    mail_subject = 'Thank you for ordering.'
    message = render_to_string('orders/order_received_email.html', {
        'user' : request.user,
        'order' : order,
    })

    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()


    # send order no and payment and transaction id bavck to senddata method  via json response
    data = {
        'order_number' : order.order_number,
        'transID' : payment.payment_id,

    }




    return JsonResponse(data)
    # return render(request, 'orders/payments.html')



'''

    def payments(request):
    body = json.loads(request.body)
    print(body)

    order = Order.objects.get(user = request.user, is_ordered = False, order_number = body['orderID'])

    # Store transaction details into payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )

    payment.save()

    order.payment = payment

    order.is_ordered = True
    order.save()

    # move the cart items to order product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        # orderproduct.product_id = request.product_id
        orderproduct.product = item.product
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True

        orderproduct.save()


    # reduce the quantity of sold products


    # clear the cart 


    # send order received email to the customer


    # send order no and payment and transaction id bavck to senddata method  via json response

    return render(request, 'orders/payments.html')

'''



def place_order(request, total = 0, quantity = 0):
    # return HttpResponse('place order ............ ok')
    current_user = request.user

    # if the cart count <= 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    tax = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax
    
    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            # store all the billing information inside order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            
            data.order_total = grand_total
            data.tax = tax

            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")  # e.g. 20250817

            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user,  is_ordered=False, order_number=order_number)

            context = {
                'order' : order,
                'cart_items' : cart_items,
                'total' : total,
                'tax' : tax,
                'grand_total' : grand_total,
            }

            # return redirect('checkout')
            return render(request, 'orders/payments.html', context)
        
    else:
        return redirect('checkout')
    



def order_complete(request):

    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number = order_number, is_ordered = True)
        ordered_products = OrderProduct.objects.filter(order_id = order.id)

        subtotal = 0

        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id = transID)

        context = {
            'order' : order,
            'ordered_products' : ordered_products,
            'order_number' : order.order_number,
            'transID' : payment.payment_id,
            'payment' : payment,
            'subtotal' : subtotal,
        }

        return render(request, 'orders/order_complete.html', context)
    
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

    

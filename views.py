from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
import mollie.api.client
from ecomerce import settings
from .models import Product
from .models import Category
from .models import ContactMessage
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings

mollie_client = mollie.api.client.Client()
mollie_client.set_api_key(settings.MOLLIE_API_KEY)

def create_payment(request):
    if request.method == 'POST':
        # Get total price (replace with your cart's total price logic)
        total = request.session.get('cart_total', 10.00)  # Example: 10.00 EUR

        # Create Mollie payment
        payment = mollie_client.payments.create({
            'amount': {'currency': 'EUR', 'value': f'{total:.2f}'},  # Total in EUR
            'description': 'Order payment',
            'redirectUrl': request.build_absolute_uri('/payment/success/'),  # Redirect to success page
            'webhookUrl': request.build_absolute_uri('/payment/webhook/'),   # Optional for payment status updates
        })

        # Redirect the user to Mollie's payment page
        return redirect(payment.get('checkoutUrl'))

    # Render the payment form
    return render(request, 'payment.html')

def payment_success(request):
    return HttpResponse("Payment successful! Thank you for your purchase.")

def payment_webhook(request):
    # Process Mollie's webhook (optional)
    payment_id = request.POST.get('id')
    if payment_id:
        payment = mollie_client.payments.get(payment_id)

        if payment.is_paid():
            # Payment successful, update your database, etc.
            return HttpResponse('Payment received')
        elif payment.is_pending():
            # Payment is pending
            return HttpResponse('Payment pending')
        elif payment.is_failed():
            # Payment failed
            return HttpResponse('Payment failed')

    return HttpResponse('Webhook received')



def home(request):
    featured_products = Product.objects.all()[:3] 
    return render(request, 'home.html', {'featured_products': featured_products})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def product_list(request):
    products = Product.objects.all()  
    return render(request, 'products.html', {'products': products})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        return HttpResponse("Thank you for your message!")
    return render(request, 'contact.html')

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)

    if str(product_id) not in cart:
        cart[str(product_id)] = {'name': product.name, 'price': str(product.price), 'quantity': 1}
    else:
        cart[str(product_id)]['quantity'] += 1

    request.session['cart'] = cart
    return redirect('cart_detail')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart

    return redirect('cart_detail')

def cart_detail(request):
    cart = request.session.get('cart', {})
    total = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
    return render(request, 'cart.html', {'cart': cart, 'total': total})

def checkout(request):
    if request.method == 'POST':
        return redirect('payment')  

    cart = request.session.get('cart', {})
    total = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
    request.session['cart_total'] = float(total)  
    return render(request, 'checkout.html', {'cart': cart, 'total': total})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})

def categories_processor(request):
    categories = Category.objects.all() 
    return {'categories': categories} 

def product_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'products.html', {'category': category, 'products': products}) 

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        ContactMessage.objects.create(name=name, email=email, message=message)

        return HttpResponse("Thank you for your message!")
    
    return render(request, 'contact.html')
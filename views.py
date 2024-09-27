from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
import json
import stripe
from ecomerce import settings
from .models import Product
from .models import Category
from .models import ContactMessage
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import JsonResponse, HttpResponseBadRequest

stripe.api_key = settings.STRIPE_SECRET_KEY 

def payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            payment_method_id = data.get('payment_method_id')

            if not payment_method_id:
                return JsonResponse({'error': 'Payment method ID is missing.'}, status=400)

            total = request.session.get('cart_total', 0)
            if total <= 0:
                return JsonResponse({'error': 'Invalid payment amount.'}, status=400)

            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),  
                currency='usd',
                payment_method=payment_method_id,
                confirm=True, 
            )

            request.session['cart'] = {}
            request.session['cart_total'] = 0

            return JsonResponse({'success': 'Payment successful!'})

        except stripe.error.CardError as e:
            return JsonResponse({'error': str(e.error.message)}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


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
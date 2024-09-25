from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
import stripe
from ecomerce import settings
from .models import Product

stripe.api_key = settings.STRIPE_SECRET_KEY  # Ensure Stripe secret key is set

# Home view
def home(request):
    # Fetch some featured products to display (you can customize this)
    featured_products = Product.objects.all()[:3]  # For example, fetching first 3 products
    return render(request, 'home.html', {'featured_products': featured_products})

# Register view
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
    products = Product.objects.all()  # Get all products from the database
    return render(request, 'products.html', {'products': products})

# Contact view
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        return HttpResponse("Thank you for your message!")
    return render(request, 'contact.html')

# Add to cart view
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)

    if str(product_id) not in cart:
        cart[str(product_id)] = {'name': product.name, 'price': str(product.price), 'quantity': 1}
    else:
        cart[str(product_id)]['quantity'] += 1

    request.session['cart'] = cart
    return redirect('cart_detail')

# Remove from cart view
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart

    return redirect('cart_detail')

# Cart detail view
def cart_detail(request):
    cart = request.session.get('cart', {})
    total = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
    return render(request, 'cart.html', {'cart': cart, 'total': total})

# Checkout view
def checkout(request):
    if request.method == 'POST':
        return redirect('payment')  # Redirect to payment page

    cart = request.session.get('cart', {})
    total = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
    request.session['cart_total'] = float(total)  # Store total for payment

    return render(request, 'checkout.html', {'cart': cart, 'total': total})


stripe.api_key = settings.STRIPE_SECRET_KEY

def payment(request):
    if request.method == 'POST':
        stripe_token = request.POST.get('stripeToken')

        if not stripe_token:
            return HttpResponse("Payment token is missing.", status=400)

        try:
            # Retrieve the total amount from session
            total = request.session.get('cart_total', 0)
            if total <= 0:
                return HttpResponse("Invalid payment amount.", status=400)

            # Create the charge with Stripe (amount is in cents)
            charge = stripe.Charge.create(
                amount=int(total * 100),  # Convert to cents
                currency='usd',
                description='Payment for order',
                source=stripe_token,
            )

            # Clear cart after successful payment
            request.session['cart'] = {}
            request.session['cart_total'] = 0

            return HttpResponse("Payment successful! Thank you for your purchase.")

        except stripe.error.CardError as e:
            return HttpResponse(f"Payment error: {e.error.message}", status=400)

    return render(request, 'payment.html', {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    })
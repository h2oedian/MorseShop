from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout 
from .forms import RegisterForm, EmailAuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .models import Product
from .forms import ProductForm


def is_admin(user):
    return user.is_staff  


@login_required
@user_passes_test(is_admin)
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = ProductForm()

    return render(request, "add_product.html", {"form": form})


def home(request):
    products = Product.objects.all()
    return render(request, 'auth_app/home.html', {'products': products})


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "ثبت‌نام با موفقیت انجام شد. حالا وارد شوید.")
            return redirect("login")
        else:
            messages.error(request, "ثبت‌نام ناموفق بود. لطفاً اطلاعات را بررسی کنید.")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, "با موفقیت وارد شدید.")
            return redirect("home")
        else:
            messages.error(request, "ورود ناموفق بود. اطلاعات را بررسی کنید.")
    else:
        form = EmailAuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout(request):
    auth_logout(request)
    messages.success(request, "با موفقیت خارج شدید.")
    return redirect("home")


def products(request):
    products = Product.objects.all()
    return render(request, 'auth_app/products.html', {'products': products})

def ProductDetail(request,pk):
    product = get_object_or_404(Product,pk=pk)
    return render(request,'auth_app/detail.html',{'product':product})


def cart(request):
    cart_items = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart_items.keys())
    cart_details = []

    for product in products:
        quantity = cart_items[str(product.id)]
        total_price = product.price * quantity
        cart_details.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price
        })

    total_cart_price = sum(item['total_price'] for item in cart_details)
    return render(request, 'auth_app/cart.html', {'cart_details': cart_details, 'total_cart_price': total_cart_price})


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1

    request.session['cart'] = cart
    messages.success(request, "محصول به سبد خرید اضافه شد.")
    return redirect('products')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]
        request.session['cart'] = cart
        messages.success(request, "محصول از سبد خرید حذف شد.")

    return redirect('cart')

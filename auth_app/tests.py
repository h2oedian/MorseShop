from urllib.parse import urlencode
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from .models import Order, OrderItem, Product




class ProductModelTests(TestCase):
    """
    تست‌های مربوط به مدل Product
    """
    def setUp(self):
        self.product = Product.objects.create(
            name="Laptop",
            description="Good laptop",
            price=1000,
        )

    def test_product_is_created_correctly(self):
        # Assert: بررسی اینکه محصول درست ساخته شده
        self.assertEqual(self.product.name, "Laptop")
        self.assertEqual(self.product.price, 1000)
        self.assertIsInstance(self.product, Product)

    def test_product_str_returns_name(self):
        # Assert: بررسی __str__
        self.assertEqual(str(self.product), "Laptop")


class OrderAndOrderItemModelTests(TestCase):
    """
    تست‌های مربوط به مدل‌های Order و OrderItem
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="zahra",
            email="zahra@example.com",
            password="12345",
        )

        self.product = Product.objects.create(
            name="Phone",
            description="Nice phone",
            price=500,
        )

        self.order = Order.objects.create(user=self.user, status="pending")

        # نکته: در این پروژه price داخل OrderItem قیمت لحظه خرید است
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=self.product.price,
        )

    def test_order_str_contains_order_id(self):
        self.assertIn("Order #", str(self.order))

    def test_order_item_total_price_property(self):
        # total_price = price * quantity
        self.assertEqual(self.item.total_price, 1000)

    def test_order_total_price_property(self):
        # total_price Order = جمع total_price آیتم‌ها
        self.assertEqual(self.order.total_price, 1000)


class HomeAndProductsViewsTests(TestCase):
    """
    تست صفحه اصلی و لیست محصولات
    """

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            name="Tablet",
            description="Nice tablet",
            price=300,
        )

    def test_home_page_returns_200(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_page_contains_product_name(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Tablet")

    def test_products_page_returns_200(self):
        # در این پروژه، products عملاً همان home را رندر می‌کند
        response = self.client.get(reverse("products"))
        self.assertEqual(response.status_code, 200)

    def test_product_detail_page_returns_200_and_contains_name(self):
        response = self.client.get(reverse("product_detail", args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tablet")


class RegisterLoginLogoutTests(TestCase):
    """
    تست ثبت‌نام / ورود / خروج
    """

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="12345",
        )

    def test_register_creates_user_and_redirects_to_login(self):
        # نکته آموزشی: RegisterForm ایمیل هم می‌خواهد
        response = self.client.post(
            reverse("register"),
            data={
                "username": "ali",
                "email": "ali@example.com",
                "password1": "StrongPass12345",
                "password2": "StrongPass12345",
            },
        )

        # بعد از ثبت‌نام صحیح باید به login ریدایرکت شود
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="ali").exists())

    def test_login_with_username_redirects(self):
        response = self.client.post(
            reverse("login"),
            data={"username": "testuser", "password": "12345"},
        )
        self.assertEqual(response.status_code, 302)

    def test_login_with_email_redirects(self):
        # چون EmailAuthenticationForm ایمیل را هم می‌پذیرد
        response = self.client.post(
            reverse("login"),
            data={"username": "testuser@example.com", "password": "12345"},
        )
        self.assertEqual(response.status_code, 302)

    def test_logout_redirects_to_home(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)


class CartAndCheckoutTests(TestCase):
    """
    تست‌های مربوط به سبد خرید و checkout
    """

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="12345",
        )

        self.product = Product.objects.create(
            name="Mouse",
            description="Wireless mouse",
            price=50,
        )

    def test_cart_page_returns_200(self):
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart_requires_authentication(self):
        """
        وقتی کاربر لاگین نیست، add_to_cart باید به login ریدایرکت کند
        و next را هم ست کند (طبق کد view).
        """
        login_url = reverse("login")
        referer = reverse("home")

        response = self.client.get(
            reverse("add_to_cart", args=[self.product.id]),
            HTTP_REFERER=referer,
        )

        self.assertEqual(response.status_code, 302)

        expected = f"{login_url}?{urlencode({'next': referer})}"
        self.assertEqual(response["Location"], expected)

    def test_add_to_cart_when_logged_in_adds_session_cart(self):
        self.client.login(username="buyer", password="12345")

        response = self.client.get(reverse("add_to_cart", args=[self.product.id]))
        self.assertEqual(response.status_code, 302)

        session = self.client.session
        cart = session.get("cart", {})
        self.assertIn(str(self.product.id), cart)
        self.assertEqual(cart[str(self.product.id)], 1)

    def test_remove_from_cart_deletes_item(self):
        self.client.login(username="buyer", password="12345")

        # Arrange: دستی در سشن سبد خرید می‌گذاریم
        session = self.client.session
        session["cart"] = {str(self.product.id): 2}
        session.save()

        # Act
        response = self.client.get(reverse("remove_from_cart", args=[self.product.id]))
        self.assertEqual(response.status_code, 302)

        # Assert
        session = self.client.session
        self.assertNotIn(str(self.product.id), session.get("cart", {}))

    def test_checkout_requires_login(self):
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 302)  # login_required

    def test_checkout_empty_cart_redirects_to_cart(self):
        self.client.login(username="buyer", password="12345")

        # cart خالی
        session = self.client.session
        session["cart"] = {}
        session.save()

        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("cart"))

    def test_checkout_creates_order_and_clears_cart(self):
        self.client.login(username="buyer", password="12345")

        # Arrange: cart با یک محصول
        session = self.client.session
        session["cart"] = {str(self.product.id): 3}
        session.save()

        # Act
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 302)

        # Assert: یک سفارش ساخته شده
        order = Order.objects.filter(user=self.user).order_by("-id").first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, "pending")

        # Assert: آیتم سفارش ساخته شده
        item = OrderItem.objects.filter(order=order).first()
        self.assertIsNotNone(item)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.price, self.product.price)

        # Assert: cart پاک شده
        session = self.client.session
        self.assertEqual(session.get("cart"), {})


class AddProductAccessTests(TestCase):
    """
    تست دسترسی به add_product (فقط admin/staff)
    """

    def setUp(self):
        self.client = Client()

        self.staff_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="12345",
            is_staff=True,
        )
        self.normal_user = User.objects.create_user(
            username="normal",
            email="normal@example.com",
            password="12345",
            is_staff=False,
        )

    def test_add_product_requires_login(self):
        response = self.client.get(reverse("add_product"))
        self.assertEqual(response.status_code, 302)

    def test_add_product_forbidden_for_non_staff(self):
        self.client.login(username="normal", password="12345")
        response = self.client.get(reverse("add_product"))
        # user_passes_test در صورت fail معمولاً ریدایرکت به login می‌دهد (یا 403 بسته به تنظیمات)
        # در این پروژه انتظار 302 منطقی است.
        self.assertEqual(response.status_code, 302)

    def test_add_product_page_accessible_for_staff(self):
        self.client.login(username="admin", password="12345")
        response = self.client.get(reverse("add_product"))
        self.assertEqual(response.status_code, 200)
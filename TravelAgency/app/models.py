from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CompanyInfo(models.Model):
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    history = models.TextField()
    founding_year = models.PositiveIntegerField()
    requisites = models.TextField(help_text="Реквизиты")

    def __str__(self):
        return f"Работаем с {self.founding_year} г."


class Vacancy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Country(models.Model):
    name = models.CharField(max_length=100)
    climate_summer = models.CharField(max_length=100)
    climate_winter = models.CharField(max_length=100)
    climate_spring = models.CharField(max_length=100)
    climate_autumn = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Hotel(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, default='')
    stars = models.PositiveSmallIntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.country.name})"


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)
    email = models.EmailField()
    birth_date = models.DateField()

    def __str__(self):
        return f"{self.last_name} ({self.position})"


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    birth_date = models.DateField()
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='clients')

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Tour(models.Model):
    title = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    duration_weeks = models.PositiveSmallIntegerField(choices=[(1, "1 неделя"), (2, "2 недели"), (4, "4 недели")])
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='tour_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} в {self.country.name} ({self.duration_weeks} нед.)"


class Promocode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    discount_percent = models.PositiveSmallIntegerField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.discount_percent}% для {self.tour.title}"


class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    departure_date = models.DateField()
    quantity = models.PositiveIntegerField(default=1)
    promo_code = models.ForeignKey(Promocode, on_delete=models.SET_NULL, null=True, blank=True)

    def total_price(self):
        price = self.quantity * self.tour.base_price
        if self.promo_code and self.promo_code.is_active:
            discount = price * self.promo_code.discount_percent / 100
            return price - discount
        return price

    def __str__(self):
        return f"Заказ №{self.id} от {self.client}"


class Review(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.client} на {self.tour}"


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    short_description = models.CharField(max_length=255, verbose_name="Краткое описание")
    content = models.TextField(verbose_name="Текст статьи")
    image = models.ImageField(upload_to='news_images/', blank=True, null=True, verbose_name="Изображение")
    published_at = models.DateTimeField(default=timezone.now, verbose_name="Дата публикации")

    def __str__(self):
        return self.title


class UserSessionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)

    def duration_minutes(self):
        if self.logout_time:
            return (self.logout_time - self.login_time).total_seconds() / 60
        return None

    def __str__(self):
        return f"{self.user.username} — {self.login_time.strftime('%Y-%m-%d %H:%M')} ➝ {self.logout_time.strftime('%H:%M') if self.logout_time else 'сессия активна'}"
import base64
import calendar
import io
import logging
from datetime import date
from decimal import Decimal
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import requests
from django import forms
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import (RegisterForm, SelectEmployeeForm, ReviewForm, 
                   OrderForm, TourForm, PromocodeForm)
from .models import (Client, Review, Vacancy, Tour, Employee, 
                    Order, Promocode, UserSessionLog, FAQ,
                    CompanyInfo, Article)

logger = logging.getLogger(__name__)


def main_view(request):
    latest_tour = Tour.objects.order_by('-id').first()
    return render(request, 'app/main.html', {'latest_tour': latest_tour})


def about_company_view(request):
    company = CompanyInfo.objects.first()
    return render(request, 'app/about_company.html', {'company': company})


def contacts_view(request):
    employees = Employee.objects.all()
    return render(request, 'app/contacts.html', {'employees': employees})


def faq_view(request):
    faqs = FAQ.objects.order_by('-created_at')
    return render(request, 'app/faq.html', {'faqs': faqs})


def news_view(request):
    articles = Article.objects.order_by('-published_at')
    return render(request, 'app/news.html', {'articles': articles})


def news_detail_view(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'app/news_detail.html', {'article': article})


def privacy_policy_view(request):
    return render(request, 'app/privacy_policy.html')


def vacancies_view(request):
    vacancies = Vacancy.objects.all().order_by('-created_at')
    return render(request, 'app/vacancies.html', {'vacancies': vacancies})

def clients_view(request):
    clients = Client.objects.all()
    return render(request, 'app/clients.html', {'clients': clients})


def tours_view(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'base_price')

    tours = Tour.objects.all()

    if query:
        tours = tours.filter(
            Q(title__icontains=query) |
            Q(country__name__icontains=query)
        )

    if sort_by in ['base_price', '-base_price']:
        tours = tours.order_by(sort_by)

    return render(request, 'app/tours.html', {
        'tours': tours, 
        'query': query,
        'sort_by': sort_by
    })


def tour_detail_view(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    weather = get_weather(tour.hotel.city)
    converted_price = convert_from_byn(tour.base_price, "USD")
    return render(request, 'app/tour_detail.html', {
        'tour': tour, 
        'weather': weather, 
        'converted_price': converted_price
    })


@staff_member_required
def tour_create_view(request):
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('tours')
    else:
        form = TourForm()
    return render(request, 'app/tour_form.html', {'form': form})


@staff_member_required
def tour_edit_view(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES, instance=tour)
        if form.is_valid():
            form.save()
            return redirect('tour_detail', pk=pk)
    else:
        form = TourForm(instance=tour)
    return render(request, 'app/tour_form.html', {'form': form, 'tour': tour})


@staff_member_required
def tour_delete_view(request, pk):
    tour = get_object_or_404(Tour, pk=pk)
    if request.method == 'POST':
        tour.delete()
        return redirect('tours')
    return render(request, 'app/tour_confirm_delete.html', {'tour': tour})


def tour_distribution_chart(request):
    tour_stats = Order.objects.values('tour__title').annotate(total=Count('id'))
    labels = [item['tour__title'] for item in tour_stats]
    values = [item['total'] for item in tour_stats]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')

    return render(request, 'app/tour_chart.html', {'chart': graphic})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Client.objects.create(
                user=user,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                patronymic=form.cleaned_data.get("patronymic", ""),
                address=form.cleaned_data["address"],
                phone=form.cleaned_data["phone"],
                birth_date=form.cleaned_data["birth_date"]
            )
            login(request, user)
            return redirect("select_employee")
    else:
        form = RegisterForm()
    return render(request, "app/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("main")
    else:
        form = AuthenticationForm()
    return render(request, "app/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("main")


@login_required
def profile_view(request):
    try:
        client = Client.objects.get(user=request.user)
        orders = Order.objects.filter(client=client)
        used_promo_ids = orders.exclude(promo_code__isnull=True).values_list('promo_code__id', flat=True)
        used_promos = Promocode.objects.filter(id__in=used_promo_ids)
        available_promos = Promocode.objects.filter(
            is_active=True,
            valid_until__gte=date.today()
        ).exclude(id__in=used_promo_ids)
    except Client.DoesNotExist:
        orders = []
        used_promos = []
        available_promos = []
    return render(request, 'app/profile.html', {
        'orders': orders,
        'used_promos': used_promos,
        'available_promos': available_promos
    })


@login_required
def select_employee_view(request):
    try:
        client = request.user.client
    except Client.DoesNotExist:
        return HttpResponseForbidden("Вы не зарегистрированы как клиент.")

    if request.method == 'POST':
        form = SelectEmployeeForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = SelectEmployeeForm(instance=client)

    return render(request, 'app/select_employee.html', {'form': form})


@login_required
def tour_booking_view(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)

    try:
        client = Client.objects.get(user=request.user)
    except Client.DoesNotExist:
        return HttpResponseForbidden("Вы не зарегистрированы как клиент.")

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.tour = tour
            order.client = client
            order.promo_code = form.cleaned_data.get("promo_code")
            order.save()
            return redirect('profile')
    else:
        form = OrderForm()

    return render(request, 'app/tour_booking.html', {'form': form, 'tour': tour})


@login_required
def add_review_view(request):
    if request.method == "POST":
        form = ReviewForm(request.POST, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.client = Client.objects.get(user=request.user)
            review.save()
            return redirect('my_reviews')
    else:
        form = ReviewForm(user=request.user)
    return render(request, 'app/add_review.html', {'form': form})


@login_required
def reviews_view(request):
    reviews = Review.objects.select_related('client', 'tour')
    return render(request, 'app/reviews.html', {'reviews': reviews})


@login_required
def my_reviews_view(request):
    try:
        client = Client.objects.get(user=request.user)
        reviews = Review.objects.filter(client=client)
    except Client.DoesNotExist:
        reviews = []

    return render(request, 'app/my_reviews.html', {'reviews': reviews})


@login_required
def employee_dashboard_view(request):
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return HttpResponseForbidden("Вы не являетесь сотрудником.")

    orders = Order.objects.filter(employee=employee) if employee else []
    clients = Client.objects.filter(employee=employee)
    tours = Tour.objects.all()
    return render(request, 'app/employee_dashboard.html', {
        'employee': employee,
        'orders': orders,
        'clients': clients,
        'tours': tours
    })


@staff_member_required
def add_promocode_view(request):
    if request.method == 'POST':
        form = PromocodeForm(request.POST)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.created_by = request.user
            promo.save()
            return redirect('employee_dashboard')
    else:
        form = PromocodeForm()
    return render(request, 'app/add_promocode.html', {'form': form})


@login_required
def statistics_view(request):
    user = request.user

    if not user.is_staff and not Employee.objects.filter(user=user).exists():
        return render(request, 'app/access_denied.html')

    logs = UserSessionLog.objects.exclude(logout_time__isnull=True)
    data = []

    for log in logs:
        duration = log.duration_minutes()
        if duration:
            data.append({'user': log.user.username, 'duration_minutes': duration})

    df = pd.DataFrame(data)
    if df.empty:
        average = 0
    else:
        average = df['duration_minutes'].mean()

    plt.figure(figsize=(10, 6))
    if not df.empty:
        plt.bar(df['user'], df['duration_minutes'], color='skyblue', label='Пользователь')
        plt.axhline(y=average, color='red', linestyle='--', label=f'Среднее: {average:.1f} мин')
    plt.title('Время, проведённое пользователями на сайте')
    plt.ylabel('Минуты')
    plt.xlabel('Пользователи')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    chart_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return render(request, 'app/statistics.html', {'chart_data': chart_data})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip if ip else None


def get_timezone_by_ip(ip):
    if not ip or ip.startswith(('127.', '10.', '192.168.')):
        return None

    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip}?fields=timezone',
            timeout=2
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('timezone')
    except requests.RequestException:
        return None


def time_info_view(request):
    now_utc = timezone.now()
    client_ip = get_client_ip(request)
    user_timezone = get_timezone_by_ip(client_ip)
    
    if not user_timezone:
        user_timezone = timezone.get_current_timezone_name()

    cal = calendar.TextCalendar(calendar.MONDAY)
    calendar_text = cal.formatmonth(now_utc.year, now_utc.month)
    tours = Tour.objects.all()

    return render(request, 'app/time_info.html', {
        'now': now_utc,
        'user_timezone': user_timezone,
        'calendar_text': calendar_text,
        'tours': tours,
        'client_ip': client_ip
    })


def get_weather(city):
    api_key = 'ab032113dbdc460da821bddb431f0dfe'
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            'temp': data['main']['temp'],
            'desc': data['weather'][0]['description'],
        }
    return None


def get_exchange_rate(currency_code):
    url = f"https://www.nbrb.by/api/exrates/rates/{currency_code}?parammode=2"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rate = Decimal(str(data["Cur_OfficialRate"]))
        scale = Decimal(str(data["Cur_Scale"]))
        return rate / scale
    except Exception as e:
        logger.error(f"Ошибка при получении курса валюты {currency_code}: {e}")
        return None


def convert_from_byn(amount_byn, to_currency="USD"):
    rate = get_exchange_rate(to_currency)
    if rate is None or rate == 0:
        return None
    return round(amount_byn / rate, 2)
from django.test import TestCase
from django.test import Client as TestClient  # избегаем конфликта имен
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

from app.models import (
    Country, Hotel, Client as TourClient, Employee,
    Tour, Review, Promocode, Order
)


class CountryModelTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name='France',
            climate_summer='Warm',
            climate_winter='Cold',
            climate_spring='Mild',
            climate_autumn='Cool'
        )

    def test_country_str(self):
        self.assertEqual(str(self.country), 'France')


class HotelModelTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name='Italy', climate_summer='Hot',
            climate_winter='Mild', climate_spring='Warm',
            climate_autumn='Cool'
        )
        self.hotel = Hotel.objects.create(
            name='Hotel Roma',
            country=self.country,
            city='Rome',
            stars=4,
            price_per_day=Decimal('200.00')
        )

    def test_hotel_str(self):
        self.assertEqual(str(self.hotel), 'Hotel Roma (Italy)')


class EmployeeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='employee1', password='pass')
        self.employee = Employee.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            position='Manager',
            phone='123456789',
            email='john@example.com',
            birth_date='1990-01-01'
        )

    def test_employee_str(self):
        self.assertEqual(str(self.employee), 'Doe (Manager)')


class ClientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='client1', password='pass')
        self.employee = Employee.objects.create(
            first_name='Anna',
            last_name='Ivanova',
            position='Agent',
            phone='987654321',
            email='anna@example.com',
            birth_date='1985-02-02'
        )
        self.client = TourClient.objects.create(
            user=self.user,
            first_name='Alice',
            last_name='Smith',
            patronymic='Lee',
            address='123 Main St',
            phone='555-1234',
            birth_date='2000-01-01',
            employee=self.employee
        )

    def test_client_str(self):
        self.assertEqual(str(self.client), 'Smith Alice')


class TourModelTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name='Spain', climate_summer='Hot',
            climate_winter='Cool', climate_spring='Mild',
            climate_autumn='Warm'
        )
        self.hotel = Hotel.objects.create(
            name='Hotel Madrid',
            country=self.country,
            city='Madrid',
            stars=3,
            price_per_day=150
        )
        self.tour = Tour.objects.create(
            title='Sunny Spain',
            country=self.country,
            hotel=self.hotel,
            duration_weeks=2,
            base_price=1000,
            description='Nice tour in Spain'
        )

    def test_tour_str(self):
        self.assertEqual(str(self.tour), 'Sunny Spain в Spain (2 нед.)')


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='client1')
        self.employee = Employee.objects.create(
            first_name='Emp', last_name='Loy',
            position='Guide', phone='123',
            email='emp@test.com', birth_date='1980-01-01'
        )
        self.client = TourClient.objects.create(
            user=self.user, first_name='Review', last_name='Tester',
            address='Nowhere', phone='000', birth_date='2000-01-01',
            employee=self.employee
        )
        self.country = Country.objects.create(
            name='Germany', climate_summer='Mild',
            climate_winter='Cold', climate_spring='Cool',
            climate_autumn='Foggy'
        )
        self.hotel = Hotel.objects.create(
            name='Berlin Inn', country=self.country,
            city='Berlin', stars=4, price_per_day=180
        )
        self.tour = Tour.objects.create(
            title='Berlin Tour', country=self.country,
            hotel=self.hotel, duration_weeks=1, base_price=800,
            description='Nice one'
        )
        self.review = Review.objects.create(
            client=self.client, tour=self.tour,
            rating=4, text='Great!'
        )

    def test_review_str(self):
        self.assertIn('Отзыв от', str(self.review))


class PromoCodeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='adminuser')
        self.country = Country.objects.create(
            name='Portugal', climate_summer='Hot',
            climate_winter='Mild', climate_spring='Warm',
            climate_autumn='Cool'
        )
        self.hotel = Hotel.objects.create(
            name='Lisbon Stay', country=self.country,
            city='Lisbon', stars=3, price_per_day=120
        )
        self.tour = Tour.objects.create(
            title='Lisbon Adventure', country=self.country,
            hotel=self.hotel, duration_weeks=2,
            base_price=1100, description='Explore Lisbon'
        )
        self.promo = Promocode.objects.create(
            code='SAVE20', tour=self.tour, discount_percent=20,
            created_by=self.user, is_active=True,
            valid_until=date(2030, 1, 1)
        )

    def test_promo_str(self):
        self.assertEqual(str(self.promo), 'SAVE20 - 20% для Lisbon Adventure')


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='orderuser')
        self.employee = Employee.objects.create(
            first_name='Oleg', last_name='Ivanov',
            position='Sales', phone='999',
            email='oleg@ex.com', birth_date='1985-03-03'
        )
        self.client = TourClient.objects.create(
            user=self.user, first_name='Test', last_name='Client',
            address='Test St', phone='123',
            birth_date='2001-01-01', employee=self.employee
        )
        self.country = Country.objects.create(
            name='Japan', climate_summer='Hot',
            climate_winter='Snowy', climate_spring='Warm',
            climate_autumn='Cool'
        )
        self.hotel = Hotel.objects.create(
            name='Tokyo Stay', country=self.country,
            city='Tokyo', stars=5, price_per_day=300
        )
        self.tour = Tour.objects.create(
            title='Tokyo Trip', country=self.country,
            hotel=self.hotel, duration_weeks=1,
            base_price=2000, description='Visit Tokyo'
        )
        self.promo = Promocode.objects.create(
            code='JAPAN10', tour=self.tour, discount_percent=10,
            created_by=self.user, is_active=True
        )
        self.order = Order.objects.create(
            client=self.client, tour=self.tour, employee=self.employee,
            departure_date=date(2025, 6, 1), quantity=2,
            promo_code=self.promo
        )

    def test_order_str(self):
        self.assertIn('Заказ #', str(self.order))

    def test_total_price_with_discount(self):
        expected_price = Decimal('4000') * (1 - Decimal('10') / 100)
        self.assertEqual(self.order.total_price(), expected_price)

class ViewsTest(TestCase):
    def setUp(self):
        self.client = TestClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.employee = Employee.objects.create(
            first_name='Emp', last_name='Loyee',
            position='Agent', phone='123456789',
            email='emp@example.com', birth_date='1990-01-01'
        )
        self.country = Country.objects.create(
            name='Spain', climate_summer='Hot',
            climate_winter='Cold', climate_spring='Mild',
            climate_autumn='Cool'
        )
        self.hotel = Hotel.objects.create(
            name='Madrid Inn', country=self.country,
            city='Madrid', stars=4, price_per_day=100
        )
        self.tour = Tour.objects.create(
            title='Madrid Tour', country=self.country,
            hotel=self.hotel, duration_weeks=2,
            base_price=1000, description='A nice trip'
        )
        self.client_data = TourClient.objects.create(
            user=self.user, first_name='Test', last_name='Client',
            address='123 Test St', phone='555555',
            birth_date='2000-01-01', employee=self.employee
        )
        self.client.login(username='testuser', password='12345')

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_tour_list_view(self):
        response = self.client.get(reverse('tour_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Madrid Tour')

    def test_tour_detail_view(self):
        response = self.client.get(reverse('tour_detail', args=[self.tour.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Madrid Tour')



    def test_create_promo_code(self):
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('create_promo'), {
            'tour': self.tour.id,
            'code': 'DISCOUNT25',
            'discount_percent': 25,
            'valid_until': '2030-01-01'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Promocode.objects.filter(code='DISCOUNT25').exists())

    def test_my_reviews_view(self):
        Review.objects.create(tour=self.tour, client=self.client_data, rating=5, text='Amazing!')
        response = self.client.get(reverse('my_reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amazing!')

    def test_all_reviews_view(self):
        Review.objects.create(tour=self.tour, client=self.client_data, rating=5, text='Perfect tour!')
        response = self.client.get(reverse('all_reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Perfect tour!')

    def test_select_employee_get(self):
        response = self.client.get(reverse('select_employee'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Выберите сотрудника') 

    def test_chart_view(self):
        response = self.client.get(reverse('tour_chart'))
        self.assertEqual(response.status_code, 200)

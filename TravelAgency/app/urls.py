from django.urls import path,re_path
from . import views

urlpatterns = [
    path('', views.main_view, name='main'),  
    path('tours/', views.tours_view, name='tours'),  
    path('tours/<int:pk>/', views.tour_detail_view, name='tour_detail'),
    path('clients/', views.clients_view, name='clients'), 
    path('register/', views.register_view, name='register'), 
    path('login/', views.login_view, name='login'), 
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('tour/<int:tour_id>/booking/', views.tour_booking_view, name='tour_booking'),
    path('dashboard/', views.employee_dashboard_view, name='employee_dashboard'),
    path("select-employee/", views.select_employee_view, name="select_employee"),
    path('reviews/', views.reviews_view, name='reviews'),
    path('add_review/', views.add_review_view, name='add_review'),
    path('my_reviews/', views.my_reviews_view, name='my_reviews'),
    path('add_promocode/', views.add_promocode_view, name='add_promocode'),
    re_path(r'^chart/$', views.tour_distribution_chart, name='tour_chart'),
    re_path(r'^privacy/$', views.privacy_policy_view, name='privacy_policy'),
    re_path(r'^vacancies/$', views.vacancies_view, name='vacancies'),
    re_path(r'^tours/create/$', views.tour_create_view, name='tour_create'),
    path('tours/<int:pk>/edit/', views.tour_edit_view, name='tour_edit'),
    path('tours/<int:pk>/delete/', views.tour_delete_view, name='tour_delete'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('time_info/', views.time_info_view, name='time_info'),
    path('faq/', views.faq_view, name='faq'),
    path('about_company/', views.about_company_view, name='about_company'),
    path('news/', views.news_view, name='news'),
    path('news/<int:pk>/', views.news_detail_view, name='news_detail'),
    path('contacts/', views.contacts_view, name='contacts'),
]


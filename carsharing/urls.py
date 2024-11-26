from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('users/', views.user_list, name='user_list'),
    path('cars/', views.car_list, name='car_list'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('users/add/', views.add_user, name='add_user'),
    path('cars/add/', views.add_car, name='add_car'),
    path('bookings/add/', views.add_booking, name='add_booking'),
    path('users/edit/<int:pk>/', views.edit_user, name='edit_user'),
    path('cars/edit/<int:pk>/', views.edit_car, name='edit_car'),
    path('bookings/edit/<int:pk>/', views.edit_booking, name='edit_booking'),
    path('users/delete/<int:pk>/', views.delete_user, name='delete_user'),
    path('cars/delete/<int:pk>/', views.delete_car, name='delete_car'),
    path('bookings/delete/<int:pk>/', views.delete_booking, name='delete_booking'),
    path('statistics/total_income', views.total_income, name='total_income'),
    path('statistics/most_popular_cars', views.most_popular_cars, name='most_popular_cars'),
    path('user/<int:user_id>/bookings/', views.user_bookings, name='user_bookings'),
    path('car/<int:car_id>/bookings/', views.car_bookings, name='car_bookings'),
]

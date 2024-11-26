from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm, CarForm, BookingForm
from .models import User, Car, Booking
from django.db.models import Sum, Count


def index(request):
    return render(request, 'carsharing/index.html')

def user_list(request):
    users = User.objects.all()
    return render(request, 'carsharing/user_list.html', {'users': users})

def car_list(request):
    cars = Car.objects.all()
    return render(request, 'carsharing/car_list.html', {'cars': cars})

def booking_list(request):
    bookings = Booking.objects.all()
    return render(request, 'carsharing/booking_list.html', {'bookings': bookings})

def add_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'carsharing/add_user.html', {'form': form})

def add_car(request):
    if request.method == "POST":
        form = CarForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('car_list')
    else:
        form = CarForm()
    return render(request, 'carsharing/add_car.html', {'form': form})


def add_booking(request):
    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            car = form.cleaned_data['car']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            overlapping_bookings = Booking.objects.filter(
                car=car,
                start_date__lt=end_date,
                end_date__gt=start_date
            )

            if overlapping_bookings.exists():
                form.add_error(None, 'This car is already booked for the selected period.')
            else:
                form.save()
                return redirect('booking_list')

    else:
        form = BookingForm()

    return render(request, 'carsharing/add_booking.html', {'form': form})

def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'carsharing/edit_user.html', {'form': form, 'user': user})


def edit_car(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = CarForm(request.POST, instance=car)
        if form.is_valid():
            form.save()
            return redirect('car_list')
    else:
        form = CarForm(instance=car)
    return render(request, 'carsharing/edit_car.html', {'form': form, 'car': car})


def edit_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('booking_list')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'carsharing/edit_booking.html', {'form': form, 'booking': booking})

def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.delete()
        return redirect('user_list')
    return render(request, 'carsharing/confirm_delete.html', {'object': user})


def delete_car(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        car.delete()
        return redirect('car_list')
    return render(request, 'carsharing/confirm_delete.html', {'object': car})


def delete_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        booking.delete()
        return redirect('booking_list')
    return render(request, 'carsharing/confirm_delete.html', {'object': booking})


def total_income(request):
    total_income = None
    bookings = None

    if 'start_date' in request.GET and 'end_date' in request.GET:
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']

        bookings = Booking.objects.filter(
            start_date__gte=start_date,
            end_date__lte=end_date,
            status='completed'
        )

        total_income = bookings.aggregate(total_income=Sum('total_price'))['total_income']

    return render(request, 'carsharing/total_income.html', {
        'total_income': total_income,
        'bookings': bookings
    })


def most_popular_cars(request):
    cars_stats = Car.objects.annotate(bookings_count=Count('booking')).order_by('-bookings_count')
    return render(request, 'carsharing/most_popular_cars.html', {'cars_stats': cars_stats})

def user_bookings(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    bookings = Booking.objects.filter(client=user)
    return render(request, 'carsharing/user_bookings.html', {'user': user, 'bookings': bookings})

def car_bookings(request, car_id):
    car = get_object_or_404(Car, pk=car_id)
    bookings = Booking.objects.filter(car=car)
    return render(request, 'carsharing/car_bookings.html', {'car': car, 'bookings': bookings})

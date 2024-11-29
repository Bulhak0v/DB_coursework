from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm, CarForm, BookingForm, UserRegistrationForm, UserLoginForm, BookingStepOneForm, BookingStepTwoForm
from .models import User, Car, Booking, Branch
from django.db.models import Sum, Count
from datetime import datetime


def index(request):
    if 'user_id' not in request.session:
        return redirect('login')
    user_id = request.session['user_id']
    user = User.objects.get(user_id=user_id)
    if not user.is_superuser:
        return render(request, 'carsharing/user/user_main_page.html', {'user': user})
    else:
        return render(request, 'carsharing/admin/index.html', {'user': user})


def register_page(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'carsharing/register.html', {'form': form})


def login_page(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(email=email)
                if user.password == password:
                    request.session['user_id'] = user.user_id
                    return redirect('index')
                else:
                    form.add_error('password', 'Incorrect Password')
            except User.DoesNotExist:
                form.add_error('email', 'There is no user with this email')

    else:
        form = UserLoginForm()

    return render(request, 'carsharing/login.html', {'form': form})


def logout_page(request):
    request.session.flush()
    return redirect('login')


def user_list(request):
    users = User.objects.all()
    return render(request, 'carsharing/admin/user_list.html', {'users': users})


def car_list(request):
    cars = Car.objects.all()
    return render(request, 'carsharing/admin/car_list.html', {'cars': cars})


def booking_list(request):
    bookings = Booking.objects.all()
    return render(request, 'carsharing/admin/booking_list.html', {'bookings': bookings})


def branches_list(request):
    branches = Branch.objects.all()
    return render(request, 'carsharing/admin/branches_list.html', {'branches': branches})


def add_user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'carsharing/admin/add_user.html', {'form': form})


def add_car(request):
    if request.method == "POST":
        form = CarForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('car_list')
    else:
        form = CarForm()
    return render(request, 'carsharing/admin/add_car.html', {'form': form})


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

    return render(request, 'carsharing/admin/add_booking.html', {'form': form})


def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'carsharing/admin/edit_user.html', {'form': form, 'user': user})


def edit_car(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = CarForm(request.POST, instance=car)
        if form.is_valid():
            form.save()
            return redirect('car_list')
    else:
        form = CarForm(instance=car)
    return render(request, 'carsharing/admin/edit_car.html', {'form': form, 'car': car})


def edit_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('booking_list')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'carsharing/admin/edit_booking.html', {'form': form, 'booking': booking})


def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.delete()
        return redirect('user_list')
    return render(request, 'carsharing/admin/confirm_delete.html', {'object': user})


def delete_car(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        car.delete()
        return redirect('car_list')
    return render(request, 'carsharing/admin/confirm_delete.html', {'object': car})


def delete_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        booking.delete()
        return redirect('booking_list')
    return render(request, 'carsharing/admin/confirm_delete.html', {'object': booking})


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

    return render(request, 'carsharing/admin/total_income.html', {
        'total_income': total_income,
        'bookings': bookings
    })


def most_popular_cars(request):
    cars_stats = Car.objects.annotate(bookings_count=Count('booking')).order_by('-bookings_count')
    return render(request, 'carsharing/admin/most_popular_cars.html', {'cars_stats': cars_stats})


def user_bookings(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    bookings = Booking.objects.filter(client=user)
    return render(request, 'carsharing/admin/user_bookings.html', {'user': user, 'bookings': bookings})


def car_bookings(request, car_id):
    car = get_object_or_404(Car, pk=car_id)
    bookings = Booking.objects.filter(car=car)
    return render(request, 'carsharing/admin/car_bookings.html', {'car': car, 'bookings': bookings})


def user_info(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user = get_object_or_404(User, pk=user_id)
    bookings = Booking.objects.filter(client=user)
    if not user.is_superuser:
        return render(request, 'carsharing/user/user_account_info.html', {'user': user, 'bookings': bookings})
    else:
        return render(request, 'carsharing/admin/user_info.html', {'user': user, 'bookings': bookings})


def user_cars(request):
    cars = Car.objects.all()
    return render(request, 'carsharing/user/user_cars_page.html', {'cars': cars})


def user_make_booking_step_one(request):
    if request.method == 'POST':
        form = BookingStepOneForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            pickup_branch = form.cleaned_data['pickup_branch']
            return_branch = form.cleaned_data['return_branch']

            start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

            request.session['start_date'] = start_date_str
            request.session['end_date'] = end_date_str
            request.session['pickup_branch'] = pickup_branch.branch_id
            request.session['return_branch'] = return_branch.branch_id

            return redirect('user_make_booking_step_two')
    else:
        form = BookingStepOneForm()

    return render(request, 'carsharing/user/user_booking_step_one.html', {'form': form})


def user_make_booking_step_two(request):
    # Отримуємо значення з сесії
    start_date_str = request.session.get('start_date')
    end_date_str = request.session.get('end_date')

    # Конвертуємо їх у datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')

    pickup_branch_id = request.session.get('pickup_branch')
    pickup_branch = Branch.objects.get(branch_id=pickup_branch_id)

    return_branch_id = request.session.get('return_branch')

    available_cars = Car.objects.filter(branch=pickup_branch)

    if request.method == 'POST':
        form = BookingStepTwoForm(request.POST)
        form.fields['car'].queryset = available_cars
        if form.is_valid():
            selected_car = form.cleaned_data['car']
            total_days = (end_date - start_date).days
            total_price = total_days * selected_car.price_per_day

            # Створюємо бронювання
            Booking.objects.create(
                client=User.objects.get(pk=request.session['user_id']),
                car=selected_car,
                start_date=start_date,
                end_date=end_date,
                total_price=total_price,
                status='reserved',
                pickup_location=pickup_branch_id,
                return_location=return_branch_id
            )

            return redirect('user_info')
    else:
        form = BookingStepTwoForm()
        form.fields['car'].queryset = available_cars

    return render(request, 'carsharing/user/user_booking_step_two.html', {
        'form': form,
        'available_cars': available_cars,
    })
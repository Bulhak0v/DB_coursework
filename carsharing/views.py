from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm, CarForm, BookingForm, UserRegistrationForm, UserLoginForm, BookingStepOneForm, \
    BookingStepTwoForm, BookingStepThreeForm
from .models import User, Car, Booking, Branch, Additional_Services, Booking_Services, Rental_Agreement, Promo_Code
from django.db.models import Sum, Count
from datetime import datetime
from django.utils.timezone import make_aware, now
import random


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
    branches = {branch.branch_id: branch for branch in Branch.objects.all()}

    for booking in bookings:
        booking.pickup_branch = branches.get(booking.pickup_location)
        booking.return_branch = branches.get(booking.return_location)

    return render(request, 'carsharing/admin/booking_list.html', {
        'bookings': bookings,
    })


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


def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.status == 'cancelled':
        return redirect('user_info')

    if request.method == "POST":
        booking.status = 'Cancelled'
        booking.save()
        return redirect('user_info')
    return render(request, 'carsharing/user/confirm_cancel.html', {'object': booking})


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

            current_datetime = now()

            if start_date.tzinfo is None or start_date.tzinfo.utcoffset(start_date) is None:
                start_date = make_aware(start_date)

            if end_date.tzinfo is None or end_date.tzinfo.utcoffset(end_date) is None:
                end_date = make_aware(end_date)

            if end_date < start_date:
                form.add_error('end_date', 'End date cannot be earlier than start date.')
            elif start_date < current_datetime:
                form.add_error('start_date', 'Start date cannot be in the past.')

            else:
                # Зберігаємо дати та інші дані в сесії
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
    start_date_str = request.session.get('start_date')
    end_date_str = request.session.get('end_date')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')

    pickup_branch_id = request.session.get('pickup_branch')
    pickup_branch = Branch.objects.get(branch_id=pickup_branch_id)

    branch_cars = Car.objects.filter(branch=pickup_branch)

    unavailable_cars = Booking.objects.filter(
        car__in=branch_cars,
        start_date__lt=end_date,
        end_date__gt=start_date
    ).exclude(status='cancelled').values_list('car', flat=True)

    available_cars = branch_cars.exclude(car_id__in=unavailable_cars)

    if request.method == 'POST':
        form = BookingStepTwoForm(request.POST)
        form.fields['car'].queryset = available_cars
        if form.is_valid():
            selected_car = form.cleaned_data['car']
            request.session['selected_car_id'] = selected_car.car_id

            total_days = (end_date - start_date).days
            total_price = total_days * selected_car.price_per_day
            request.session['total_price'] = total_price
            request.session['pickup_branch'] = pickup_branch_id
            request.session['return_branch'] = request.session.get('return_branch')
            request.session['start_date'] = start_date_str
            request.session['end_date'] = end_date_str

            return redirect('user_booking_step_three')
    else:
        form = BookingStepTwoForm()
        form.fields['car'].queryset = available_cars

    return render(request, 'carsharing/user/user_booking_step_two.html', {
        'form': form,
        'available_cars': available_cars,
    })


def user_make_booking_step_three(request):
    start_date_str = request.session.get('start_date')
    end_date_str = request.session.get('end_date')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')

    selected_car_id = Car.objects.get(car_id=request.session.get('selected_car_id'))

    pickup_branch_id = request.session.get('pickup_branch')
    pickup_branch = Branch.objects.get(branch_id=pickup_branch_id)

    return_branch_id = request.session.get('return_branch')
    return_branch = Branch.objects.get(branch_id=return_branch_id)

    if request.method == 'POST':
        form = BookingStepThreeForm(request.POST)
        if form.is_valid():
            booking = Booking.objects.create(
                client=User.objects.get(pk=request.session['user_id']),
                car=selected_car_id,
                start_date=start_date,
                end_date=end_date,
                total_price=request.session.get('total_price'),
                status='reserved',
                pickup_location=pickup_branch_id,
                return_location=return_branch_id,
            )

            selected_services = form.cleaned_data['services']
            for service in selected_services:
                Booking_Services.objects.create(
                    booking=booking,
                    service=service,
                    services_number=1
                )

            total_price = booking.total_price
            for service in selected_services:
                total_price += service.price
            booking.total_price = total_price
            booking.save()

            return redirect('user_booking_step_four', booking_id=booking.booking_id)

    else:
        form = BookingStepThreeForm()

    return render(request, 'carsharing/user/user_booking_step_three.html', {
        'form': form,
        'selected_car': selected_car_id,
        'pickup_branch': pickup_branch,
        'return_branch': return_branch,
    })


def user_make_booking_step_four(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)

    def generate_agreement_number():
        while True:
            number = ''.join(random.choices('0123456789', k=10))
            if not Rental_Agreement.objects.filter(agreement_number=number).exists():
                return number

    agreement_number = generate_agreement_number()
    request.session['agreement_number'] = agreement_number

    payment_sum = request.session.get('payment_sum', float(booking.total_price))
    promo_code = None
    discount = 0

    if request.method == 'POST' and 'apply_promo_code' in request.POST:
        if 'promo_code' in request.session:
            context = {
                'error_message': 'Промокод вже було застосовано.',
                'agreement_number': agreement_number,
                'signature_date': now(),
                'payment_sum': payment_sum,
                'booking': booking,
                'promo_code': promo_code,
                'discount': discount,
            }
            return render(request, 'carsharing/user/rental_agreement.html', context)

        entered_code = request.POST.get('promo_code', '').strip()
        try:
            promo_code = Promo_Code.objects.get(code=entered_code, end_date__gte=now().date())
            discount = promo_code.discount
            payment_sum = payment_sum * (100 - discount) / 100
            request.session['payment_sum'] = payment_sum
            request.session['promo_code'] = promo_code.promo_code_id
            booking.total_price = payment_sum
            booking.save()
        except Promo_Code.DoesNotExist:
            context = {
                'error_message': 'Введено недійсний промокод.',
                'agreement_number': agreement_number,
                'signature_date': now(),
                'payment_sum': payment_sum,
                'booking': booking,
                'promo_code': promo_code,
                'discount': discount,
            }
            return render(request, 'carsharing/user/rental_agreement.html', context)

    request.session['payment_sum'] = payment_sum
    context = {
        'agreement_number': agreement_number,
        'signature_date': now(),
        'payment_sum': payment_sum,
        'booking': booking,
        'promo_code': promo_code,
        'discount': discount,
    }
    return render(request, 'carsharing/user/rental_agreement.html', context)


def confirm_rental_agreement(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    agreement_number = request.session.get('agreement_number')
    payment_sum = request.session.get('payment_sum')
    if payment_sum is None:
        return redirect('user_booking_step_four', booking_id=booking_id)

    prom_code = request.session.get('promo_code')
    promo_code = None
    if prom_code:
        promo_code = get_object_or_404(Promo_Code, promo_code_id=prom_code)

    Rental_Agreement.objects.create(
        agreement_number=agreement_number,
        signature_date=now(),
        payment_sum=payment_sum,
        booking=booking,
        promo_code=promo_code,
    )

    del request.session['agreement_number']
    del request.session['payment_sum']
    request.session.pop('promo_code', None)
    return redirect('user_info')

def cancel_rental_agreement(request, booking_id=None):
    booking_id = booking_id or request.session.get('current_booking_id')
    if booking_id:
        booking = get_object_or_404(Booking, booking_id=booking_id)
        booking.delete()
        request.session.pop('current_booking_id', None)
        del request.session['agreement_number']
        del request.session['payment_sum']
        request.session.pop('promo_code', None)
    return redirect('user_make_booking_step_one')

def edit_user_info(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_info')
    else:
        form = UserForm(instance=user)
    return render(request, 'carsharing/user/edit_user_info.html', {'form': form, 'user': user})
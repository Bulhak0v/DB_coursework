from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm, CarForm, BookingForm, UserRegistrationForm, UserLoginForm, BookingStepOneForm, \
    BookingStepTwoForm, BookingStepThreeForm, ClientScoreForm, BranchForm
from .models import User, Car, Booking, Branch, Additional_Services, Booking_Services, Rental_Agreement, Promo_Code, \
    Insurance, ClientScore
from django.db.models import Sum, Count, Q
from django.http import HttpResponseForbidden
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

    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(driver_license__icontains=search_query)
        )

    sort_by = request.GET.get('sort', 'user_id')
    order = request.GET.get('order', 'asc')
    allowed_fields = ['user_id', 'first_name', 'last_name', 'email', 'phone_number', 'driver_license']

    if sort_by in allowed_fields:
        if order == 'desc':
            sort_by = f'-{sort_by}'
        users = users.order_by(sort_by)

    context = {
        'users': users,
        'search_query': search_query,
        'sort_by': sort_by.lstrip('-'),
        'order': order
    }

    return render(request, 'carsharing/admin/user_list.html', context)


def car_list(request):
    cars = Car.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        cars = cars.filter(
            Q(brand__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(license_plate__icontains=search_query)
        )

    sort_by = request.GET.get('sort', 'car_id')
    order = request.GET.get('order', 'asc')
    allowed_fields = [
        'car_id', 'car_type', 'brand', 'model',
        'license_plate', 'release_year', 'price_per_day'
    ]

    if sort_by in allowed_fields:
        if order == 'desc':
            sort_by = f'-{sort_by}'
        cars = cars.order_by(sort_by)

    car_type = request.GET.get('car_type')
    if car_type:
        cars = cars.filter(car_type=car_type)

    branch = request.GET.get('branch')
    if branch:
        cars = cars.filter(branch_id=branch)

    context = {
        'cars': cars,
        'car_types': Car.objects.values_list('car_type', flat=True).distinct(),
        'branches': Branch.objects.order_by('city', 'street'),
        'search_query': search_query,
        'selected_car_type': car_type,
        'selected_branch': branch,
        'sort_by': sort_by.lstrip('-'),
        'order': order
    }

    return render(request, 'carsharing/admin/car_list.html', context)


def booking_list(request):
    bookings = Booking.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        bookings = bookings.filter(
            Q(client__first_name__icontains=search_query) |
            Q(client__last_name__icontains=search_query) |
            Q(car__brand__icontains=search_query) |
            Q(car__model__icontains=search_query) |
            Q(booking_id__icontains=search_query) |
            Q(client__first_name__icontains=search_query.split()[0],
              client__last_name__icontains=' '.join(search_query.split()[1:])) |
            Q(car__brand__icontains=search_query.split()[0], car__model__icontains=' '.join(search_query.split()[1:]))
        )

    pickup_location_filter = request.GET.get('pickup_location', '')
    if pickup_location_filter:
        bookings = bookings.filter(pickup_location=pickup_location_filter)

    return_location_filter = request.GET.get('return_location', '')
    if return_location_filter:
        bookings = bookings.filter(return_location=return_location_filter)

    sort_by = request.GET.get('sort', 'booking_id')
    order = request.GET.get('order', 'asc')
    allowed_fields = [
        'booking_id', 'client__first_name', 'client__last_name', 'car__brand',
        'car__model', 'start_date', 'end_date', 'total_price', 'status', 'pickup_location', 'return_location'
    ]

    if sort_by in allowed_fields:
        if order == 'desc':
            sort_by = f'-{sort_by}'
        bookings = bookings.order_by(sort_by)

    branches = {branch.branch_id: branch for branch in Branch.objects.all()}

    for booking in bookings:
        booking.pickup_location = branches.get(booking.pickup_location)
        booking.return_location = branches.get(booking.return_location)

    branches_list = Branch.objects.all()

    context = {
        'bookings': bookings,
        'search_query': search_query,
        'pickup_location_filter': pickup_location_filter,
        'return_location_filter': return_location_filter,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
        'branches': branches_list,
    }

    return render(request, 'carsharing/admin/booking_list.html', context)


def branches_list(request):
    search_query = request.GET.get('search', '')
    filter_city = request.GET.get('filter_city', '')
    sort_by = request.GET.get('sort', 'branch_id')
    order = request.GET.get('order', 'asc')

    branches = Branch.objects.all()

    if search_query:
        branches = branches.filter(
            Q(city__icontains=search_query) |
            Q(street__icontains=search_query) |
            Q(building__icontains=search_query) |
            Q(zip_code__icontains=search_query)
        )

    if filter_city:
        branches = branches.filter(city=filter_city)

    allowed_fields = ['branch_id', 'city', 'street', 'building', 'zip_code']
    if sort_by in allowed_fields:
        if order == 'desc':
            sort_by = f'-{sort_by}'
        branches = branches.order_by(sort_by)

    cities = Branch.objects.values_list('city', flat=True).distinct()

    return render(request, 'carsharing/admin/branches_list.html', {
        'branches': branches,
        'search_query': search_query,
        'filter_city': filter_city,
        'cities': cities,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
    })


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
            if not form.cleaned_data.get('branch'):
                form.add_error('branch', 'Необхідно обрати філію')
            else:
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


def add_branch(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('branches_list')
    else:
        form = BranchForm()

    return render(request, 'carsharing/admin/add_branch.html', {'form': form})


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


def edit_branch(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            return redirect('branches_list')
    else:
        form = BranchForm(instance=branch)

    return render(request, 'carsharing/admin/edit_branch.html', {'form': form, 'branch': branch})


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


def delete_branch(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == "POST":
        branch.delete()
        return redirect('branches_list')
    return render(request, 'carsharing/admin/confirm_delete.html', {'object': branch})


def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.status == 'cancelled':
        return redirect('user_info')
    if booking.status == 'completed':
        return redirect('user_info')

    if request.method == "POST":
        booking.status = 'Cancelled'
        booking.save()
        return redirect('user_info')
    return render(request, 'carsharing/user/confirm_cancel.html', {'object': booking})


def complete_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.status == 'completed':
        return redirect('user_info')
    if booking.status == 'cancelled':
        return redirect('user_info')

    if request.method == "POST":
        booking.status = 'Completed'
        booking.save()
        return redirect('user_info')
    return render(request, 'carsharing/user/confirm_complete.html', {'object': booking})


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


def get_services_statistics():
    total_services_count = Booking_Services.objects.aggregate(total_services=Sum('services_number'))[
                               'total_services'] or 0

    services_statistics = Booking_Services.objects.values('service__name').annotate(
        total_count=Sum('services_number')
    ).order_by('service__name')

    return total_services_count, services_statistics


def additional_services_statistics(request):
    total_services_count, services_statistics = get_services_statistics()
    return render(request, 'carsharing/admin/additional_services_statistics.html', {
        'total_services_count': total_services_count,
        'services_statistics': services_statistics
    })


def insurance_usage_ratio(request):
    total_rentals = Rental_Agreement.objects.count()
    rentals_with_insurance = Rental_Agreement.objects.filter(insurance__isnull=False).count()
    usage_ratio = (rentals_with_insurance / total_rentals) if total_rentals > 0 else 0

    return render(request, 'carsharing/admin/insurance_usage_ratio.html', {
        'total_rentals': total_rentals,
        'rentals_with_insurance': rentals_with_insurance,
        'usage_ratio': usage_ratio
    })


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
    rental_agreements = Rental_Agreement.objects.filter(booking__client=user)
    return render(
        request,
        'carsharing/user/user_account_info.html',
        {'user': user, 'rental_agreements': rental_agreements}
    )


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

    agreement_number = request.session.get('agreement_number')
    if not agreement_number:
        agreement_number = generate_agreement_number()
        request.session['agreement_number'] = agreement_number

    insurances = Insurance.objects.all()
    selected_insurance_id = request.session.get('selected_insurance_id')
    selected_insurance = None
    insurance_value = 0

    if selected_insurance_id:
        selected_insurance = Insurance.objects.filter(insurance_id=selected_insurance_id).first()
        if selected_insurance:
            insurance_value = float(selected_insurance.insurance_value)

    base_payment_sum = float(booking.total_price) + insurance_value

    promo_code = None
    discount = 0
    applied_promo_code_id = request.session.get('promo_code')

    if applied_promo_code_id:
        promo_code = Promo_Code.objects.filter(promo_code_id=applied_promo_code_id).first()
        if promo_code:
            discount = promo_code.discount

    payment_sum = base_payment_sum * (100 - discount) / 100

    if request.method == 'POST':
        if 'remove_promo_code' in request.POST:
            request.session.pop('promo_code', None)
            payment_sum = base_payment_sum
            request.session['payment_sum'] = payment_sum
            return redirect('user_booking_step_four', booking_id=booking_id)

        if 'apply_promo_code' in request.POST:
            entered_code = request.POST.get('promo_code', '').strip()
            promo_code = Promo_Code.objects.filter(
                code=entered_code, end_date__gte=now().date()
            ).first()
            if promo_code:
                discount = promo_code.discount
                payment_sum = base_payment_sum * (100 - discount) / 100
                request.session['promo_code'] = promo_code.promo_code_id
            else:
                return render(
                    request,
                    'carsharing/user/rental_agreement.html',
                    {
                        'error_message': 'Введено недійсний промокод.',
                        'agreement_number': agreement_number,
                        'signature_date': now(),
                        'payment_sum': payment_sum,
                        'booking': booking,
                        'promo_code': None,
                        'discount': 0,
                        'insurances': insurances,
                        'selected_insurance': selected_insurance,
                    }
                )

        if 'select_insurance' in request.POST:
            selected_insurance_id = request.POST.get('insurance_id')
            if selected_insurance_id:
                request.session['selected_insurance_id'] = selected_insurance_id
                selected_insurance = Insurance.objects.filter(insurance_id=selected_insurance_id).first()
                insurance_value = float(selected_insurance.insurance_value) if selected_insurance else 0
                base_payment_sum = float(booking.total_price) + insurance_value
                payment_sum = base_payment_sum * (100 - discount) / 100

    request.session['payment_sum'] = payment_sum

    context = {
        'agreement_number': agreement_number,
        'signature_date': now(),
        'payment_sum': payment_sum,
        'booking': booking,
        'promo_code': promo_code,
        'discount': discount,
        'insurances': insurances,
        'selected_insurance': selected_insurance,
    }
    return render(request, 'carsharing/user/rental_agreement.html', context)


def confirm_rental_agreement(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    agreement_number = request.session.get('agreement_number')
    payment_sum = request.session.get('payment_sum')
    promo_code_id = request.session.get('promo_code')
    promo_code = Promo_Code.objects.filter(promo_code_id=promo_code_id).first()
    selected_insurance_id = request.session.get('selected_insurance_id')
    selected_insurance = Insurance.objects.filter(insurance_id=selected_insurance_id).first()

    rental_agreement = Rental_Agreement.objects.create(
        agreement_number=agreement_number,
        signature_date=now(),
        payment_sum=payment_sum,
        booking=booking,
        promo_code=promo_code,
        insurance=selected_insurance,
    )

    request.session.pop('agreement_number', None)
    request.session.pop('payment_sum', None)
    request.session.pop('selected_insurance_id', None)
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


def rental_agreement_info(request, pk):
    agreement = get_object_or_404(Rental_Agreement, pk=pk)
    booking = agreement.booking
    booking_services = Booking_Services.objects.filter(booking=booking).select_related('service')
    insurance = agreement.insurance
    client_score = ClientScore.objects.filter(rental_agreement_id=agreement.rental_agreement_id).select_related(
        'rental_agreement_id')
    context = {
        'agreement': agreement,
        'booking': booking,
        'booking_services': booking_services,
        'insurance': insurance,
        'client_score': client_score
    }
    return render(request, 'carsharing/user/rental_agreement_info.html', context)


def rate_booking(request, pk):
    agreement = get_object_or_404(Rental_Agreement, pk=pk)

    if agreement.booking.status != 'completed':
        return HttpResponseForbidden("Rating is only allowed for completed bookings.")
    if ClientScore.objects.filter(rental_agreement=agreement).exists():
        return HttpResponseForbidden("You have already rated this booking.")

    if request.method == 'POST':
        form = ClientScoreForm(request.POST)
        if form.is_valid():
            ClientScore.objects.create(
                score=form.cleaned_data['score'],
                comment=form.cleaned_data['comment'],
                score_date=now().date(),
                rental_agreement=agreement
            )
            return redirect('rental_agreement_info', pk=pk)
    else:
        form = ClientScoreForm()

    return render(request, 'carsharing/user/rate_booking.html', {
        'form': form,
        'agreement': agreement
    })


def additional_services_list(request):
    services = Additional_Services.objects.all()
    search_query = request.GET.get('search', '')
    if search_query:
        services = services.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    sort_by = request.GET.get('sort', 'name')
    order = request.GET.get('order', 'asc')
    allowed_fields = [
        'service_id', 'name', 'description', 'price', 'service_status'
    ]

    if sort_by in allowed_fields:
        if order == 'desc':
            sort_by = f'-{sort_by}'
        services = services.order_by(sort_by)

    service_status = request.GET.get('service_status')
    if service_status:
        services = services.filter(service_status=service_status)

    context = {
        'services': services,
        'search_query': search_query,
        'sort_by': sort_by.lstrip('-'),
        'order': order,
        'service_status': service_status
    }

    return render(request, 'carsharing/admin/additional_services_list.html', context)


def additional_service_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        service_status = request.POST.get('service_status') == 'on'

        Additional_Services.objects.create(
            name=name, description=description, price=price, service_status=service_status
        )
        return redirect('additional_services')

    return render(request, 'carsharing/admin/additional_service_form.html', {'action': 'Add'})


def additional_service_edit(request, service_id):
    service = get_object_or_404(Additional_Services, service_id=service_id)

    if request.method == 'POST':
        service.name = request.POST.get('name')
        service.description = request.POST.get('description')
        service.price = request.POST.get('price')
        service.service_status = request.POST.get('service_status') == 'on'
        service.save()

        return redirect('additional_services')

    return render(request, 'carsharing/admin/additional_service_form.html', {
        'service': service,
        'action': 'Edit'
    })


def additional_service_delete(request, service_id):
    service = get_object_or_404(Additional_Services, service_id=service_id)
    if request.method == "POST":
        service.delete()
        return redirect('additional_services')
    return render(request, 'carsharing/admin/confirm_delete.html', {'object': service})

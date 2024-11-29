from django import forms
from .models import User, Car, Booking, Branch, Additional_Services


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'phone_number', 'driver_license']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        phone_number = cleaned_data.get('phone_number')
        driver_license = cleaned_data.get('driver_license')

        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            self.add_error('email', 'A user with this email already exists.')

        if User.objects.filter(phone_number=phone_number).exclude(pk=self.instance.pk).exists():
            self.add_error('phone_number', 'A user with this phone number already exists.')

        if User.objects.filter(driver_license=driver_license).exclude(pk=self.instance.pk).exists():
            self.add_error('driver_license', 'A user with this driver license already exists.')

        return cleaned_data


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['car_type', 'brand', 'model', 'license_plate', 'release_year', 'price_per_day', 'car_status']

    def clean(self):
        cleaned_data = super().clean()
        license_plate = cleaned_data.get('license_plate')

        if Car.objects.filter(license_plate=license_plate).exclude(pk=self.instance.pk).exists():
            self.add_error('license_plate', 'A car with this license plate already exists.')

        return cleaned_data


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['client', 'car', 'start_date', 'end_date', 'total_price', 'status']

    def clean(self):
        cleaned_data = super().clean()
        car = cleaned_data.get('car')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if car and start_date and end_date:
            overlapping_bookings = Booking.objects.filter(
                car=car,
                end_date__gte=start_date,
                start_date__lte=end_date
            ).exclude(pk=self.instance.pk)
            if overlapping_bookings.exists():
                raise forms.ValidationError(
                    "This car is already booked for the selected dates."
                )
        return cleaned_data


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'phone_number', 'driver_license']

    password = forms.CharField(widget=forms.PasswordInput)


class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        try:
            user = User.objects.get(email=email)
            if user.password != password:
                raise forms.ValidationError("Incorrect password")
        except User.DoesNotExist:
            raise forms.ValidationError("There is no user with this email")

        return cleaned_data


class BookingStepOneForm(forms.ModelForm):
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    pickup_branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Pickup Location",
        widget=forms.Select
    )
    return_branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Return Location",
        widget=forms.Select
    )
    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'pickup_branch', 'return_branch']

class BookingStepTwoForm(forms.Form):
    car = forms.ModelChoiceField(
        queryset=Car.objects.none(),
        label="Car",
        widget=forms.Select
    )

    class Meta:
        model = Booking
        fields = ['car']

class BookingStepThreeForm(forms.Form):
    services = forms.ModelMultipleChoiceField(
        queryset=Additional_Services.objects.filter(service_status=True),
        widget=forms.CheckboxSelectMultiple,
        label="Additional Services",
        required=False
    )
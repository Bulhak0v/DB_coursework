from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    driver_license = models.CharField(max_length=9)
    is_superuser = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'user'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Branch(models.Model):
    branch_id = models.AutoField(primary_key=True)
    city = models.CharField(max_length=25)
    street = models.CharField(max_length=50)
    building = models.CharField(max_length=5)
    zip_code = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'branch'

    def __str__(self):
        return f"Branch {self.branch_id} in {self.city} {self.street} {self.building} {self.zip_code}"


class Car(models.Model):
    car_id = models.AutoField(primary_key=True)
    branch = models.ForeignKey(Branch, related_name='cars', on_delete=models.CASCADE)
    car_type = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=30)
    license_plate = models.CharField(max_length=15)
    release_year = models.IntegerField()
    price_per_day = models.IntegerField()
    car_status = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'car'

    def __str__(self):
        return f"{self.brand} {self.model} ({self.car_type})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('reserved', 'Reserved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    booking_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(User, related_name='booking', on_delete=models.CASCADE)
    car = models.ForeignKey(Car, related_name='booking', on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='reserved')
    pickup_location = models.IntegerField()
    return_location = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'booking'

    def __str__(self):
        return f"Booking {self.booking_id} for {self.client} with {self.car} from {self.start_date} to {self.end_date}"


class Additional_Services(models.Model):
    service_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    service_status = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'additional_services'

    def __str__(self):
        return self.name


class Booking_Services(models.Model):
    booking = models.ForeignKey(Booking, related_name='booking_services', on_delete=models.CASCADE)
    service = models.ForeignKey(Additional_Services, related_name='booking_services', on_delete=models.CASCADE)
    services_number = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'booking_services'

    def __str__(self):
        return f"Booking {self.booking.booking_id} - Service {self.service.name}"


class Promo_Code(models.Model):
    promo_code_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True)
    discount = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    end_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'promo_code'

    def __str__(self):
        return f"Promo Code {self.code} - {self.discount}% valid till {self.end_date}"


class Insurance(models.Model):
    insurance_id = models.AutoField(primary_key=True)
    insurance_type = models.CharField(max_length=100, verbose_name="Insurance Type")
    insurance_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Insurance Value")
    insurance_details = models.TextField(blank=True, null=True, verbose_name="Insurance Details")

    class Meta:
        managed = False
        db_table = 'insurance'

    def __str__(self):
        return f"{self.insurance_type} (${self.insurance_value})"


class Rental_Agreement(models.Model):
    rental_agreement_id = models.AutoField(primary_key=True)
    agreement_number = models.CharField(max_length=10, unique=True)
    signature_date = models.DateTimeField(auto_now_add=True)
    payment_sum = models.DecimalField(max_digits=10, decimal_places=2)
    booking = models.OneToOneField('Booking', on_delete=models.CASCADE)
    insurance = models.ForeignKey('Insurance', on_delete=models.SET_NULL, null=True, blank=True)
    promo_code = models.ForeignKey('Promo_Code', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='rental_agreements')

    class Meta:
        managed = False
        db_table = 'rental_agreement'

    def __str__(self):
        return f"Rental Agreement {self.agreement_number} for Booking {self.booking.id}"


class ClientScore(models.Model):
    client_score_id = models.AutoField(primary_key=True)
    score = models.PositiveSmallIntegerField(
        verbose_name="Score",
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Score between 1 and 5"
    )
    comment = models.TextField(blank=True, null=True, verbose_name="Comment")
    score_date = models.DateField(verbose_name="Score Date")
    rental_agreement = models.OneToOneField(
        Rental_Agreement,
        on_delete=models.CASCADE,
        verbose_name="Rental Agreement",
        unique=True
    )

    class Meta:
        managed = False
        db_table = 'client_score'

    def __str__(self):
        return f"Score {self.score} for Agreement {self.rental_agreement}"

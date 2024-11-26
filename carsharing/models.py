from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    driver_license = models.CharField(max_length=9)

    class Meta:
        managed = False
        db_table = 'user'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Car(models.Model):
    car_id = models.AutoField(primary_key=True)
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

    class Meta:
        managed = False
        db_table = 'booking'

    def __str__(self):
        return f"Booking {self.booking_id} for {self.client} with {self.car} from {self.start_date} to {self.end_date}"


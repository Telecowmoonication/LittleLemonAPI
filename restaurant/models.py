from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# For logging staff hours
class Logger(models.Model):
    LOG_TYPE_CHOICES = [
        ('IN', 'Login'),
        ('OUT', 'Logout'),
    ]
    
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    log_type = models.CharField(max_length=3, choices=LOG_TYPE_CHOICES, default='IN')
    time_log = models.TimeField(help_text="Enter the exact time! (Ex. 15:26)")
    
    def __str__(self)-> str:
        return f'{self.first_name} {self.last_name} - {self.log_type} at {self.time_log}'
    

# For user comments/reviews
class UserComments(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    comment = models.CharField(max_length=1000)
    

class Category(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255, unique=True, db_index=True)
    
    def __str__(self)-> str:
        return self.title


class MenuItem(models.Model):
    title = models.CharField(max_length=255, unique=True, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True, default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    inventory = models.IntegerField(default=0)
    
    def __str__(self)-> str:
        return self.title


# For booking a reservation
class Booking(models.Model):
    name = models.CharField(max_length=255, help_text="Enter First and Last name please.")
    no_of_guests = models.IntegerField(default=1)
    booking_date = models.DateTimeField()
    
    def __str__(self)-> str:
        return f'Reservation by {self.name} for {self.no_of_guests}'
    

# For each user's cart
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField(default=1)
    
    # These @properties behave like fields when you access them, but they're not actual database fields, and their values are calculated on-demand.
    @property
    def unit_price(self):
        return self.menuitem.price
    
    @property
    def price(self):
        return self.unit_price * self.quantity
    
    class Meta:
        unique_together = ['menuitem', 'user']
        
    def __str__(self)-> str:
        return f'Cart of {self.user.username}'
    

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True)
    status = models.BooleanField(db_index=True, default=False)
    ready_for_delivery = models.BooleanField(db_index=True, default=False)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    time = models.DateField(db_index=True)
    
    def __str__(self)-> str:
        delivery_crew_username = self.delivery_crew.username if self.delivery_crew else "Not assigned"
        status_str = "Delivered" if self.status else "Out for Delivery"
        return f'Order {self.id} by {self.user.username} - Delivery Crew: {delivery_crew_username} (Status: {status_str})'
    
    # For deleting items from the cart once the order is placed.
    def delete(self, *args, **kwargs):
        self.orderitem_set.all().delete()
        super().delete(*args, **kwargs)
        
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    
    class Meta:
        unique_together = ['order', 'menuitem']
    
    def __str__(self)-> str:
        return f'{self.order.id} - {self.menuitem.title} (x{self.quantity})'
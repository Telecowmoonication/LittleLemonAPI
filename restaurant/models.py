from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from decimal import Decimal, ROUND_HALF_UP

# Create your models here.

# Table for employee hours and logs
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
    

# Table for user comments/reviews
class UserComments(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    comment = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self)-> str:
        return f'{self.first_name} {self.last_name}: {self.comment}'
    

# Table for the categories of menu items
class Category(models.Model):
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    title = models.CharField(max_length=255, unique=True, db_index=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs)
    
    def __str__(self)-> str:
        return self.title


# Table for menu items
class MenuItem(models.Model):
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    title = models.CharField(max_length=255, unique=True, db_index=True)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True, default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    inventory = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(MenuItem, self).save(*args, **kwargs)
    
    def __str__(self)-> str:
        return self.title
    

# Table for each user's cart
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField(default=1)
    
    # These @properties behave like fields when you access them, but they're not actual database fields, and their values are calculated on-demand.
    @property
    def unit_price(self):
        return self.menuitem.unit_price
    
    @property
    def price(self):
        return self.unit_price * self.quantity
    
    class Meta:
        unique_together = ['menuitem', 'user']
        
    def __str__(self)-> str:
        return f'Cart of {self.user.username}'
    

# Table for all orders
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True)
    order_status = models.BooleanField(db_index=True, default=False)
    ready_for_delivery = models.BooleanField(db_index=True, default=False)
    time = models.DateField(db_index=True)
    
    def __str__(self)-> str:
        delivery_crew_username = self.delivery_crew.username if self.delivery_crew else "Not assigned"
        status_str = "Delivered" if self.order_status else "Out for Delivery"
        return f'Order {self.id} by {self.user.username} - Delivery Crew: {delivery_crew_username} (Status: {status_str})'
    
    @property
    def subtotal(self):
        subtotal = sum(item.price for item in self.orderitem_set.all())
        return subtotal.quantize(Decimal(1.1), rounding=ROUND_HALF_UP)
    
    @property
    def price_after_tax(self):
        price_after_tax = self.subtotal * Decimal(1.1)
        return price_after_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # For deleting items from the cart once the order is placed.
    def delete(self, *args, **kwargs):
        self.orderitem_set.all().delete()
        super().delete(*args, **kwargs)
        

# Table for order details    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
        
    class Meta:
        unique_together = ['order', 'menuitem']
    
    def __str__(self)-> str:
        return f'{self.order.id} - {self.menuitem.title} (x{self.quantity})'
    
    @property
    def unit_price(self):
        return self.menuitem.unit_price
    
    @property
    def price(self):
        price = self.unit_price * self.quantity
        return price.quantize(Decimal(1.1), rounding=ROUND_HALF_UP)

# Table for reservations booked
class Booking(models.Model):
    STATUS_CHOICES = [
        ('current', 'Current'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ]
    name = models.CharField(max_length=255, help_text="Enter First and Last name please.")
    no_of_guests = models.IntegerField(default=1)
    booking_date = models.DateTimeField()
    reservation_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='current')
    
    def __str__(self)-> str:
        return f'Reservation by {self.name} for {self.no_of_guests}'
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.validators import UniqueValidator
from rest_framework.reverse import reverse
from .models import Logger, UserComments, Category, MenuItem, Booking, Cart, Order, OrderItem
from decimal import Decimal, ROUND_HALF_UP
from datetime import time
import re
import bleach
import datetime

# Serializes User model for use with API, links to user instance
class UserSerializer(serializers.HyperlinkedModelSerializer):
    user_details_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['url', 'user_details_url', 'username', 'email', 'first_name', 'last_name', 'groups']
        read_only_fields = ['username']
        
    def get_user_details_url(self, obj):
        request = self.context.get('request')
        return reverse('user_api_view', args=[obj.username], request=request)


# Serializes and validates the user registration information
class UserRegSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']
        
    def validate_pass(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields did not match."})
        return attrs
    
    def validate_username(self, value):
        if len(value) < 3 or len(value) > 150:
            raise serializers.ValidationError("Username must be betweeb 3 and 150 characters long.")
        return bleach.clean(value, tags=[], strip=True)
    
    def validate_email(self, value):
        if not serializers.EmailField().run_validation(value):
            raise serializers.ValidationError("Invalid email format.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create(
            username = validated_data['username'],
            email = validated_data['email'],
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


# Serializes and validates employee hours worked, links to log details
class LoggerSerializer(serializers.HyperlinkedModelSerializer):
    log_details_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Logger
        fields = ['url', 'log_details_url', 'id', 'first_name', 'last_name', 'log_type', 'time_log']
        read_only_fields = ['id']
        
    def get_log_details_url(self, obj):
        request = self.context.get('request')
        return reverse('log_details_api_view', args=[obj.user.id], request=request)
        
    def validate_first_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("First name should contain only letters.")
        return value
    
    def validate_last_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Last name should contain only letters.")
        return value
        
    def validate_time_log(self, value):
        # Defining allowed time range (7AM to 12AM)
        start_time = time(7, 0) # 7AM
        end_time = time(0, 0) # 12AM (Midnight)
        
        if not (start_time <= value <= time(23, 59) or value == end_time):
            raise serializers.ValidationError("Log time must be between 7AM and 12AM.")
        return value
    
    def validate_log(self, data):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        log_type = data.get('log_type')
        
        # Check if user logged out before trying to login again
        incomplete_log = Logger.objects.filter(
            first_name = first_name,
            last_name = last_name,
            log_type = 'IN'
        ).exclude(log_type='OUT').exists()
        
        if log_type == 'IN' and incomplete_log:
            raise serializers.ValidationError("Cannot log in again without logging out first.")
        return data


# Serializes and validates user comments
class UserCommentsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = UserComments
        fields = ['id', 'first_name', 'last_name', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']
        
    def validate_first_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("First name should contain only letters.")
        return value
    
    def validate_last_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Last name should contain only letters.")
        return value
    
    def validate_comment(self, value):
        if len(value) > 1000:
            raise serializers.ValidationError("Comment cannot be more than 1000 characters.")
        return bleach.clean(value, tags=[], strip=True)


# Serializes and validates categories, links to category details
class CategorySerializer(serializers.HyperlinkedModelSerializer):
    category_details_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['url', 'category_details_url', 'id', 'slug', 'title']
        read_only_fields = ['id']
        extra_kwargs = {
            'slug': {
                'validators': [
                    UniqueValidator(queryset=Category.objects.all())
                ]
            },
            'title': {
                'validators': [
                    UniqueValidator(queryset=Category.objects.all())
                ]
            }
        }
        
    def get_category_details_url(self, obj):
        request = self.context.get('request')
        return reverse('category_details_api_view', args=[obj.slug], request=request)
    
    # Ensuring slug only has lowercase letters, numbers, and hyphens. Cannot be blank or only hyphens
    def validate_slug(self, value):
        if not re.match(r'^[a-z0-9-]+$', value):
            raise serializers.ValidationError("Slug can only contain lowercase letters, numbers, and hyphens.")
        if value.strip('-') == '':
            raise serializers.ValidationError("Slug cannot be blank or only hyphens.")
        return value
    
    # Generates slug from title if not provided upon creation
    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)
    
    # Generates slug from title if not provided upon update
    def update(self, instance, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().update(instance, validated_data)
    
    # Sanatizes title and makes sure it is at least 3 characters long
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return bleach.clean(value, tags=[], strip=True)
    

# Serializes and validates menu items, links to menu item details
class MenuItemSerializer(serializers.HyperlinkedModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True, allow_null=True)
    stock = serializers.IntegerField(source='inventory')
    price_after_tax = serializers.SerializerMethodField(method_name='calculate_tax')
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    featured = serializers.BooleanField(required=False)
    menuitem_details_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['url', 'menuitem_details_url', 'id', 'slug', 'title', 'unit_price', 'price_after_tax', 'category', 'featured', 'stock']
        read_only_fields = ['id']
        extra_kwargs = {
            'unit_price': {'min_value': Decimal('0.01'), 'error_messages': {'min_value': 'Price must be greater than zero.'}},
            'stock': {'min_value': 0, 'error_messages': {'min_value': 'Stock must be greater than zero.'}},
            'slug' : {
                'validators': [
                    UniqueValidator(queryset=MenuItem.objects.all())
                ]
            },
            'title': {
                'validators': [
                    UniqueValidator(queryset=MenuItem.objects.all())
                ]
            }
        }
        
    def get_menuitem_details_url(self, obj):
        request = self.context.get('request')
        return reverse('menu_item_api_view', args=[obj.slug], request=request)
    
    # Ensuring slug only has lowercase letters, numbers, and hyphens. Cannot be blank or only hyphens
    def validate_slug(self, value):
        if not re.match(r'^[a-z0-9-]+$', value):
            raise serializers.ValidationError("Slug can only contain lowercase letters, numbers, and hyphens.")
        if value.strip('-') == '':
            raise serializers.ValidationError("Slug cannot be blank or only hyphens.")
        return value
    
    # Generates slug from title if not provided upon creation
    def create(self, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)
    
    # Generates slug from title if not provided upon update
    def update(self, instance, validated_data):
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().update(instance, validated_data)
    
    # Sanatizes title and makes sure it is at least 3 characters long
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return bleach.clean(value, tags=[], strip=True)
    
    # Calculates price after tax
    def calculate_tax(self, menuitem):
        return menuitem.unit_price * Decimal(1.1)
    

# Serializes and validates carts, links to menu item details
class CartSerializer(serializers.HyperlinkedModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username') # Gets username from User model
    menuitem_title = serializers.CharField(write_only=True) # Allows for the input of a menuitem by a user
    unit_price = serializers.ReadOnlyField() # Shows but does not allow editing/input
    price = serializers.ReadOnlyField() # Shows but does not allow editing/input
    subtotal = serializers.SerializerMethodField() # Shows but does not allow editing/input
    price_after_tax = serializers.SerializerMethodField() # Shows but does not allow editing/input
    menuitem_details_url = serializers.SerializerMethodField() # For hyperlink
    
    class Meta:
        model = Cart
        fields = ['url', 'menuitem_details_url', 'id', 'user_username', 'menuitem_title', 'quantity', 'unit_price', 'price', 'subtotal', 'price_after_tax']
        read_only_fields = ['id', 'user_username', 'unit_price', 'price', 'subtotal', 'price_after_tax']
        extra_kwargs = {
            'quantity': {'min_value': 1, 'error_messages': {'min_value': 'Quantity must be greater than zero.'}},
        }
        
    # For hyperlink
    def get_menuitem_details_url(self, obj):
        request = self.context.get('request')
        return reverse('menu_item_api_view', args=[obj.menuitem.slug], request=request)
    
    # Calculates subtotal    
    def get_subtotal(self, obj):
        user = self.context['request'].user
        user_cart_items = Cart.objects.filter(user=user)
        subtotal = sum(item.price for item in user_cart_items)
        return Decimal(subtotal)
    
    # Calculates price after tax
    def get_price_after_tax(self, obj):
        subtotal = self.get_subtotal(obj)
        price_after_tax = subtotal * Decimal(1.1)
        return price_after_tax
        
    # Checks if the user has the menuitem in their cart already or not
    def create(self, validated_data):
        user = self.context['request'].user
        title = validated_data.pop('menuitem_title')
        
        # Ensures the item added is actually on the menu
        try:
            menuitem = MenuItem.objects.get(title=title)
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError({'menuitem_title': 'MenuItem with this title does not exist. Please check spelling and letter-case.'})
        
        # If item not in cart, the entry is created
        cart_item, created = Cart.objects.get_or_create(
            user = user,
            menuitem = menuitem,
            defaults = {
                'quantity': validated_data.get('quantity', 1),
            }
        )
        
        # If item in cart the quantity is increased instead of a new entry being created
        if not created:
            cart_item.quantity += validated_data.get('quantity', 1)
            cart_item.save()
        
        return cart_item
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Ensure 'menuitem_title' is shown to the client in output as it is a write_only field
        representation['menuitem_title'] = instance.menuitem.title
        # Format unit_price, the price of the menuitem, and show in output
        representation['unit_price'] = "{:.2f}".format(instance.menuitem.unit_price)
        # Format price, total for the menuitems in the cart (unit_price * quantity), and show in output
        representation['price'] = "{:.2f}".format(instance.price)
        # Format subtotal and show in output 
        representation['subtotal'] = "{:.2f}".format(self.get_subtotal(instance))
        # Format price after tax for menu items in cart (subtotal * Decimal(1.1)), and show in output
        representation['price_after_tax'] = "{:.2f}".format(self.get_price_after_tax(instance))
        # Show category in output
        representation['category'] = instance.menuitem.category.title
        
        return representation
    

# Used to represent the details of a single order item
# Serializes and validates order item, links to menu item details
class OrderItemSerializer(serializers.HyperlinkedModelSerializer):
    menuitem_title = serializers.ReadOnlyField(source='menuitem.title')
    price = serializers.SerializerMethodField()
    menuitem_details_url = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['url', 'menuitem_details_url', 'id', 'order', 'menuitem', 'menuitem_title', 'quantity', 'price']
        read_only_fields = ['id', 'order', 'menuitem_title', 'price']
        extra_kwargs = {
            'quantity': {'min_value': 1, 'error_messages': {'min_value': 'Quantity must be at least 1.'}},
        }
    
    def get_menuitem_details_url(self, obj):
        request = self.context.get('request')
        return reverse('menu_item_api_view', args=[obj.menuitem.slug], request=request)
    
    
    def get_price(self, order_item: OrderItem):
        price = order_item.quantity * order_item.menuitem.unit_price
        return price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    

# Used to represent the entire order, which may include a list of OrderItem instances
# Serializes and validates orders, links to order details
class OrderSerializer(serializers.HyperlinkedModelSerializer):
    # For each Order instance being serialized, the serializer should include a list of all related OrderItem instances serialized by OrderItemSerializer
    # orderitem_set refers to a reverse relation from a foreign key
    # Used to include all related 'OrderItem' instances within the serialization of an 'Order'
    order_items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    user_username = serializers.ReadOnlyField(source='user.username')
    delivery_crew_username = serializers.CharField(write_only=True, required=False)
    subtotal = serializers.SerializerMethodField()
    price_after_tax = serializers.SerializerMethodField()
    order_details_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['url', 'order_details_url', 'id', 'user', 'user_username', 'delivery_crew', 'delivery_crew_username', 'order_status', 'ready_for_delivery', 'time', 'order_items', 'subtotal', 'price_after_tax']
        read_only_fields = ['id', 'user', 'user_username', 'subtotal', 'price_after_tax' 'order_items']
        extra_kwargs = {
            'time': {'error_messages': {'required': 'Please provide the time of the order.'}},
        }
    
    def get_order_details_url(self, obj):
        request = self.context.get('request')
        return reverse('order_details_api_view', args=[obj.id], request=request)
    
    def get_subtotal(self, order: Order):
        subtotal = sum(Decimal(item.quantity) * Decimal(item.menuitem.unit_price) for item in order.orderitem_set.all())
        return subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def get_price_after_tax(self, order: Order):
        subtotal = self.get_subtotal(order)
        price_after_tax = subtotal * Decimal(1.1)
        return price_after_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['subtotal'] = "{:.2f}".format(self.get_subtotal(instance))
        representation['price_after_tax'] = "{:.2f}".format(self.get_price_after_tax(instance))
        
        return representation
    
    # Ensure user exists and is a Delivery crew member
    def validate_delivery_crew_username(self, value):
        try:
            user = User.objects.get(username=value)
            if not user.groups.filter(name='Delivery crew').exists():
                raise serializers.ValidationError("User is not a Delivery crew member.")
            return
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
    # Ensure total is greater than $0.00
    def validate_total(self, value):
        if value <= Decimal('0.01'):
            raise serializers.ValidationError("Total cannot be less than $0.01.")
        return value
    
    # Ensure order is placed for today
    def validate_time(self, value):
        if value > datetime.date.today():
            raise serializers.ValidationError("Order date cannot be in the future.")
        return value
    
    # Handles creation of order and setting of delivery_crew if delivery_crew_username provided
    def create(self, validated_data):
        delivery_crew_username = validated_data.pop('delivery_crew_username', None)
        if delivery_crew_username:
            validated_data['delivery_crew'] = User.objects.get(username=delivery_crew_username)
        return super().create(validated_data)
    
    # Handles update of order and updating of delivery_crew if delivery_crew_username provided
    def update(self, instance, validated_data):
        delivery_crew_username = validated_data.pop('delivery_crew_username', None)
        if delivery_crew_username:
            validated_data['delivery_crew'] = User.objects.get(username=delivery_crew_username)
        return super().update(instance, validated_data)

   
# Serializes and validates bookings, links to user instance
class BookingSerializer(serializers.HyperlinkedModelSerializer):
    user_details_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = ['url', 'user_details_url', 'id', 'name', 'no_of_guests', 'booking_date', 'reservation_status']
        read_only_fields = ['id']
        
    def get_user_details_url(self, obj):
        request = self.context.get('request')
        return reverse('user_api_view', args=[obj.user.username], request=request)
        
    def validate_no_of_guests(self, value):
            if value < 1:
                raise serializers.ValidationError("Number of guests must be at least 1.")
            if value > 15:
                raise serializers.ValidationError("Number of guests cannot exceed 15. ")
            return value
        
    def validate_booking_date(self, value):
            if value < timezone.now():
                raise serializers.ValidationError("Booking date must be in the future.")
            return value
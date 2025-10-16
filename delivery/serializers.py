from rest_framework import serializers
from .models import CustomerAddress,DeliveryLocation
import re
class CustomerAddressSerializer(serializers.ModelSerializer):
    """Serializer for CustomerAddress model with validation and delivery check"""
    
    # Read-only fields
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    
    # Additional computed fields
    delivery_available = serializers.SerializerMethodField()
    delivery_info = serializers.SerializerMethodField()
    formatted_address = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerAddress
        fields = [
            'id',
            'title', 
            'full_address',
            'pincode',
            'phone',
            'is_default',
            'created_at',
            'delivery_available',
            'delivery_info',
            'formatted_address'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_delivery_available(self, obj):
        """Check if delivery is available for this address"""
        try:
            location = DeliveryLocation.objects.get(pincode=obj.pincode, is_available=True)
            return True
        except DeliveryLocation.DoesNotExist:
            return False
    
    def get_delivery_info(self, obj):
        """Get delivery information for this address"""
        try:
            location = DeliveryLocation.objects.get(pincode=obj.pincode, is_available=True)
            return {
                'area_name': location.area_name,
                'city': location.city,
                'delivery_fee': float(location.delivery_fee),
                'minimum_order': float(location.minimum_order),
                'estimated_hours': location.estimated_delivery_hours
            }
        except DeliveryLocation.DoesNotExist:
            return {
                'area_name': 'Unknown',
                'city': 'Unknown',
                'delivery_fee': 0,
                'minimum_order': 0,
                'estimated_hours': 0,
                'message': 'Delivery not available to this location'
            }
    
    def get_formatted_address(self, obj):
        """Return formatted address string"""
        return f"{obj.full_address}, {obj.pincode}"
    
    # Field-level validations
    def validate_title(self, value):
        """Validate address title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Address title is required")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Address title must be at least 2 characters long")
        
        if len(value.strip()) > 50:
            raise serializers.ValidationError("Address title cannot exceed 50 characters")
        
        return value.strip().title()  # Clean and capitalize
    
    def validate_full_address(self, value):
        """Validate full address"""
        if not value or not value.strip():
            raise serializers.ValidationError("Full address is required")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Please provide a complete address (minimum 10 characters)")
        
        if len(value.strip()) > 500:
            raise serializers.ValidationError("Address is too long (maximum 500 characters)")
        
        return value.strip()
    
    def validate_pincode(self, value):
        """Validate pincode"""
        if not value:
            raise serializers.ValidationError("Pincode is required")
        
        # Remove any spaces and validate
        pincode = str(value).replace(' ', '')
        
        if not pincode.isdigit():
            raise serializers.ValidationError("Pincode must contain only digits")
        
        if len(pincode) != 6:
            raise serializers.ValidationError("Pincode must be exactly 6 digits")
        
        # Check if pincode exists in our delivery locations (optional)
        # Uncomment if you want to restrict to only serviceable areas during creation
        # if not DeliveryLocation.objects.filter(pincode=pincode).exists():
        #     raise serializers.ValidationError("We don't deliver to this pincode yet")
        
        return pincode
    
    def validate_phone(self, value):
        """Validate phone number"""
        if not value:
            raise serializers.ValidationError("Phone number is required")
        
        # Remove spaces, dashes, and other common separators
        phone = re.sub(r'[\s\-\(\)]+', '', str(value))
        
        # Check if it starts with country code
        if phone.startswith('+91'):
            phone = phone[3:]
        elif phone.startswith('91') and len(phone) == 12:
            phone = phone[2:]
        
        # Validate Indian mobile number
        if not phone.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        
        if len(phone) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits")
        
        if not phone.startswith(('6', '7', '8', '9')):
            raise serializers.ValidationError("Please enter a valid Indian mobile number")
        
        return phone
    
    # Object-level validation
    def validate(self, attrs):
        """Cross-field validation"""
        
        # Check if user is trying to set multiple default addresses
        if attrs.get('is_default', False):
            user = self.context['request'].user if self.context.get('request') else None
            
            if user and self.instance is None:  # Creating new address
                # Check if user already has a default address
                if CustomerAddress.objects.filter(user=user, is_default=True).exists():
                    # This will be handled in the view, but we can warn here
                    pass
        
        # Additional business logic validations
        pincode = attrs.get('pincode')
        if pincode:
            # You can add more complex validation here
            # For example, check if the pincode matches the address city
            pass
        
        return attrs
    
    def create(self, validated_data):
        """Custom create method"""
        # The user will be set in the view
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Custom update method"""
        # Handle default address logic
        if validated_data.get('is_default', False):
            # This will be handled in the view to avoid duplicate defaults
            pass
        
        return super().update(instance, validated_data)

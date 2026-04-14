# accounts/forms.py
from django import forms
from .models import User
from captcha.fields import CaptchaField

class ClientSignupForm(forms.ModelForm):
    captcha = CaptchaField()
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    
    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "password", "first_name", "last_name")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add helpful text for username field
        self.fields['username'].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    # def clean_phone_number(self):
    #     """Validate phone number uniqueness"""
    #     phone = self.cleaned_data.get('phone_number')
    #     if User.objects.filter(phone_number=phone).exists():
    #         raise forms.ValidationError("This phone number is already registered.")
    #     return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_client = True
        user.is_driver = False
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class DriverSignupForm(forms.ModelForm):
    captcha = CaptchaField()
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    
    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "password", "first_name", "last_name")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add helpful text for username field
        self.fields['username'].help_text = "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    # def clean_phone_number(self):
    #     """Validate phone number uniqueness"""
    #     phone = self.cleaned_data.get('phone_number')
    #     if User.objects.filter(phone_number=phone).exists():
    #         raise forms.ValidationError("This phone number is already registered.")
    #     return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_driver = True
        user.is_client = False
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# drivers/forms.py
from django import forms
from drivers.models import DriverProfile
from PIL import Image

class DriverProfileForm(forms.ModelForm):
    """Form for driver profile creation with ID and vehicle info"""
    
    class Meta:
        model = DriverProfile
        fields = ('id_number', 'id_photo', 'vehicle_type', 'vehicle_seats', 'location')
        labels = {
            'id_number': 'ID number',
            'id_photo': 'ID photo',
            'vehicle_type': 'Vehicle type',
            'vehicle_seats': 'Vehicle seats',
            'location': 'Location',
        }
        help_texts = {
            'location': 'City/neighborhood',
            'id_photo': 'Upload a clear photo of your ID (Max 5MB, JPEG/PNG, min 400x400px)',
        }
        widgets = {
            'vehicle_seats': forms.NumberInput(attrs={'min': 1, 'max': 50, 'value': 4}),
        }
    
    def clean_id_number(self):
        """Validate ID number uniqueness"""
        id_number = self.cleaned_data.get('id_number')
        # Check if ID already exists (excluding current instance if updating)
        qs = DriverProfile.objects.filter(id_number=id_number)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This ID number is already registered.")
        return id_number
    
    def clean_id_photo(self):
        """Validate ID photo upload"""
        f = self.cleaned_data.get('id_photo')
        if not f:
            raise forms.ValidationError("ID photo is required.")
        
        # Validate content type
        if hasattr(f, 'content_type') and f.content_type not in ('image/jpeg', 'image/png'):
            raise forms.ValidationError("Only JPEG/PNG formats are supported.")
        
        # Validate size (max 5MB)
        if hasattr(f, 'size') and f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Maximum file size is 5MB.")
        
        # Validate dimensions (min 400x400)
        try:
            image = Image.open(f)
            w, h = image.size
            if w < 400 or h < 400:
                raise forms.ValidationError(
                    "Image is too small. Minimum size is 400x400 pixels."
                )
            # Reset file pointer after reading
            f.seek(0)
        except Exception as e:
            if "too small" in str(e):
                raise
            raise forms.ValidationError(f"Invalid image file: {str(e)}")
        
        return f
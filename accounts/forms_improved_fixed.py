"""
IMPROVED ACCOUNTS FORMS - Enhanced Backend Logic
Robust validation, better error handling, and improved security
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile
import re

class EnhancedUserRegistrationForm(UserCreationForm):
    """
    Enhanced registration form with better validation
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'autocomplete': 'given-name'
        }),
        error_messages={
            'required': 'First name is required.',
            'max_length': 'First name cannot exceed 30 characters.'
        }
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'autocomplete': 'family-name'
        }),
        error_messages={
            'required': 'Last name is required.',
            'max_length': 'Last name cannot exceed 30 characters.'
        }
    )
    
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select Role'
        }),
        error_messages={
            'required': 'Please select a role.'
        }
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (Optional)',
            'autocomplete': 'tel'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Please enter a valid phone number.'
            )
        ]
    )
    
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password'
        }),
        error_messages={
            'required': 'Password is required.'
        }
    )
    
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password'
        }),
        error_messages={
            'required': 'Please confirm your password.'
        }
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'phone_number', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since we use email as username
        self.fields.pop('username', None)
    
    def clean_email(self):
        """Enhanced email validation"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError('A user with this email already exists.')
            
            # Enhanced email format validation
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                raise ValidationError('Please enter a valid email address.')
        
        return email
    
    def clean_first_name(self):
        """Enhanced name validation"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # Remove extra spaces and validate
            first_name = ' '.join(first_name.split())
            
            if not first_name.replace(' ', '').isalpha():
                raise ValidationError('First name should only contain letters.')
            
            if len(first_name) < 2:
                raise ValidationError('First name must be at least 2 characters long.')
        
        return first_name
    
    def clean_last_name(self):
        """Enhanced last name validation"""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # Remove extra spaces and validate
            last_name = ' '.join(last_name.split())
            
            if not last_name.replace(' ', '').isalpha():
                raise ValidationError('Last name should only contain letters.')
            
            if len(last_name) < 2:
                raise ValidationError('Last name must be at least 2 characters long.')
        
        return last_name
    
    def clean_password1(self):
        """Enhanced password validation"""
        password = self.cleaned_data.get('password1')
        if password:
            try:
                validate_password(password, user=User)
            except ValidationError as e:
                raise ValidationError(e.messages)
        
        return password
    
    def clean(self):
        """Enhanced form validation"""
        cleaned_data = super().clean()
        
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Enhanced save method"""
        user = super().save(commit=False)
        
        # Set username to email for authentication
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name'].title()
        user.last_name = self.cleaned_data['last_name'].title()
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
        
        return user

class EnhancedUserLoginForm(forms.Form):
    """
    Enhanced login form with better validation
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autocomplete': 'email',
            'autofocus': True
        }),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        }),
        error_messages={
            'required': 'Password is required.'
        }
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    
    def clean_email(self):
        """Enhanced email validation"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            
            # Basic email format validation
            if '@' not in email or '.' not in email:
                raise ValidationError('Please enter a valid email address.')
        
        return email
    
    def clean_password(self):
        """Enhanced password validation"""
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 6:
                raise ValidationError('Password must be at least 6 characters long.')
        
        return password

class EnhancedUserProfileForm(forms.ModelForm):
    """
    Enhanced user profile form with better validation
    """
    class Meta:
        model = UserProfile
        fields = ('institution', 'department', 'bio', 'phone_number', 'student_id', 'teacher_id')
        widgets = {
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Institution'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell us about yourself...',
                'rows': 4
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Student ID'
            }),
            'teacher_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teacher ID'
            })
        }
    
    def clean_institution(self):
        """Enhanced institution validation"""
        institution = self.cleaned_data.get('institution')
        if institution:
            institution = institution.strip()
            if len(institution) < 2:
                raise ValidationError('Institution name must be at least 2 characters long.')
        
        return institution
    
    def clean_department(self):
        """Enhanced department validation"""
        department = self.cleaned_data.get('department')
        if department:
            department = department.strip()
            if len(department) < 2:
                raise ValidationError('Department name must be at least 2 characters long.')
        
        return department
    
    def clean_bio(self):
        """Enhanced bio validation"""
        bio = self.cleaned_data.get('bio')
        if bio:
            bio = bio.strip()
            if len(bio) > 500:
                raise ValidationError('Bio cannot exceed 500 characters.')
        
        return bio
    
    def clean_phone_number(self):
        """Enhanced phone number validation"""
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            phone_number = phone_number.strip()
            
            # Enhanced phone number validation
            phone_regex = r'^\+?1?\d{9,15}$'
            if not re.match(phone_regex, phone_number):
                raise ValidationError('Please enter a valid phone number.')
        
        return phone_number

class PasswordChangeForm(forms.Form):
    """
    Enhanced password change form
    """
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
    
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password'
        })
    
    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })
    
    def clean_new_password(self):
        """Enhanced password validation"""
        password = self.cleaned_data.get('new_password')
        if password:
            try:
                validate_password(password, user=User)
            except ValidationError as e:
                raise ValidationError(e.messages)
        
        return password
    
    def clean(self):
        """Enhanced form validation"""
        cleaned_data = super().clean()
        
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('New passwords do not match.')
        
        return cleaned_data

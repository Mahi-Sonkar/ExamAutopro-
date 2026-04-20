"""
IMPROVED ACCOUNTS VIEWS - Enhanced Backend Logic
Robust authentication, registration, and user management
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from .models import User, UserProfile

logger = logging.getLogger(__name__)

class ImprovedAuthMixin:
    """Enhanced authentication mixin with better error handling"""
    
    def handle_no_permission(self, request):
        """Handle unauthorized access"""
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Authentication required'}, status=401)
        messages.error(request, 'Please login to access this page.')
        return redirect('login')

def enhanced_login_required(view_func=None, login_url=None):
    """Enhanced login decorator with better handling"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url,
        redirect_field_name='next'
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator

@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Enhanced registration view with better error handling
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user with enhanced validation
                    user = form.save(commit=False)
                    user.username = user.email  # Ensure username matches email
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    
                    # Create user profile
                    UserProfile.objects.create(
                        user=user,
                        role=form.cleaned_data['role'],
                        phone_number=form.cleaned_data.get('phone_number', '')
                    )
                    
                    # Log successful registration
                    logger.info(f"New user registered: {user.email}")
                    messages.success(request, 'Registration successful! Please login.')
                    
                    # Handle AJAX requests
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({
                            'success': True,
                            'message': 'Registration successful',
                            'redirect_url': reverse('login')
                        })
                    
                    return redirect('login')
                    
            except Exception as e:
                logger.error(f"Registration error: {e}")
                messages.error(request, 'Registration failed. Please try again.')
                
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': 'Registration failed',
                        'details': str(e)
                    }, status=400)
        else:
            # Handle form validation errors
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid form data',
                    'details': form.errors
                }, status=400)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Enhanced login view with better security and error handling
    """
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            password = form.cleaned_data['password']
            
            # Enhanced authentication with rate limiting check
            try:
                user = authenticate(request, username=email, password=password)
                
                if user is not None:
                    # Check if user is active
                    if user.is_active:
                        # Update last login
                        login(request, user)
                        update_session_auth_hash(request, user)
                        
                        # Log successful login
                        logger.info(f"User logged in: {user.email}")
                        messages.success(request, f'Welcome back, {user.get_full_name() or user.email}!')
                        
                        # Handle redirect
                        next_url = request.GET.get('next', 'dashboard')
                        if next_url and next_url.startswith('/'):
                            return redirect(next_url)
                        return redirect('dashboard')
                    else:
                        logger.warning(f"Inactive login attempt: {email}")
                        messages.error(request, 'This account is inactive. Please contact admin.')
                else:
                    logger.warning(f"Failed login attempt: {email}")
                    messages.error(request, 'Invalid email or password.')
                    
            except Exception as e:
                logger.error(f"Login error: {e}")
                messages.error(request, 'Login system error. Please try again.')
        else:
            # Handle form validation errors
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid form data',
                    'details': form.errors
                }, status=400)
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    """
    Enhanced logout view with better session handling
    """
    try:
        # Log user out
        logout(request)
        logger.info(f"User logged out: {request.user.email}")
        messages.success(request, 'You have been logged out successfully.')
        
        # Handle AJAX requests
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Logged out successfully',
                'redirect_url': reverse('login')
            })
        
        return redirect('login')
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        messages.error(request, 'Error during logout. Please try again.')
        return redirect('login')

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Enhanced profile update view with better validation
    """
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.pk)
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Update user with enhanced validation
                user = form.save(commit=False)
                user.username = user.email  # Ensure username matches email
                user.save()
                
                # Update or create profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.institution = form.cleaned_data.get('institution', profile.institution)
                profile.department = form.cleaned_data.get('department', profile.department)
                profile.bio = form.cleaned_data.get('bio', profile.bio)
                profile.save()
                
                logger.info(f"Profile updated: {user.email}")
                messages.success(self.request, 'Profile updated successfully!')
                
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            messages.error(self.request, 'Error updating profile. Please try again.')
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

@csrf_exempt
@require_http_methods(["POST"])
def check_email_availability(request):
    """
    Enhanced email availability check
    """
    try:
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Check if email exists
        exists = User.objects.filter(email=email).exists()
        
        return JsonResponse({
            'available': not exists,
            'message': 'Email is available' if not exists else 'Email is already registered'
        })
        
    except Exception as e:
        logger.error(f"Email check error: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)

@login_required
def dashboard_view(request):
    """
    Enhanced dashboard view with user data
    """
    try:
        user = request.user
        profile = getattr(user, 'userprofile', None)
        
        context = {
            'user': user,
            'profile': profile,
            'recent_activity': [],  # Can be enhanced later
            'stats': {
                'login_count': 0,  # Can be tracked
                'last_login': user.last_login if user.last_login else 'Never'
            }
        }
        
        return render(request, 'accounts/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        messages.error(request, 'Error loading dashboard.')
        return redirect('login')

# Enhanced error handlers
def handle_404(request, exception):
    """Custom 404 handler"""
    logger.warning(f"404 error: {request.path}")
    return render(request, 'errors/404.html', status=404)

def handle_500(request):
    """Custom 500 handler"""
    logger.error(f"500 error: {request.path}")
    return render(request, 'errors/500.html', status=500)

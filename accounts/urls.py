from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'user-profiles', views.UserProfileView, basename='user-profile')

urlpatterns = [
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('accounts/dj-rest-auth/registration/account-confirm-email/<str:key>/', views.CustomVerifyEmailView.as_view(), name='account_confirm_email'),
    path('api/auth/login/', views.CustomLoginView.as_view(),name='login'),
    path('api/auth/logout/', views.CustomLogoutView.as_view(),name='logout'),
    path('api/auth/password/change/', views.CustomPasswordChangeView.as_view(),name='password_change'),
    path('api/auth/password/reset/', views.CustomPasswordResetView.as_view(),name='password_reset'),
    path('api/auth/password/reset/confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(),name='password_reset_confirm'),

    path('api/', include(router.urls)),
]


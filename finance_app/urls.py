"""
FinanceHub URL Patterns
========================
All URLs for the finance application
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── PUBLIC ──────────────────────────────────
    path('',                    views.home,             name='home'),
    path('about/',              views.about,            name='about'),
    path('contact/',            views.contact,          name='contact'),

    # ── LOAN PRODUCTS ───────────────────────────
    path('loans/',              views.loan_products,    name='loan_products'),
    path('loans/<int:pk>/',     views.loan_product_detail, name='loan_product_detail'),

    # ── EMI CALCULATOR ──────────────────────────
    path('emi-calculator/',     views.emi_calculator,   name='emi_calculator'),

    # ── AUTH ─────────────────────────────────────
    path('register/',           views.register,         name='register'),
    path('login/',              views.user_login,       name='login'),
    path('logout/',             views.user_logout,      name='logout'),

    # ── DASHBOARD (LOGIN REQUIRED) ───────────────
    path('dashboard/',          views.dashboard,        name='dashboard'),
    path('profile/',            views.profile_view,     name='profile'),
    path('notifications/',      views.notifications,    name='notifications'),
    path('profile/kyc/', views.kyc_update, name='kyc_update'),
    path('profile/complete/',   views.complete_profile, name='complete_profile'),
  

    # ── LOAN APPLICATION ────────────────────────
    path('apply/',              views.apply_loan,       name='apply_loan'),
    path('apply/<int:product_id>/', views.apply_loan,   name='apply_loan_product'),
    path('my-loans/',           views.my_loans,         name='my_loans'),
    path('my-loans/<int:pk>/',  views.loan_detail,      name='loan_detail'),

    # ── EMI ─────────────────────────────────────
    path('emi/pay/<int:emi_id>/', views.pay_emi,        name='pay_emi'),

    # ── GOLD LOAN ───────────────────────────────
    path('gold-loan/',          views.gold_loan_apply,  name='gold_loan'),

    # ── AJAX API ────────────────────────────────
    path('api/emi-calculate/',  views.api_emi_calculate,     name='api_emi_calc'),
    path('api/product/<int:pk>/', views.api_loan_product_detail, name='api_product_detail'),
]
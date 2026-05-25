"""
FinanceHub Admin Configuration
Fully customized Django admin for NBFC finance platform
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Sum, Count
from .models import (
    Branch, CustomerProfile, LoanProduct, GoldPledge,
    CreditScore, LoanApplication, EMISchedule,
    Transaction, Document, Notification, Insurance
)


# ─────────────────────────────────────────
# BRANCH ADMIN
# ─────────────────────────────────────────

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display    = ['code', 'name', 'city', 'state', 'manager_name', 'is_active', 'created_at']
    list_filter     = ['state', 'is_active']
    search_fields   = ['code', 'name', 'city', 'manager_name']
    list_editable   = ['is_active']
    ordering        = ['state', 'name']
    fieldsets = (
        ('Branch Info', {'fields': ('code', 'name', 'is_active')}),
        ('Location', {'fields': ('address', 'city', 'state', 'pincode')}),
        ('Contact', {'fields': ('phone', 'email', 'manager_name')}),
    )


# ─────────────────────────────────────────
# CUSTOMER PROFILE ADMIN
# ─────────────────────────────────────────

class DocumentInline(admin.TabularInline):
    model   = Document
    extra   = 0
    fields  = ['document_type', 'file', 'status', 'uploaded_at']
    readonly_fields = ['uploaded_at']

class CreditScoreInline(admin.TabularInline):
    model   = CreditScore
    extra   = 0
    fields  = ['bureau', 'score', 'fetched_at', 'report_number']
    readonly_fields = ['fetched_at']

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display  = ['customer_id_short', 'full_name', 'phone', 'city', 'kyc_status_badge',
                     'active_loans_count', 'created_at']
    list_filter   = ['kyc_status', 'gender', 'employment_type', 'state', 'branch']
    search_fields = ['user__first_name', 'user__last_name', 'phone', 'pan_number', 'aadhaar_number']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']
    inlines       = [DocumentInline, CreditScoreInline]
    fieldsets = (
        ('User Account', {'fields': ('user', 'customer_id')}),
        ('Personal Info', {'fields': ('phone', 'alternate_phone', 'date_of_birth', 'gender', 'photo')}),
        ('Address', {'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode')}),
        ('KYC', {'fields': ('aadhaar_number', 'pan_number', 'kyc_status', 'kyc_verified_at')}),
        ('Financial', {'fields': ('annual_income', 'employment_type', 'employer_name')}),
        ('Branch', {'fields': ('branch',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def customer_id_short(self, obj):
        return str(obj.customer_id)[:8].upper() + '...'
    customer_id_short.short_description = 'Customer ID'

    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Name'

    def kyc_status_badge(self, obj):
        colors = {'VERIFIED': 'green', 'PENDING': 'orange', 'REJECTED': 'red'}
        color = colors.get(obj.kyc_status, 'gray')
        return format_html('<span style="color:{}; font-weight:bold;">●  {}</span>',
                           color, obj.get_kyc_status_display())
    kyc_status_badge.short_description = 'KYC'

    def active_loans_count(self, obj):
        count = obj.loan_applications.filter(status='ACTIVE').count()
        return format_html('<span style="color: #1976d2; font-weight:bold;">{}</span>', count)
    active_loans_count.short_description = 'Active Loans'


# ─────────────────────────────────────────
# LOAN PRODUCT ADMIN
# ─────────────────────────────────────────

@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display  = ['icon', 'name', 'loan_type', 'min_amount', 'max_amount',
                     'base_interest_rate', 'min_tenure_months', 'max_tenure_months', 'is_active']
    list_filter   = ['loan_type', 'is_active']
    list_editable = ['kyc_status'] 
    search_fields = ['name']
    list_editable = ['is_active', 'base_interest_rate']
    fieldsets = (
        ('Product Info', {'fields': ('name', 'loan_type', 'icon', 'description', 'is_active')}),
        ('Loan Limits', {'fields': ('min_amount', 'max_amount', 'min_tenure_months', 'max_tenure_months')}),
        ('Rates & Fees', {'fields': ('base_interest_rate', 'processing_fee_pct', 'prepayment_penalty')}),
        ('Features & Documents', {'fields': ('features', 'eligibility', 'documents_required')}),
    )


# ─────────────────────────────────────────
# GOLD PLEDGE ADMIN
# ─────────────────────────────────────────

@admin.register(GoldPledge)
class GoldPledgeAdmin(admin.ModelAdmin):
    list_display  = ['pledge_id_short', 'description', 'gold_purity', 'net_weight_g',
                     'market_value', 'pledge_value', 'is_released', 'pledged_at']
    list_filter   = ['is_released', 'gold_purity']
    search_fields = ['description', 'appraised_by']
    readonly_fields = ['pledge_id', 'pledged_at']

    def pledge_id_short(self, obj):
        return str(obj.pledge_id)[:8].upper()
    pledge_id_short.short_description = 'Pledge ID'


# ─────────────────────────────────────────
# LOAN APPLICATION ADMIN
# ─────────────────────────────────────────

class EMIScheduleInline(admin.TabularInline):
    model         = EMISchedule
    extra         = 0
    fields        = ['emi_number', 'due_date', 'emi_amount', 'principal_amt',
                     'interest_amt', 'outstanding_bal', 'is_paid', 'paid_date']
    readonly_fields = ['emi_number', 'principal_amt', 'interest_amt', 'outstanding_bal']

class TransactionInline(admin.TabularInline):
    model         = Transaction
    extra         = 0
    fields        = ['transaction_type', 'amount', 'payment_mode', 'status', 'processed_at']
    readonly_fields = ['transaction_id', 'processed_at']

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display  = ['reference_number', 'customer_name', 'product', 'requested_amount',
                     'status_badge', 'loan_officer', 'applied_at']
    list_filter   = ['status', 'product__loan_type', 'branch', 'applied_at']
    search_fields = ['reference_number', 'customer__user__first_name',
                     'customer__user__last_name', 'customer__phone']
    readonly_fields = ['application_id', 'reference_number', 'applied_at',
                       'approved_at', 'disbursed_at', 'closed_at']
    inlines       = [EMIScheduleInline, TransactionInline]
    date_hierarchy = 'applied_at'
    fieldsets = (
        ('Application', {'fields': ('application_id', 'reference_number', 'customer', 'product', 'branch')}),
        ('Loan Details', {'fields': ('requested_amount', 'approved_amount', 'disbursed_amount',
                                     'tenure_months', 'interest_rate', 'emi_amount', 'first_emi_date')}),
        ('Status', {'fields': ('status', 'loan_purpose', 'remarks', 'rejection_reason')}),
        ('Gold Loan', {'fields': ('gold_pledge',), 'classes': ('collapse',)}),
        ('Officers', {'fields': ('loan_officer', 'approved_by')}),
        ('Timestamps', {'fields': ('applied_at', 'approved_at', 'disbursed_at', 'closed_at'),
                        'classes': ('collapse',)}),
    )
    actions = ['approve_loans', 'reject_loans']

    def customer_name(self, obj):
        return obj.customer.user.get_full_name()
    customer_name.short_description = 'Customer'

    def status_badge(self, obj):
        color_map = {
            'DRAFT': '#9e9e9e', 'SUBMITTED': '#2196f3', 'UNDER_REVIEW': '#ff9800',
            'APPROVED': '#4caf50', 'DISBURSED': '#00bcd4', 'ACTIVE': '#1976d2',
            'CLOSED': '#607d8b', 'REJECTED': '#f44336', 'DEFAULTED': '#b71c1c'
        }
        color = color_map.get(obj.status, '#gray')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:12px;font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def approve_loans(self, request, queryset):
        queryset.filter(status='UNDER_REVIEW').update(
            status='APPROVED', approved_at=timezone.now(), approved_by=request.user
        )
    approve_loans.short_description = "✅ Approve selected loans"

    def reject_loans(self, request, queryset):
        queryset.exclude(status__in=['ACTIVE', 'CLOSED', 'DISBURSED']).update(status='REJECTED')
    reject_loans.short_description = "❌ Reject selected loans"


# ─────────────────────────────────────────
# TRANSACTION ADMIN
# ─────────────────────────────────────────

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ['transaction_id_short', 'loan', 'transaction_type', 'amount',
                     'payment_mode', 'status_badge', 'processed_at']
    list_filter   = ['transaction_type', 'status', 'payment_mode', 'processed_at']
    search_fields = ['loan__reference_number', 'reference_number']
    readonly_fields = ['transaction_id', 'processed_at']
    date_hierarchy = 'processed_at'

    def transaction_id_short(self, obj):
        return str(obj.transaction_id)[:8].upper()
    transaction_id_short.short_description = 'Txn ID'

    def status_badge(self, obj):
        colors = {'PENDING': 'orange', 'SUCCESS': 'green', 'FAILED': 'red', 'REVERSED': 'purple'}
        return format_html('<b style="color:{}">● {}</b>', colors.get(obj.status, 'gray'), obj.status)
    status_badge.short_description = 'Status'


# ─────────────────────────────────────────
# NOTIFICATION ADMIN
# ─────────────────────────────────────────

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['customer', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter   = ['notification_type', 'is_read', 'created_at']
    search_fields = ['customer__user__first_name', 'title']
    list_editable = ['is_read']


# ─────────────────────────────────────────
# INSURANCE ADMIN
# ─────────────────────────────────────────

@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display  = ['policy_number', 'loan', 'provider', 'coverage_amount', 'premium_amount',
                     'start_date', 'end_date', 'is_active']
    list_filter   = ['is_active', 'provider']
    search_fields = ['policy_number', 'loan__reference_number']

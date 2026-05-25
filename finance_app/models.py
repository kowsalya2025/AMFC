"""
FinanceHub Models
=================
Complete finance platform models inspired by Muthoot Finance / NBFC standards.

Modules:
- CustomerProfile
- LoanProduct
- LoanApplication
- GoldPledge
- EMISchedule
- Transaction
- Document
- Notification
- Branch
- LoanOfficer
- CreditScore
- Insurance
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


# ─────────────────────────────────────────
# CHOICES
# ─────────────────────────────────────────

class LoanStatus(models.TextChoices):
    DRAFT         = 'DRAFT',       'Draft'
    SUBMITTED     = 'SUBMITTED',   'Submitted'
    UNDER_REVIEW  = 'UNDER_REVIEW','Under Review'
    APPROVED      = 'APPROVED',    'Approved'
    DISBURSED     = 'DISBURSED',   'Disbursed'
    ACTIVE        = 'ACTIVE',      'Active'
    CLOSED        = 'CLOSED',      'Closed'
    REJECTED      = 'REJECTED',    'Rejected'
    DEFAULTED     = 'DEFAULTED',   'Defaulted'

class LoanType(models.TextChoices):
    GOLD_LOAN         = 'GOLD',      'Gold Loan'
    PERSONAL_LOAN     = 'PERSONAL',  'Personal Loan'
    HOME_LOAN         = 'HOME',      'Home Loan'
    BUSINESS_LOAN     = 'BUSINESS',  'Business Loan'
    VEHICLE_LOAN      = 'VEHICLE',   'Vehicle Loan'
    EDUCATION_LOAN    = 'EDUCATION', 'Education Loan'
    MICRO_FINANCE     = 'MICRO',     'Micro Finance'

class Gender(models.TextChoices):
    MALE   = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER  = 'O', 'Other'

class KYCStatus(models.TextChoices):
    PENDING   = 'PENDING',   'Pending'
    VERIFIED  = 'VERIFIED',  'Verified'
    REJECTED  = 'REJECTED',  'Rejected'

class PaymentMode(models.TextChoices):
    CASH   = 'CASH',   'Cash'
    UPI    = 'UPI',    'UPI'
    NEFT   = 'NEFT',   'NEFT'
    RTGS   = 'RTGS',   'RTGS'
    CHEQUE = 'CHEQUE', 'Cheque'
    AUTO   = 'AUTO',   'Auto Debit'


# ─────────────────────────────────────────
# BRANCH
# ─────────────────────────────────────────

class Branch(models.Model):
    code         = models.CharField(max_length=10, unique=True)
    name         = models.CharField(max_length=200)
    address      = models.TextField()
    city         = models.CharField(max_length=100)
    state        = models.CharField(max_length=100)
    pincode      = models.CharField(max_length=6)
    phone        = models.CharField(max_length=15)
    email        = models.EmailField()
    manager_name = models.CharField(max_length=200)
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Branches"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


# ─────────────────────────────────────────
# CUSTOMER PROFILE
# ─────────────────────────────────────────

class CustomerProfile(models.Model):
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    customer_id      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    phone            = models.CharField(max_length=15, unique=True)
    alternate_phone  = models.CharField(max_length=15, blank=True)
    date_of_birth    = models.DateField()
    gender           = models.CharField(max_length=1, choices=Gender.choices)
    photo            = models.ImageField(upload_to='customers/photos/', blank=True)

    # Address
    address_line1    = models.CharField(max_length=255)
    address_line2    = models.CharField(max_length=255, blank=True)
    city             = models.CharField(max_length=100)
    state            = models.CharField(max_length=100)
    pincode          = models.CharField(max_length=6)

    # KYC
    aadhaar_number   = models.CharField(max_length=12, unique=True)
    pan_number       = models.CharField(max_length=10, unique=True)
    kyc_status       = models.CharField(max_length=20, choices=KYCStatus.choices, default=KYCStatus.PENDING)
    kyc_verified_at  = models.DateTimeField(null=True, blank=True)

    # Financial
    annual_income    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    employment_type  = models.CharField(max_length=50, choices=[
        ('SALARIED', 'Salaried'), ('SELF_EMPLOYED', 'Self Employed'),
        ('BUSINESS', 'Business Owner'), ('RETIRED', 'Retired'), ('OTHER', 'Other')
    ])
    employer_name    = models.CharField(max_length=200, blank=True)

    branch           = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} | {self.phone}"

    @property
    def total_loans(self):
        return self.loan_applications.count()

    @property
    def active_loans(self):
        return self.loan_applications.filter(status=LoanStatus.ACTIVE).count()


# ─────────────────────────────────────────
# LOAN PRODUCT
# ─────────────────────────────────────────

class LoanProduct(models.Model):
    name                = models.CharField(max_length=200)
    loan_type           = models.CharField(max_length=20, choices=LoanType.choices)
    min_amount          = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount          = models.DecimalField(max_digits=12, decimal_places=2)
    min_tenure_months   = models.IntegerField()
    max_tenure_months   = models.IntegerField()
    base_interest_rate  = models.DecimalField(max_digits=5, decimal_places=2,
                            help_text="Annual interest rate %")
    processing_fee_pct  = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                            help_text="Processing fee as % of loan amount")
    prepayment_penalty  = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)
    description         = models.TextField()
    features            = models.JSONField(default=list, help_text='["Feature 1", "Feature 2"]')
    eligibility         = models.TextField()
    documents_required  = models.JSONField(default=list)
    is_active           = models.BooleanField(default=True)
    icon                = models.CharField(max_length=50, default='💰')
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['loan_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_loan_type_display()})"

    def calculate_emi(self, principal, tenure_months, rate=None):
        """Calculate EMI using standard formula: P * r * (1+r)^n / ((1+r)^n - 1)"""
        if rate is None:
            rate = self.base_interest_rate
        monthly_rate = Decimal(str(rate)) / Decimal('100') / Decimal('12')
        n = Decimal(str(tenure_months))
        P = Decimal(str(principal))
        if monthly_rate == 0:
            return P / n
        emi = P * monthly_rate * (1 + monthly_rate)**n / ((1 + monthly_rate)**n - 1)
        return round(emi, 2)


# ─────────────────────────────────────────
# GOLD PLEDGE (for Gold Loans)
# ─────────────────────────────────────────

class GoldPledge(models.Model):
    pledge_id       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    description     = models.CharField(max_length=500)
    gold_purity     = models.DecimalField(max_digits=5, decimal_places=2,
                        help_text="Purity in karats (e.g. 22.00)")
    gross_weight_g  = models.DecimalField(max_digits=8, decimal_places=3)
    net_weight_g    = models.DecimalField(max_digits=8, decimal_places=3)
    gold_rate_per_g = models.DecimalField(max_digits=10, decimal_places=2,
                        help_text="Gold rate on pledge date")
    market_value    = models.DecimalField(max_digits=12, decimal_places=2)
    pledge_value    = models.DecimalField(max_digits=12, decimal_places=2,
                        help_text="Typically 75% of market value (RBI norm)")
    pledged_at      = models.DateTimeField(auto_now_add=True)
    released_at     = models.DateTimeField(null=True, blank=True)
    is_released     = models.BooleanField(default=False)
    appraised_by    = models.CharField(max_length=200)
    photo           = models.ImageField(upload_to='gold_pledges/', blank=True)

    def __str__(self):
        return f"Pledge #{self.pledge_id} | {self.net_weight_g}g @ {self.gold_purity}K"


# ─────────────────────────────────────────
# CREDIT SCORE
# ─────────────────────────────────────────

class CreditScore(models.Model):
    customer        = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE,
                        related_name='credit_scores')
    score           = models.IntegerField(validators=[MinValueValidator(300), MaxValueValidator(900)])
    bureau          = models.CharField(max_length=50, choices=[
        ('CIBIL', 'CIBIL'), ('EXPERIAN', 'Experian'),
        ('EQUIFAX', 'Equifax'), ('CRIF', 'CRIF High Mark')
    ])
    fetched_at      = models.DateTimeField(auto_now_add=True)
    report_number   = models.CharField(max_length=100)
    remarks         = models.TextField(blank=True)

    class Meta:
        ordering = ['-fetched_at']

    def __str__(self):
        return f"{self.customer} | Score: {self.score} ({self.bureau})"

    @property
    def rating(self):
        if self.score >= 750: return "Excellent"
        if self.score >= 700: return "Good"
        if self.score >= 650: return "Fair"
        return "Poor"


# ─────────────────────────────────────────
# LOAN APPLICATION
# ─────────────────────────────────────────

class LoanApplication(models.Model):
    application_id      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference_number    = models.CharField(max_length=20, unique=True, editable=False)
    customer            = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE,
                            related_name='loan_applications')
    product             = models.ForeignKey(LoanProduct, on_delete=models.PROTECT)
    branch              = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)

    # Loan Details
    requested_amount    = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount     = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    disbursed_amount    = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tenure_months       = models.IntegerField()
    interest_rate       = models.DecimalField(max_digits=5, decimal_places=2)
    emi_amount          = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Status
    status              = models.CharField(max_length=20, choices=LoanStatus.choices,
                            default=LoanStatus.DRAFT)

    # Gold Loan specific
    gold_pledge         = models.OneToOneField(GoldPledge, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='loan')

    # Purpose
    loan_purpose        = models.TextField()

    # Dates
    applied_at          = models.DateTimeField(auto_now_add=True)
    approved_at         = models.DateTimeField(null=True, blank=True)
    disbursed_at        = models.DateTimeField(null=True, blank=True)
    closed_at           = models.DateTimeField(null=True, blank=True)
    first_emi_date      = models.DateField(null=True, blank=True)

    # Officers
    loan_officer        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                            related_name='assigned_loans')
    approved_by         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                            blank=True, related_name='approved_loans')

    remarks             = models.TextField(blank=True)
    rejection_reason    = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.reference_number} | {self.customer} | ₹{self.requested_amount}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            import random, string
            prefix = self.product.loan_type[:2].upper()
            suffix = ''.join(random.choices(string.digits, k=8))
            self.reference_number = f"FH{prefix}{suffix}"
        super().save(*args, **kwargs)

    @property
    def outstanding_balance(self):
        paid = self.transactions.filter(
            transaction_type='EMI', status='SUCCESS'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        return (self.disbursed_amount or Decimal('0')) - paid

    @property
    def total_emis(self):
        return self.tenure_months

    @property
    def paid_emis(self):
        return self.transactions.filter(transaction_type='EMI', status='SUCCESS').count()


# ─────────────────────────────────────────
# EMI SCHEDULE
# ─────────────────────────────────────────

class EMISchedule(models.Model):
    loan            = models.ForeignKey(LoanApplication, on_delete=models.CASCADE,
                        related_name='emi_schedule')
    emi_number      = models.IntegerField()
    due_date        = models.DateField()
    principal_amt   = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amt    = models.DecimalField(max_digits=12, decimal_places=2)
    emi_amount      = models.DecimalField(max_digits=12, decimal_places=2)
    outstanding_bal = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid         = models.BooleanField(default=False)
    paid_date       = models.DateField(null=True, blank=True)
    late_fee        = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['emi_number']
        unique_together = ['loan', 'emi_number']

    def __str__(self):
        return f"{self.loan.reference_number} | EMI #{self.emi_number} | Due: {self.due_date}"

    @property
    def is_overdue(self):
        return not self.is_paid and self.due_date < timezone.now().date()


# ─────────────────────────────────────────
# TRANSACTION
# ─────────────────────────────────────────

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('DISBURSEMENT', 'Disbursement'),
        ('EMI',          'EMI Payment'),
        ('PREPAYMENT',   'Pre-payment'),
        ('PENALTY',      'Penalty'),
        ('REFUND',       'Refund'),
        ('FEE',          'Fee'),
    ]
    STATUS = [
        ('PENDING',  'Pending'),
        ('SUCCESS',  'Success'),
        ('FAILED',   'Failed'),
        ('REVERSED', 'Reversed'),
    ]

    transaction_id      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    loan                = models.ForeignKey(LoanApplication, on_delete=models.CASCADE,
                            related_name='transactions')
    transaction_type    = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount              = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode        = models.CharField(max_length=20, choices=PaymentMode.choices)
    reference_number    = models.CharField(max_length=100, blank=True)
    status              = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    remarks             = models.TextField(blank=True)
    processed_at        = models.DateTimeField(auto_now_add=True)
    emi_schedule        = models.ForeignKey(EMISchedule, on_delete=models.SET_NULL,
                            null=True, blank=True)

    class Meta:
        ordering = ['-processed_at']

    def __str__(self):
        return f"{self.transaction_type} | ₹{self.amount} | {self.status}"


# ─────────────────────────────────────────
# DOCUMENT
# ─────────────────────────────────────────

class Document(models.Model):
    DOC_TYPES = [
        ('AADHAAR',        'Aadhaar Card'),
        ('PAN',            'PAN Card'),
        ('PHOTO',          'Photograph'),
        ('INCOME_PROOF',   'Income Proof'),
        ('BANK_STATEMENT', 'Bank Statement'),
        ('PROPERTY_DOC',   'Property Document'),
        ('VEHICLE_RC',     'Vehicle RC'),
        ('OTHER',          'Other'),
    ]
    DOC_STATUS = [
        ('PENDING',  'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    customer        = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE,
                        related_name='documents')
    loan            = models.ForeignKey(LoanApplication, on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='documents')
    document_type   = models.CharField(max_length=30, choices=DOC_TYPES)
    file            = models.FileField(upload_to='documents/%Y/%m/')
    status          = models.CharField(max_length=20, choices=DOC_STATUS, default='PENDING')
    uploaded_at     = models.DateTimeField(auto_now_add=True)
    verified_at     = models.DateTimeField(null=True, blank=True)
    verified_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    remarks         = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer} | {self.get_document_type_display()}"


# ─────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────

class Notification(models.Model):
    NOTIF_TYPES = [
        ('EMI_REMINDER',    'EMI Reminder'),
        ('APPROVAL',        'Loan Approved'),
        ('DISBURSEMENT',    'Loan Disbursed'),
        ('KYC',             'KYC Update'),
        ('OVERDUE',         'Overdue Alert'),
        ('OFFER',           'Special Offer'),
        ('SYSTEM',          'System Notification'),
    ]

    customer        = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE,
                        related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIF_TYPES)
    title           = models.CharField(max_length=200)
    message         = models.TextField()
    is_read         = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
    action_url      = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer} | {self.title}"


# ─────────────────────────────────────────
# INSURANCE
# ─────────────────────────────────────────

class Insurance(models.Model):
    loan            = models.OneToOneField(LoanApplication, on_delete=models.CASCADE,
                        related_name='insurance')
    policy_number   = models.CharField(max_length=100, unique=True)
    provider        = models.CharField(max_length=200)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    premium_amount  = models.DecimalField(max_digits=10, decimal_places=2)
    start_date      = models.DateField()
    end_date        = models.DateField()
    is_active       = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.policy_number} | {self.loan.reference_number}"

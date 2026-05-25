"""
FinanceHub Views
================
All views for the finance platform: home, dashboard, loans, EMI, transactions, etc.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    CustomerProfile, Gender, LoanProduct, LoanApplication, EMISchedule,
    Transaction, Notification, GoldPledge, CreditScore, Branch
)
from .forms import (
    CustomerRegistrationForm, LoanApplicationForm,
    GoldPledgeForm, EMIPaymentForm
)


# ─────────────────────────────────────────
# PUBLIC VIEWS
# ─────────────────────────────────────────

def home(request):
    """Landing page with loan products and stats"""
    products    = LoanProduct.objects.filter(is_active=True)
    stats = {
        'total_customers': CustomerProfile.objects.count(),
        'total_loans':     LoanApplication.objects.count(),
        'active_loans':    LoanApplication.objects.filter(status='ACTIVE').count(),
        'branches':        Branch.objects.filter(is_active=True).count(),
    }
    return render(request, 'finance_app/home.html', {
        'products': products,
        'stats': stats,
    })


def about(request):
    return render(request, 'finance_app/about.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, "Thank you! We'll contact you shortly.")
        return redirect('contact')
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'finance_app/contact.html', {'branches': branches})


def loan_products(request):
    """Show all loan products with filtering"""
    loan_type = request.GET.get('type', '')
    products  = LoanProduct.objects.filter(is_active=True)
    if loan_type:
        products = products.filter(loan_type=loan_type)
    return render(request, 'finance_app/loan_products.html', {
        'products': products,
        'selected_type': loan_type,
        'loan_types': LoanProduct.objects.values('loan_type').distinct(),
    })


def loan_product_detail(request, pk):
    product = get_object_or_404(LoanProduct, pk=pk, is_active=True)
    return render(request, 'finance_app/loan_product_detail.html', {'product': product})


def emi_calculator(request):
    """EMI Calculator - works without login"""
    result = None
    if request.method == 'POST' or request.GET.get('principal'):
        try:
            principal = Decimal(request.POST.get('principal') or request.GET.get('principal', '0'))
            rate      = Decimal(request.POST.get('rate') or request.GET.get('rate', '0'))
            tenure    = int(request.POST.get('tenure') or request.GET.get('tenure', '0'))

            monthly_rate = rate / 100 / 12
            if monthly_rate > 0:
                emi = principal * monthly_rate * (1 + monthly_rate)**tenure / ((1 + monthly_rate)**tenure - 1)
            else:
                emi = principal / tenure

            total_amount  = emi * tenure
            total_interest = total_amount - principal

            schedule = []
            balance = principal
            for i in range(1, tenure + 1):
                interest_part = balance * monthly_rate
                principal_part = emi - interest_part
                balance -= principal_part
                schedule.append({
                    'month': i,
                    'emi': round(emi, 2),
                    'principal': round(principal_part, 2),
                    'interest': round(interest_part, 2),
                    'balance': round(max(balance, 0), 2),
                })

            result = {
                'emi':            round(emi, 2),
                'total_amount':   round(total_amount, 2),
                'total_interest': round(total_interest, 2),
                'principal':      principal,
                'rate':           rate,
                'tenure':         tenure,
                'schedule':       schedule,
            }
        except Exception as e:
            messages.error(request, "Please enter valid values.")

    return render(request, 'finance_app/emi_calculator.html', {'result': result})


# ─────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to FinanceHub! Complete your KYC to apply for loans.")
            return redirect('dashboard')
    else:
        form = CustomerRegistrationForm()
    return render(request, 'finance_app/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        # Fallback to authenticate by email
        if not user and '@' in username:
            try:
                from django.contrib.auth.models import User
                user_obj = User.objects.get(email__iexact=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
                
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'finance_app/login.html')


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────

@login_required
def dashboard(request):
    try:
        profile = request.user.profile
    except CustomerProfile.DoesNotExist:
        messages.warning(request, "Please complete your profile.")
        return redirect('complete_profile')

    loans = LoanApplication.objects.filter(customer=profile).order_by('-applied_at')

    # Stats
    active_loans   = loans.filter(status='ACTIVE')
    total_outstanding = active_loans.aggregate(
        total=Sum('disbursed_amount'))['total'] or Decimal('0')

    upcoming_emis  = EMISchedule.objects.filter(
        loan__customer=profile,
        is_paid=False,
        due_date__gte=date.today(),
        due_date__lte=date.today() + timedelta(days=30)
    ).order_by('due_date')[:5]

    overdue_emis   = EMISchedule.objects.filter(
        loan__customer=profile,
        is_paid=False,
        due_date__lt=date.today()
    )

    recent_txns    = Transaction.objects.filter(
        loan__customer=profile
    ).order_by('-processed_at')[:5]

    notifications  = Notification.objects.filter(
        customer=profile, is_read=False
    ).order_by('-created_at')[:5]

    credit_score   = CreditScore.objects.filter(customer=profile).first()

    return render(request, 'finance_app/dashboard.html', {
        'profile':          profile,
        'loans':            loans[:5],
        'active_loans':     active_loans,
        'total_outstanding': total_outstanding,
        'upcoming_emis':    upcoming_emis,
        'overdue_emis':     overdue_emis,
        'recent_txns':      recent_txns,
        'notifications':    notifications,
        'credit_score':     credit_score,
    })


# ─────────────────────────────────────────
# LOAN APPLICATION
# ─────────────────────────────────────────

@login_required
def apply_loan(request, product_id=None):
    profile = get_object_or_404(CustomerProfile, user=request.user)

    if profile.kyc_status != 'VERIFIED':
        messages.warning(request, "Please complete KYC verification before applying for loans.")
        return redirect('dashboard')

    product = None
    if product_id:
        product = get_object_or_404(LoanProduct, pk=product_id, is_active=True)

    if request.method == 'POST':
        # Get values directly from POST
        product_id_post  = request.POST.get('product')
        requested_amount = request.POST.get('requested_amount')
        tenure_months    = request.POST.get('tenure_months')
        interest_rate    = request.POST.get('interest_rate')
        loan_purpose     = request.POST.get('loan_purpose')

        # Validate
        errors = []
        if not product_id_post:
            errors.append("Please select a loan product.")
        if not requested_amount:
            errors.append("Please enter loan amount.")
        if not loan_purpose:
            errors.append("Please enter loan purpose.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                selected_product = get_object_or_404(LoanProduct, pk=product_id_post)
                loan = LoanApplication.objects.create(
                    customer         = profile,
                    product          = selected_product,
                    requested_amount = Decimal(requested_amount),
                    tenure_months    = int(tenure_months),
                    interest_rate    = Decimal(interest_rate),
                    loan_purpose     = loan_purpose,
                    status           = 'SUBMITTED',
                    branch           = profile.branch,
                )
                loan.emi_amount = selected_product.calculate_emi(
                    loan.requested_amount,
                    loan.tenure_months,
                    loan.interest_rate
                )
                loan.save()

                Notification.objects.create(
                    customer          = profile,
                    notification_type = 'SYSTEM',
                    title             = 'Loan Application Submitted',
                    message           = f'Your {loan.product.name} application #{loan.reference_number} has been submitted.',
                    action_url        = f'/my-loans/{loan.pk}/'
                )

                messages.success(request, f"Application submitted! Reference: {loan.reference_number}")
                return redirect('loan_detail', pk=loan.pk)

            except Exception as e:
                messages.error(request, f"Error submitting application: {e}")

    products = LoanProduct.objects.filter(is_active=True)
    return render(request, 'finance_app/apply_loan.html', {
        'form':     None,
        'product':  product,
        'products': products,
    })


@login_required
def loan_detail(request, pk):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    loan    = get_object_or_404(LoanApplication, pk=pk, customer=profile)
    emi_schedule = loan.emi_schedule.all()
    transactions = loan.transactions.all()
    

    return render(request, 'finance_app/loan_detail.html', {
        'loan': loan,
        'emi_schedule': emi_schedule,
        'transactions': transactions,
    })


@login_required
def my_loans(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    status  = request.GET.get('status', '')
    loans   = LoanApplication.objects.filter(customer=profile)
    if status:
        loans = loans.filter(status=status)
    return render(request, 'finance_app/my_loans.html', {
        'loans': loans,
        'status': status,
    })


# ─────────────────────────────────────────
# EMI PAYMENT
# ─────────────────────────────────────────

@login_required
def pay_emi(request, emi_id):
    profile  = get_object_or_404(CustomerProfile, user=request.user)
    emi      = get_object_or_404(EMISchedule, pk=emi_id, loan__customer=profile)

    if emi.is_paid:
        messages.info(request, "This EMI is already paid.")
        return redirect('loan_detail', pk=emi.loan.pk)

    if request.method == 'POST':
        form = EMIPaymentForm(request.POST)
        if form.is_valid():
            # Create transaction
            txn = Transaction.objects.create(
                loan=emi.loan,
                transaction_type='EMI',
                amount=emi.emi_amount,
                payment_mode=form.cleaned_data['payment_mode'],
                reference_number=form.cleaned_data.get('reference_number', ''),
                status='SUCCESS',
                emi_schedule=emi
            )
            # Mark EMI paid
            emi.is_paid   = True
            emi.paid_date = date.today()
            emi.save()

            messages.success(request, f"EMI #{emi.emi_number} paid successfully! Txn: {txn.transaction_id}")
            return redirect('loan_detail', pk=emi.loan.pk)
    else:
        form = EMIPaymentForm()

    return render(request, 'finance_app/pay_emi.html', {
        'emi': emi,
        'form': form,
    })


# ─────────────────────────────────────────
# GOLD LOAN FLOW
# ─────────────────────────────────────────

@login_required
def gold_loan_apply(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)

    if request.method == 'POST':
        pledge_form = GoldPledgeForm(request.POST, request.FILES)
        if pledge_form.is_valid():
            pledge = pledge_form.save()
            gold_product = LoanProduct.objects.filter(loan_type='GOLD', is_active=True).first()
            if gold_product:
                loan = LoanApplication.objects.create(
                    customer=profile,
                    product=gold_product,
                    requested_amount=pledge.pledge_value,
                    tenure_months=12,
                    interest_rate=gold_product.base_interest_rate,
                    loan_purpose='Gold Loan against pledged ornaments',
                    gold_pledge=pledge,
                    status='SUBMITTED',
                )
                loan.emi_amount = gold_product.calculate_emi(pledge.pledge_value, 12)
                loan.save()
                messages.success(request, f"Gold loan applied! Ref: {loan.reference_number}")
                return redirect('loan_detail', pk=loan.pk)
    else:
        pledge_form = GoldPledgeForm()

    return render(request, 'finance_app/gold_loan.html', {'form': pledge_form})


# ─────────────────────────────────────────
# PROFILE & KYC
# ─────────────────────────────────────────

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except CustomerProfile.DoesNotExist:
         return redirect('complete_profile')
      

    credit_scores = CreditScore.objects.filter(customer=profile)
    documents     = profile.documents.all()
    return render(request, 'finance_app/profile.html', {
        'profile': profile,
        'credit_scores': credit_scores,
        'documents': documents,
    })


# ─────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────

@login_required
def notifications(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    notifs  = Notification.objects.filter(customer=profile)
    # Mark all as read
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'finance_app/notifications.html', {'notifications': notifs})


# ─────────────────────────────────────────
# AJAX / API ENDPOINTS
# ─────────────────────────────────────────

def api_emi_calculate(request):
    """AJAX EMI calculation endpoint"""
    try:
        principal = Decimal(request.GET.get('principal', '0'))
        rate      = Decimal(request.GET.get('rate', '0'))
        tenure    = int(request.GET.get('tenure', '0'))
        monthly_rate = rate / 100 / 12
        if monthly_rate > 0:
            emi = principal * monthly_rate * (1 + monthly_rate)**tenure / ((1 + monthly_rate)**tenure - 1)
        else:
            emi = principal / tenure
        return JsonResponse({
            'emi': float(round(emi, 2)),
            'total': float(round(emi * tenure, 2)),
            'interest': float(round(emi * tenure - principal, 2)),
        })
    except Exception:
        return JsonResponse({'error': 'Invalid input'}, status=400)


def api_loan_product_detail(request, pk):
    """AJAX product details for apply form"""
    product = get_object_or_404(LoanProduct, pk=pk)
    return JsonResponse({
        'min_amount': float(product.min_amount),
        'max_amount': float(product.max_amount),
        'min_tenure': product.min_tenure_months,
        'max_tenure': product.max_tenure_months,
        'rate':       float(product.base_interest_rate),
        'features':   product.features,
    })


@login_required
def kyc_update(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)

    if profile.kyc_status == 'VERIFIED':
        messages.info(request, "Your KYC is already verified.")
        return redirect('profile')

    if request.method == 'POST':
        aadhaar = request.POST.get('aadhaar_number', '').strip()
        pan     = request.POST.get('pan_number', '').strip()
        phone   = request.POST.get('phone', '').strip()

        # Validate
        errors = []
        if len(aadhaar) != 12 or not aadhaar.isdigit():
            errors.append("Aadhaar must be 12 digits.")
        if len(pan) != 10:
            errors.append("PAN must be 10 characters.")
        if len(phone) < 10:
            errors.append("Enter a valid phone number.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            # Update profile fields
            profile.aadhaar_number = aadhaar
            profile.pan_number     = pan.upper()
            profile.phone          = phone
            profile.kyc_status     = 'PENDING'
            profile.save()

            # Save uploaded documents
            doc_fields = {
                'aadhaar_front': 'AADHAAR',
                'pan_card':      'PAN',
                'photo':         'PHOTO',
            }
            for field_name, doc_type in doc_fields.items():
                file = request.FILES.get(field_name)
                if file:
                    from .models import Document
                    Document.objects.update_or_create(
                        customer=profile,
                        document_type=doc_type,
                        defaults={'file': file, 'status': 'PENDING'}
                    )

            messages.success(request, "KYC submitted! Verification takes 24–48 hours.")
            return redirect('profile')

    return render(request, 'finance_app/kyc_update.html', {'profile': profile})

@login_required
def complete_profile(request):
    try:
        request.user.profile
        return redirect('dashboard')  # already has profile, go to dashboard
    except CustomerProfile.DoesNotExist:
        pass

    return render(request, 'finance_app/complete_profile.html', {
        'profile': None,
        'employment_choices': CustomerProfile._meta.get_field('employment_type').choices,
        'gender_choices': Gender.choices,
    })
"""
FinanceHub Forms
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import CustomerProfile, LoanApplication, GoldPledge, LoanProduct


class CustomerRegistrationForm(UserCreationForm):
    first_name  = forms.CharField(max_length=100, required=True)
    last_name   = forms.CharField(max_length=100, required=True)
    email       = forms.EmailField(required=True)
    phone       = forms.CharField(max_length=15)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    gender      = forms.ChoiceField(choices=[('M','Male'),('F','Female'),('O','Other')])
    address_line1 = forms.CharField(max_length=255)
    city        = forms.CharField(max_length=100)
    state       = forms.CharField(max_length=100)
    pincode     = forms.CharField(max_length=6)
    aadhaar_number = forms.CharField(max_length=12)
    pan_number  = forms.CharField(max_length=10)
    annual_income = forms.DecimalField(max_digits=12, decimal_places=2)
    employment_type = forms.ChoiceField(choices=[
        ('SALARIED','Salaried'), ('SELF_EMPLOYED','Self Employed'),
        ('BUSINESS','Business Owner'), ('RETIRED','Retired'), ('OTHER','Other')
    ])

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        if commit:
            user.save()
            CustomerProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                gender=self.cleaned_data['gender'],
                address_line1=self.cleaned_data['address_line1'],
                city=self.cleaned_data['city'],
                state=self.cleaned_data['state'],
                pincode=self.cleaned_data['pincode'],
                aadhaar_number=self.cleaned_data['aadhaar_number'],
                pan_number=self.cleaned_data['pan_number'].upper(),
                annual_income=self.cleaned_data['annual_income'],
                employment_type=self.cleaned_data['employment_type'],
            )
        return user


class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model  = LoanApplication
        fields = ['product', 'requested_amount', 'tenure_months', 'interest_rate', 'loan_purpose']
        widgets = {
            'loan_purpose':    forms.Textarea(attrs={'rows': 3}),
            'requested_amount': forms.NumberInput(attrs={'step': '1000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = LoanProduct.objects.filter(is_active=True)
        self.fields['interest_rate'].widget.attrs['readonly'] = True
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class GoldPledgeForm(forms.ModelForm):
    class Meta:
        model  = GoldPledge
        fields = ['description', 'gold_purity', 'gross_weight_g', 'net_weight_g',
                  'gold_rate_per_g', 'market_value', 'pledge_value', 'appraised_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class EMIPaymentForm(forms.Form):
    payment_mode     = forms.ChoiceField(choices=[
        ('UPI', 'UPI'), ('NEFT', 'NEFT'), ('RTGS', 'RTGS'),
        ('CASH', 'Cash'), ('CHEQUE', 'Cheque'),
    ])
    reference_number = forms.CharField(max_length=100, required=False,
                        help_text="UTR/Cheque/Reference number")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
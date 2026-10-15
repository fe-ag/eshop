from django import forms
from django.contrib.auth import authenticate, password_validation

from utils.validators import validate_phone

from .models import User

INPUT = {'class': 'form-control'}


class RegisterForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=150)
    last_name = forms.CharField(label='Last Name', max_length=150)
    email = forms.EmailField(label='Email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    phone = forms.CharField(label='Phone Number', max_length=20, validators=[validate_phone])
    country = forms.CharField(label='Country', max_length=80)
    state = forms.CharField(label='State / Province', max_length=80)
    city = forms.CharField(label='City', max_length=80)
    street_address = forms.CharField(label='Street Address', max_length=255)
    postal_code = forms.CharField(label='Postal Code', max_length=20)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(INPUT)
        self.fields['email'].widget.attrs['autocomplete'] = 'email'
        self.fields['password'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['confirm_password'].widget.attrs['autocomplete'] = 'new-password'

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'The two passwords do not match.')
        elif password:
            candidate = User(
                email=cleaned.get('email', ''),
                first_name=cleaned.get('first_name', ''),
                last_name=cleaned.get('last_name', ''),
            )
            try:
                password_validation.validate_password(password, candidate)
            except forms.ValidationError as error:
                self.add_error('password', error)
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User(
            username=data['email'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            country=data['country'],
            state=data['state'],
            city=data['city'],
            street_address=data['street_address'],
            postal_code=data['postal_code'],
        )
        user.set_password(data['password'])
        user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={**INPUT, 'autocomplete': 'email'}))
    password = forms.CharField(
        label='Password', widget=forms.PasswordInput(attrs={**INPUT, 'autocomplete': 'current-password'}))

    error_messages = {
        'invalid': 'Incorrect email or password.',
        'inactive': 'This account is disabled.',
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
        password = cleaned.get('password')
        if email and password:
            account = User.objects.filter(email__iexact=email.strip()).first()
            # authenticate() with the real username keeps all Django password protections.
            user = authenticate(self.request, username=account.username, password=password) if account else None
            if user is None:
                if account is not None and not account.is_active and account.check_password(password):
                    raise forms.ValidationError(self.error_messages['inactive'])
                raise forms.ValidationError(self.error_messages['invalid'])
            self.user = user
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        labels = {'first_name': 'First Name', 'last_name': 'Last Name', 'email': 'Email', 'phone': 'Phone Number'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(INPUT)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone'].required = True
        self.fields['phone'].validators.append(validate_phone)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        clash = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        old_email = User.objects.get(pk=self.instance.pk).email
        user = super().save(commit=False)
        if user.username.lower() == old_email.lower():
            user.username = user.email
        if commit:
            user.save()
        return user


class AddressForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['country', 'state', 'city', 'street_address', 'postal_code']
        labels = {
            'country': 'Country', 'state': 'State / Province', 'city': 'City',
            'street_address': 'Street Address', 'postal_code': 'Postal Code',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
            field.widget.attrs.update(INPUT)

from datetime import date
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Client, Employee, Order, Promocode, Review, Tour


class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ['title', 'country', 'hotel', 'duration_weeks', 'base_price', 'description', 'image']


class PromocodeForm(forms.ModelForm):
    class Meta:
        model = Promocode
        fields = ['code', 'tour', 'discount_percent', 'valid_until', 'is_active']
        widgets = {
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['tour', 'rating', 'text']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            try:
                client = Client.objects.get(user=user)
                tours = Tour.objects.filter(order__client=client).distinct()
                self.fields['tour'].queryset = tours
            except Client.DoesNotExist:
                self.fields['tour'].queryset = Tour.objects.none()


class OrderForm(forms.ModelForm):
    promo_code_input = forms.CharField(label="Промокод", required=False)
    
    class Meta:
        model = Order
        fields = ['tour', 'employee', 'departure_date', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.all()
        self.fields['departure_date'].widget = forms.SelectDateWidget()

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get("promo_code_input")
        tour = cleaned_data.get("tour")

        if code:
            try:
                promo = Promocode.objects.get(code=code, tour=tour, is_active=True)
                cleaned_data["promo_code"] = promo
            except Promocode.DoesNotExist:
                raise forms.ValidationError("Неверный или неактивный промокод.")
        return cleaned_data


class SelectEmployeeForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['employee']
        labels = {
            'employee': 'Выберите консультанта, с которым хотите работать'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].widget.attrs.update({
            'class': 'form-select form-select-lg',
        })


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Имя", max_length=100)
    last_name = forms.CharField(label="Фамилия", max_length=100)
    patronymic = forms.CharField(label="Отчество", max_length=100, required=False)
    address = forms.CharField(label="Адрес", max_length=255)
    phone = forms.CharField(label="Телефон", max_length=20)
    birth_date = forms.DateField(label="Дата рождения", widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = [
            "username", "email", "password1", "password2",
            "first_name", "last_name", "patronymic", 
            "address", "phone", "birth_date"
        ]

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise forms.ValidationError("Регистрация только для пользователей старше 18 лет.")
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        cleaned_phone = re.sub(r'[^\d]', '', phone)

        if len(cleaned_phone) == 12 and cleaned_phone.startswith('375'):
            operator_code = cleaned_phone[3:5]
            if operator_code in ('29', '33', '44', '25'):
                return f"+375 {operator_code} {cleaned_phone[5:]}"

        elif len(cleaned_phone) == 9:
            operator_code = cleaned_phone[:2]
            if operator_code in ('29', '33', '44', '25'):
                return f"{operator_code} {cleaned_phone[2:]}"

        raise ValidationError(
            "Введите номер в формате: +375 29 1234567 или 29 1234567. "
            "Допустимые коды операторов: 29, 33, 44, 25."
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control form-control-lg',
                'autocomplete': 'off'
            })
        self.fields['birth_date'].widget.attrs.update({'type': 'date'})
        self.fields['patronymic'].required = False
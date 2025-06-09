from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        #fields = ['first_name','last_name', 'email', 'password', 'role']
        fields = ['first_name','last_name','middle_name', 'role', 'group_number', 'date_of_the_test']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванович'}),
            'role': forms.Select(attrs={'class': 'form-control', 'id': 'id_role'}),
            'group_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '121901'}),
            'date_of_the_test': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '26.12.2003'}),


        }
        labels = {
            'last_name': 'Фамилия',
            'first_name': 'Имя',
            'middle_name': 'Отчество',
            'role': 'Роль',
            'group_number': 'Номер группы',
            'date_of_the_test': 'Дата теста'
        }

class UserFormUpdate(UserForm):
    class Meta:
        model = User
        fields = ['last_name','first_name','middle_name', 'role', 'group_number','scores', 'date_of_the_test']

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иван'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов'}),
            'middle_name':forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Отчество'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'group_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '121901'}),
            'scores': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Оценка'}),
            'date_of_the_test': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '26.12.2003'}),
        }

        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name':'Отчество',
            'role': 'Роль',
            'group_number': 'Номер группы',
            'scores': 'Оценка',
            'date_of_the_test': 'Дата теста'
        }
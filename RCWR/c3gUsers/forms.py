from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(widget = forms.EmailInput(attrs={'class':'w-auto my-4 bg-transparent rounded-0 text-white fs-5', 'placeholder':'example@gmail.com'}))
    first_name = forms.CharField(max_length = 50, widget = forms.TextInput(attrs={'class':'w-auto my-4 bg-transparent rounded-0 text-white fs-5', 'placeholder':'First Name'}))
    last_name = forms.CharField(max_length = 50, widget = forms.TextInput(attrs={'class':'w-auto my-4 bg-transparent rounded-0 text-white fs-5', 'placeholder':'Last Name'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegisterUserForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'w-auto my-4 bg-transparent text-white fs-5'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['username'].widget.attrs['style'] = 'border: none; outline: none; background: none; border-bottom: 1px solid #867832; display: block; padding-Left: 27px;'
        
        self.fields['password1'].widget.attrs['class'] = 'w-auto my-4 bg-transparent rounded-0 text-white fs-5'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        
        self.fields['password2'].widget.attrs['class'] = 'w-auto my-4 bg-transparent rounded-0 text-white fs-5'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'
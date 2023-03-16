from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import RegisterUserForm
from django.contrib.auth.decorators import login_required
from c3gUsers.decorators import unauthenticated_user
from django.contrib.auth.models import Group
from customer.models import Customer


@unauthenticated_user
def signup_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username  = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            group = Group.objects.get(name='customer')
            user.groups.add(group)

            Customer.objects.create(
                user=user,
                name=user.first_name + ' ' + user.last_name,
                email=user.email,
            )

            return redirect('TermsConditions')
        
        else:
            messages.success(request, 'Sign up failed! Please check your username or password!')
    
    else:
        form = RegisterUserForm(request.POST)
    return render(request, 'authenticate/signup.html', {'form':form})


@unauthenticated_user
def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.info(request, 'Username OR password is incorrect. Please try again!')
            return redirect ('login')
    else:
        return render(request, 'authenticate/login.html', {})

def logout_user (request):
    logout(request)
    #message
    return redirect('login')

def terms(request):
    return render(request, 'authenticate/termsconditions.html')
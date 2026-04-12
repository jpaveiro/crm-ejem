from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Usuário ou senha inválidos.')
        except User.DoesNotExist:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'login.html')

def dashboard_view(request):

    return render(request, 'dashboard.html')
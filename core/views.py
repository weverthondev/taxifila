from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.user.is_authenticated:
        return redirect('fila')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('fila')
        else:
            return render(request, 'login.html', {'erro': 'Número do carro ou senha inválidos!'})
    return render(request, 'login.html')

def fila_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'fila.html')

def sair_view(request):
    logout(request)
    return redirect('login')
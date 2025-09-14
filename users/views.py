from django.shortcuts import render
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.urls import reverse
from users.forms import UserLoginForm

def login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserLoginForm()

    content = {
        'title': 'Авторизація - Binify',
        'form': form,
    }
    return render(request, 'users/login.html', content)

def registration(request):
    content = {
        'title': 'Реєстрація - Binify'
    }
    return render(request, 'users/registration.html', content)

def profile(request):
    content = {
        'title': 'Профіль - Binify'
    }
    return render(request, 'users/profile.html', content)

def logout(request):
    # content = {
    #     'title': 'Вихід - Binify'
    # }
    # return render(request, 'users/logout.html', content)
    
    pass

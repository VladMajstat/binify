from django.shortcuts import render
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.urls import reverse
from users.forms import UserLoginForm, UserRegistrationForm

def login(request):
    # Якщо запит POST — обробляємо дані форми
    if request.method == 'POST':
        # Створюємо форму з даними, які надіслав користувач
        form = UserLoginForm(data=request.POST)
        # Перевіряємо, чи форма валідна (логін і пароль коректні)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            # Аутентифікуємо користувача
            user = auth.authenticate(username=username, password=password)
            if user:
                # Якщо користувач знайдений — виконуємо вхід і редірект на головну
                auth.login(request, user)
                return HttpResponseRedirect(reverse('main:index'))
    else:
        # Якщо GET-запит — створюємо порожню форму
        form = UserLoginForm()

    # Передаємо форму у шаблон для відображення
    context = {
        'title': 'Авторизація - Binify',
        'form': form,
    }
    return render(request, 'users/login.html', context)

def registration(request):

    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = form.instance
            auth.login(request, user)
            return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserRegistrationForm()

    context = {
        'title': 'Реєстрація - Binify',
        'form':form,
    }
    return render(request, 'users/registration.html', context)

def profile(request):
    context = {
        'title': 'Профіль - Binify'
    }
    return render(request, 'users/profile.html', context)

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('main:index'))

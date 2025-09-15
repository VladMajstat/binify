from django.shortcuts import render
from django.contrib import auth, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from users.forms import UserLoginForm, UserRegistrationForm, ProfileForm
from django.contrib.auth.decorators import login_required

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
                messages.success(request, f"{username}, Ви успішно увійшли в систему.")
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
            messages.success(request, f"{user.username}, Ви успішно зареєструвалися й увійшли в аккаунт.")
            return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserRegistrationForm()

    context = {
        'title': 'Реєстрація - Binify',
        'form':form,
    }
    return render(request, 'users/registration.html', context)

@login_required
def profile(request):

    if request.method == 'POST':
        form = ProfileForm(data=request.POST, instance=request.user, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ви успішно оновили профіль.')
            return HttpResponseRedirect(reverse('user:profile'))
    else:
        form = ProfileForm(instance=request.user)

    context = {
        'title': 'Профіль - Binify',
        'form': form,
    }
    return render(request, 'users/profile.html', context)

@login_required
def logout(request):
    messages.success(request, f"{request.user.username}, Ви успішно вийшли з аккаунт.")
    auth.logout(request)
    return HttpResponseRedirect(reverse('main:index'))

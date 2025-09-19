from django.shortcuts import render
from django.contrib import auth, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from users.forms import UserLoginForm, UserRegistrationForm, ProfileForm
from bins.models import Create_Bins, BinLike
from bins.utils import create_bin_from_data

def login(request):
    next_url = request.GET.get('next') or request.POST.get('next')
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
                # --- Автоматичне створення Bin після логіну ---
                pending_bin_data = request.session.pop('pending_bin_data', None)
                if pending_bin_data:
                    success = create_bin_from_data(request, pending_bin_data)
                    if success:
                        messages.success(request, "Bin успішно створено!")
                    else:
                        messages.error(request, "❗ Не вдалося створити Bin після логіну.")
                    return HttpResponseRedirect(reverse('bins:index'))
                # --- Редірект на next, якщо є ---
                if next_url:
                    return HttpResponseRedirect(next_url)
                return HttpResponseRedirect(reverse('main:index'))
    else:
        # Якщо GET-запит — створюємо порожню форму
        form = UserLoginForm()

    # Передаємо форму у шаблон для відображення
    context = {
        'title': 'Авторизація - Binify',
        'form': form,
        'next': next_url,
    }
    return render(request, "users/login.html", context=context)

def registration(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = form.instance
            auth.login(request, user)
            messages.success(request, f"{user.username}, Ви успішно зареєструвалися й увійшли в аккаунт.")
            # --- Автоматичне створення Bin після реєстрації ---
            pending_bin_data = request.session.pop('pending_bin_data', None)
            if pending_bin_data:
                success = create_bin_from_data(request, pending_bin_data)
                if success:
                    messages.success(request, "Bin успішно створено!")
                else:
                    messages.error(request, "❗ Не вдалося створити Bin після реєстрації.")
                return HttpResponseRedirect(reverse('bins:index'))
            # --- Редірект на next, якщо є ---
            if next_url:
                return HttpResponseRedirect(next_url)
            return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserRegistrationForm()

    context = {
        'title': 'Реєстрація - Binify',
        'form':form,
        'next': next_url,
    }
    return render(request, "users/registration.html", context=context)

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
    
    # Отримуємо всі біни, які користувач лайкнув (в вигляді списка)
    liked_bin_ids = BinLike.objects.filter(user=request.user, is_like=True).values_list('bin_id', flat=True)
    liked_bins = Create_Bins.objects.filter(id__in=liked_bin_ids).order_by('-created_at')
    liked_bins = [bin for bin in liked_bins if bin.is_active()]

    context = {
        'title': 'Профіль - Binify',
        'form': form,
        'liked_bins': liked_bins,
    }
    return render(request, "users/profile.html", context=context)

@login_required
def logout(request):
    messages.success(request, f"{request.user.username}, Ви успішно вийшли з аккаунт.")
    auth.logout(request)
    return HttpResponseRedirect(reverse('main:index'))

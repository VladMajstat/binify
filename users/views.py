from django.shortcuts import render

def login(request):
    content = {
        'title': 'Авторизація - Binify'
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

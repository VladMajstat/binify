from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import auth, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required

from users.forms import UserLoginForm, UserRegistrationForm, ProfileForm
from bins.models import Create_Bins, BinLike
from bins.utils import create_bin_from_data


class LoginView(FormView):
    template_name = "users/login.html"
    form_class = UserLoginForm

    def get_success_url(self):
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        return reverse("main:index")

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = auth.authenticate(username=username, password=password)
        if user:
            auth.login(self.request, user)
            # --- Автоматичне створення Bin після логіну ---
            pending_bin_data = self.request.session.pop("pending_bin_data", None)
            if pending_bin_data:
                success = create_bin_from_data(self.request, pending_bin_data)
                if success:
                    messages.success(self.request, "Bin успішно створено!")
                else:
                    messages.error(
                        self.request, "❗ Не вдалося створити Bin після логіну."
                    )
                return HttpResponseRedirect(reverse("bins:index"))
            return HttpResponseRedirect(self.get_success_url())
        else:
            form.add_error(None, "Невірний логін або пароль")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Авторизація - Binify"
        context["next"] = self.request.GET.get("next") or self.request.POST.get("next")
        return context


class RegistrationView(FormView):
    template_name = "users/registration.html"
    form_class = UserRegistrationForm

    def get_success_url(self):
        return reverse("main:index")

    def form_valid(self, form):
        user = form.save()
        auth.login(self.request, user)
        # --- Автоматичне створення Bin після реєстрації ---
        pending_bin_data = self.request.session.pop("pending_bin_data", None)
        if pending_bin_data:
            success = create_bin_from_data(self.request, pending_bin_data)
            if success:
                messages.success(self.request, "Bin успішно створено!")
            else:
                messages.error(
                    self.request, "❗ Не вдалося створити Bin після реєстрації."
                )
            return HttpResponseRedirect(reverse("bins:index"))
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "❗ Дані форми некоректні. Перевірте введене!")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Реєстрація - Binify"
        return context


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "users/profile.html"
    form_class = ProfileForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Ви успішно оновили профіль.')
        return HttpResponseRedirect(reverse('user:profile'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Отримуємо всі біни, які користувач лайкнув (в вигляді списка)
        liked_bin_ids = BinLike.objects.filter(user=self.request.user, is_like=True).values_list('bin_id', flat=True)
        liked_bins = Create_Bins.objects.filter(id__in=liked_bin_ids).order_by('-created_at')
        liked_bins = [bin for bin in liked_bins if bin.is_active()]
        context.update({
            'title': 'Профіль - Binify',
            'liked_bins': liked_bins,
        })
        return context


@login_required
def logout(request):
    messages.success(request, f"{request.user.username}, Ви успішно вийшли з аккаунт.")
    auth.logout(request)
    return HttpResponseRedirect(reverse('main:index'))


class PasswordChangeView(LoginRequiredMixin, FormView):
    template_name = "users/password_change.html"
    form_class = PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
        return kwargs

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(
            self.request, user
        )  # Щоб не вийти з акаунта після зміни паролю
        messages.success(self.request, "Пароль успішно змінено!")
        return HttpResponseRedirect(reverse("user:profile"))

    def form_invalid(self, form):
        messages.error(self.request, "❗ Дані форми некоректні. Перевірте введене!")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Зміна паролю"
        return context

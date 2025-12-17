from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.template.loader import render_to_string
import json
from django.views.generic.edit import FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView

from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES, EXPIRY_CHOICES, ACCESS_CHOICES
from .models import Create_Bins, BinLike, BinComment
from .utils import (
    upload_to_r2,
    create_bin_from_data,
    delete_from_r2,
    get_bin_content,
    cache_bin_meta_and_content,
    invalidate_bin_cache,
    get_redis_client,
)
from .forms import CreateBinsForm, BinCommentForm, BinComment
from hash_generator.fake_class import FakeBin

class CreateBinView(FormView):
    template_name = "bins/create_bin.html"
    form_class = CreateBinsForm

    # Додаємо додаткові дані у контекст шаблону
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "title": "Створити Bin — Binify",
            "content": "Створити новий Bin",
            "category_choices": CATEGORY_CHOICES,
            "language_choices": LANGUAGE_CHOICES,
            "expiry_choices": EXPIRY_CHOICES,
            "access_choices": ACCESS_CHOICES,
        })
        return context

    # Обробка успішної форми
    def form_valid(self, form):
        request = self.request
        if not request.user.is_authenticated:
            # Якщо користувач не авторизований — зберігаємо дані у сесії і перенаправляємо на логін
            request.session['pending_bin_data'] = form.cleaned_data
            messages.info(request, "Для створення Bin потрібно увійти або зареєструватися.")
            return redirect("users:login")
        else:
            # Створюємо Bin через утиліту
            success = create_bin_from_data(request, form.cleaned_data)
            if success:
                messages.success(request, "Bin успішно створено!")
                return redirect("bins:index")
            else:
                messages.error(request, "❗ Не вдалося створити Bin. Спробуйте ще раз.")
                return self.render_to_response(self.get_context_data(form=form))

    # Обробка невалідної форми
    def form_invalid(self, form):
        messages.error(self.request, "❗ Дані форми некоректні. Перевірте введене!")
        return self.render_to_response(self.get_context_data(form=form))


class ViewBin(DetailView):
    model = Create_Bins
    template_name = "bins/view_bin.html"
    context_object_name = "bin"
    slug_field = "hash"
    slug_url_kwarg = "hash"

    def get_object(self, queryset=None):
        # Отримуємо об'єкт Bin за hash (slug)
        hash = self.kwargs.get(self.slug_url_kwarg)
        redis_cache = get_redis_client()
        meta_key = f"bin_meta:{hash}"
        meta = redis_cache.get(meta_key)
        if meta:
            meta = json.loads(meta)
            bin = FakeBin(meta, hash)
            real_bin = get_object_or_404(Create_Bins, hash=hash)
            bin.views_count = real_bin.views_count
            bin.likes = real_bin.likes_count
            bin.dislikes = real_bin.dislikes_count
            bin.author.image = getattr(real_bin.author, "image", None)
            self.comments = real_bin.comments.all().order_by("-created_at")
        else:
            bin = get_object_or_404(Create_Bins, hash=hash)
            self.comments = bin.comments.all().order_by("-created_at")
        self.bin_obj = bin
        return bin

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        bin = self.object
        # --- Підрахунок переглядів ---
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        already_viewed = bin.views.filter(session_key=session_key).exists()
        user = request.user if request.user.is_authenticated else None
        if user:
            already_viewed = bin.views.filter(user=user).exists() or already_viewed
        if not already_viewed:
            bin.views.create(
                user=user,
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                session_key=session_key,
            )
            bin.views_count = bin.views.count()
            bin.save(update_fields=["views_count"])

        # --- Кешування контенту ---
        redis_cache = get_redis_client()
        content_key = f"bin_content:{bin.hash}"
        bin_content = redis_cache.get(content_key)
        if bin_content:
            bin_content = bin_content.decode("utf-8")
        else:
            bin_content = get_bin_content(bin)
            if hasattr(bin, "views_count") and bin.views_count >= 50:
                cache_bin_meta_and_content(
                    bin, bin_content, ttl_meta=3600, ttl_content=3600
                )

        form = CreateBinsForm(instance=bin)

        context = self.get_context_data(
            bin=bin,
            form=form,
            bin_content=bin_content,
            comments=self.comments,
            views_count=bin.views_count if hasattr(bin, "views_count") else 0,
            category_choices=CATEGORY_CHOICES,
            language_choices=LANGUAGE_CHOICES,
            expiry_choices=EXPIRY_CHOICES,
            access_choices=ACCESS_CHOICES,
            title=f"Перегляд Bin — {bin.title}",
            content="Перегляд існуючого Bin",
        )
        return self.render_to_response(context)


class UserBinsView(ListView):
    template_name = "bins/user_bins.html"
    context_object_name = "bins"

    def get_queryset(self):
        # Всі біни поточного користувача, тільки активні
        return [bin for bin in Create_Bins.objects.filter(author=self.request.user).order_by('-created_at') if bin.is_active()]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Мої Bin"
        return context


class UserCommentsView(ListView):
    template_name = "bins/user_comments.html"
    context_object_name = "comments"

    def get_queryset(self):
        # Всі коментарі поточного користувача
        return BinComment.objects.filter(author=self.request.user).order_by(
            "-created_at"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Мої коментарі"
        return context


# Повертає кількість лайків/дизлайків для біна (GET) або додає лайк/дизлайк (POST).
class BinLikeDislikeView(View):

    def get(self, request, *args, **kwargs):
        bin_hash = kwargs.get("hash")
        bin_obj = get_object_or_404(Create_Bins, hash=bin_hash)
        return JsonResponse({
            "likes": bin_obj.likes_count,
            "dislikes": bin_obj.dislikes_count
        })

    def post(self, request, *args, **kwargs):
        bin_hash = kwargs.get("hash")
        bin_obj = get_object_or_404(Create_Bins, hash=bin_hash)
        action = request.POST.get("action")

        if not request.user.is_authenticated:
            return JsonResponse({"error": "Потрібна авторизація"}, status=403)

        # --- Логіка для одного лайка/дизлайка ---
        like_obj = BinLike.objects.filter(bin=bin_obj, user=request.user).first()
        if action == "like":
            if like_obj and like_obj.is_like:
                return JsonResponse(
                    {
                        "likes": bin_obj.likes_count,
                        "dislikes": bin_obj.dislikes_count,
                    })
            # Якщо був дизлайк — забираємо його
            if like_obj and not like_obj.is_like:
                bin_obj.dislikes_count -= 1
                like_obj.delete()
            BinLike.objects.create(bin=bin_obj, user=request.user, is_like=True)
            bin_obj.likes_count += 1
            bin_obj.save(update_fields=["likes_count", "dislikes_count"])
        elif action == "dislike":
            if like_obj and not like_obj.is_like:
                return JsonResponse(
                    {
                        "likes": bin_obj.likes_count,
                        "dislikes": bin_obj.dislikes_count,
                    })
            # Якщо був лайк — забираємо його
            if like_obj and like_obj.is_like:
                bin_obj.likes_count -= 1
                like_obj.delete()
            BinLike.objects.create(bin=bin_obj, user=request.user, is_like=False)
            bin_obj.dislikes_count += 1
            bin_obj.save(update_fields=["likes_count", "dislikes_count"])
        else:
            return JsonResponse({"error": "Невідома дія"}, status=400)

        return JsonResponse(
            {"likes": bin_obj.likes_count, "dislikes": bin_obj.dislikes_count}
        )


class BinCommentView(View):
    def post(self, request, *args, **kwargs):
        bin_hash = kwargs.get("hash")
        bin_obj = get_object_or_404(Create_Bins, hash=bin_hash)
        text = request.POST.get("text", "").strip()

        if not request.user.is_authenticated:
            return JsonResponse({"error": "Потрібна авторизація"}, status=403)

        if not text:
            return JsonResponse({"error": "Коментар не може бути порожнім"}, status=400)

        comment = BinComment.objects.create(bin=bin_obj, author=request.user, text=text)
        comment_html = render_to_string("bins/bin_comment.html", {"comment": comment}, request=request)
        return JsonResponse(
            {
                "success": True,
                "comment_html": comment_html,
            }
        )


class EditBinView(UpdateView):
    model = Create_Bins
    form_class = CreateBinsForm
    template_name = "bins/view_bin.html"
    slug_field = "hash"
    slug_url_kwarg = "hash"
    context_object_name = "bin"

    def get_object(self, queryset=None):
        # Дозволяємо редагувати тільки свої біни
        obj = get_object_or_404(Create_Bins, hash=self.kwargs.get(self.slug_url_kwarg), author=self.request.user)
        self.bin_content = get_bin_content(obj)
        return obj

    def get_initial(self):
        # Передаємо поточний контент у форму
        initial = super().get_initial()
        initial["content"] = self.bin_content
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "bin_content": self.bin_content,
            "category_choices": CATEGORY_CHOICES,
            "language_choices": LANGUAGE_CHOICES,
            "expiry_choices": EXPIRY_CHOICES,
            "access_choices": ACCESS_CHOICES,
        })
        return context

    def form_valid(self, form):
        bin = self.get_object()
        new_content = form.cleaned_data.get("content")
        old_content = self.bin_content

        # Оновлюємо контент у R2, якщо він змінився
        if new_content and new_content != old_content:
            upload_to_r2(bin.file_key, new_content)

        form.save()
        # Очищаємо старий кеш
        invalidate_bin_cache(bin.hash)
        # Оновлюємо кеш, якщо бін популярний
        bin.refresh_from_db()
        if bin.views_count >= 50:
            updated_content = get_bin_content(bin)
            cache_bin_meta_and_content(bin, updated_content, ttl_meta=3600, ttl_content=3600)

        messages.success(self.request, "Bin успішно оновлено!")
        return redirect("bins:view_bin", hash=bin.hash)

    def form_invalid(self, form):
        messages.error(self.request, "❗ Дані форми некоректні. Перевірте введене!")
        return self.render_to_response(self.get_context_data(form=form))


class DeleteBinView(View):
    def post(self, request, *args, **kwargs):
        bin_hash = kwargs.get("hash")
        bin_obj = get_object_or_404(Create_Bins, hash=bin_hash, author=request.user)

        # Видалення файлу з R2
        delete_from_r2(bin_obj.file_key)
        # Очищення кешу
        invalidate_bin_cache(bin_obj.hash)
        # Видалення з БД
        bin_obj.delete()

        messages.success(request, "Bin успішно видалено!")
        return redirect("bins:user_bins")

    # def get(self, request, *args, **kwargs):
    #     # Можна зробити редірект або показати сторінку підтвердження
    #     return redirect("bins:user_bins")

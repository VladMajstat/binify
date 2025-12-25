from django.views.generic import TemplateView, ListView

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from bins.models import Create_Bins
from bins.utils import smart_search

class MainView(ListView):
    model = Create_Bins
    template_name = "main/main.html"
    context_object_name = "bins_page"
    paginate_by = 5  # Кількість елементів на сторінку

    def get_queryset(self):
        query = self.request.GET.get("q", None)
        if query:
            return smart_search(query)
        # show only non-expired bins
        return Create_Bins.objects.filter(Q(expiry_at__isnull=True) | Q(expiry_at__gt=timezone.now())).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", None)
        context["title"] = "Binify — Головна"
        context["content"] = "Легко зберігай та ділись фрагментами коду або тексту."
        context["create_new_bin"] = "Створити новий Bin"
        context["last_bin"] = "Останні Bin"
        context["0_bins"] = "Немає жодного біна. Будь першим!"
        context["search_message"] = (
            f'Результати пошуку для: "{query}"' if query else None
        )
        context["query"] = query
        return context

# class MainView(ListView):
#     model = Create_Bins
#     template_name = "main/main.html"
#     context_object_name = "bins_page"
#     paginate_by = 4

#     def get_queryset(self):
#         query = self.request.GET.get("q", None)
#         if query:
#             return smart_search(query)
#         return Create_Bins.objects.all().order_by("-created_at")

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         query = self.request.GET.get("q", None)
#         context["title"] = "Binify — Головна"
#         context["content"] = "Легко зберігай та ділись фрагментами коду або тексту."
#         context["create_new_bin"] = "Створити новий Bin"
#         context["last_bin"] = "Останні Bin"
#         context["0_bins"] = "Немає жодного біна. Будь першим!"
#         context["search_message"] = (
#             f'Результати пошуку для: "{query}"' if query else None
#         )
#         context["query"] = query
#         return context


class AboutView(TemplateView):
    template_name = 'main/about.html'  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Про сайт'
        context["content"] = 'Даний сайт потрібен для створення, перегляду та редагування своїх "bin"-обєктів.'
        return context

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from .serializers import CreateBinsSerializer, BinListSerializer
from .services import (
    create_bin_service,
    update_bin_service,
    get_bin_service,
    delete_bin_service,
    ServiceError,
)
from .models import Create_Bins
from .utils import smart_search
from .choices import CATEGORY_CHOICES, LANGUAGE_CHOICES


class CreateBinAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateBinsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            bin_obj = create_bin_service(request.user, serializer.validated_data)
            # можна повертати деталі створеного біну або просто повідомлення
            return Response({"detail": "Bin created", "id": bin_obj.pk}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            # Повідомляємо про помилки валідації сервісного шару
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateBinAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        bin_obj = get_object_or_404(Create_Bins, pk=pk)
        # Перевіряємо права: лише автор може оновлювати
        if bin_obj.author != request.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateBinsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            bin_obj = update_bin_service(bin_obj, request.user, serializer.validated_data)
            return Response({"detail": "Bin updated", "id": bin_obj.pk}, status=status.HTTP_200_OK)
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetBinAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        bin_obj = get_object_or_404(Create_Bins, pk=pk)
        try:
            data = get_bin_service(bin_obj, request.user)
            return Response(data, status=status.HTTP_200_OK)
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteBinAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, pk):
        bin_obj = get_object_or_404(Create_Bins, pk=pk)
        try:
            delete_bin_service(bin_obj, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ServiceError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BinsPagination(PageNumberPagination):
    """Пагінація для списків бінів."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PublicBinsListAPIView(APIView):
    """Публічні біни з пагінацією та фільтрами."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        queryset = Create_Bins.objects.select_related('author').order_by('-created_at')
        
        # Фільтри з query params
        language = request.query_params.get('language')
        category = request.query_params.get('category')
        author = request.query_params.get('author')  # username

        allowed_languages = {choice[0] for choice in LANGUAGE_CHOICES}
        allowed_categories = {choice[0] for choice in CATEGORY_CHOICES}
        
        if language:
            if language not in allowed_languages:
                return Response({"detail": "Invalid language"}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(language=language)
        if category:
            if category not in allowed_categories:
                return Response({"detail": "Invalid category"}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(category=category)
        if author:
            queryset = queryset.filter(author__username=author)
        
        # Фільтр активних (не протухлі)
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        if active_only:
            queryset = queryset.filter(Q(expiry_at__isnull=True) | Q(expiry_at__gt=timezone.now()))

        # Публічні тільки (додатково страховка)
        queryset = queryset.filter(access='public')
        
        # Пагінація
        paginator = BinsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BinListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MyBinsListAPIView(APIView):
    """Біни поточного користувача (JWT)."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = Create_Bins.objects.filter(author=request.user).select_related('author').order_by('-created_at')
        
        # Опціонально: фільтр активних
        active_only = request.query_params.get('active', 'false').lower() == 'true'
        if active_only:
            queryset = queryset.filter(Q(expiry_at__isnull=True) | Q(expiry_at__gt=timezone.now()))
        
        paginator = BinsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BinListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SearchBinsAPIView(APIView):
    """Пошук бінів по назві та мові через fuzzy matching (smart_search)."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({"detail": "Query parameter 'q' is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Використовуємо smart_search з utils (fuzzy matching)
        queryset = smart_search(query)
        
        # Фільтр активних
        queryset = queryset.filter(Q(expiry_at__isnull=True) | Q(expiry_at__gt=timezone.now()))
        
        # Фільтр публічних (опціонально — smart_search шукає по всіх)
        queryset = queryset.filter(access='public')
        
        paginator = BinsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BinListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

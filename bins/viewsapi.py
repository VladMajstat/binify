from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from .serializers import CreateBinsSerializer
from .services import (
    create_bin_service,
    update_bin_service,
    get_bin_service,
    delete_bin_service,
    ServiceError,
)
from .models import Create_Bins


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

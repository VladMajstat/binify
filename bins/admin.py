from django.contrib import admin
from bins.models import Create_Bins
import boto3
from django.conf import settings
import uuid

admin.site.register(Create_Bins)

# class CreateBinsAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         # Якщо контент є і file_url порожній — зберігаємо у Cloudflare
#         if obj.content and not obj.file_url:
#             filename = f"bins/bin_{uuid.uuid4().hex}.txt"
#             s3 = boto3.client(
#                 "s3",
#                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#                 endpoint_url=settings.AWS_S3_ENDPOINT_URL,
#                 region_name=settings.AWS_S3_REGION_NAME,
#             )
#             s3.put_object(
#                 Bucket=settings.AWS_STORAGE_BUCKET_NAME,
#                 Key=filename,
#                 Body=obj.content,
#                 ContentType='text/plain'
#             )
#             obj.file_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{filename}"
#         super().save_model(request, obj, form, change)

# admin.site.register(Create_Bins, CreateBinsAdmin)

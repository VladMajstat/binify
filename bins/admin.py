from django.contrib import admin
from bins.models import Create_Bins
import uuid
from .utils import upload_to_r2

# admin.site.register(Create_Bins)

class CreateBinsAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # Якщо контент є і file_url порожній — зберігаємо у Cloudflare R2
        if obj.content and not obj.file_url:
            filename = f"bins/bin_{uuid.uuid4().hex}.txt"
            obj.file_url = upload_to_r2(filename, obj.content)
        super().save_model(request, obj, form, change)

admin.site.register(Create_Bins, CreateBinsAdmin)

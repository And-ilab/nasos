
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import admin_panel.views as admin_panel

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin_panel/', include('admin_panel.urls', namespace='admin_panel')),
    # path('api/filter_dialogs/', admin_panel.filter_dialogs, name='filter_dialogs'),
    # path('api/get_info/<int:user_id>/', admin_panel.get_info, name='get_info'),
    # path('api/export_to_excel/', admin_panel.export_to_excel, name='export_to_excel'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
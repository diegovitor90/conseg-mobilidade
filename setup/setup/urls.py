from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from django.views.generic import RedirectView

from reservas.views import CustomLoginView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="reservas:veiculo_lista", permanent=False)),
    path("admin/", admin.site.urls),
    path("contas/entrar/", CustomLoginView.as_view(), name="entrar"),
    path("contas/sair/", LogoutView.as_view(), name="sair"),
    path("", include("reservas.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

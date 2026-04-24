from django.urls import path

from .views import DashboardView, cambiar_tema

app_name = "dashboard"

urlpatterns = [
    path("", DashboardView.as_view(), name="inicio"),
    path("tema/<str:tema>/", cambiar_tema, name="cambiar_tema"),
]

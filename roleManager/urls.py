from django.urls import path
from . import views

app_name="RoleManager"
urlpatterns = [
    path("AllowRoleTeamRequest", views.setTeamAllowedRoleRequest, name="setTeamAllowedRoleRequest"),
    path("AllowRoleTeamRequest/<int:requestID>", views.showSetTeamAllowedRoleRequest, name="showSetTeamAllowedRoleRequest"),
    path("NewRoleRequest", views.newRoleRequest, name="newRoleRequest"),
    path("NewRoleRequest/<int:requestID>", views.showNewRoleRequest, name="showNewRoleRequest"),
]
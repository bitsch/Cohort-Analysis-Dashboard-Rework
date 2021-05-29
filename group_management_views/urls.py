from django.conf.urls import url

from group_management_views import views

urlpatterns = [
    # path('', views.create_group, name='create_group')
    url(r"^$", views.group_management, name="group_management"),
    url(
        r"^ajax/savegroupinfo/$",
        views.save_group_info,
        name="save_group_info",
    ),
    url(
        r"^ajax/changegroupstatus/$",
        views.change_group_status,
        name="change_group_status",
    ),
]

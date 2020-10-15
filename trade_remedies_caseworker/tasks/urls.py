from django.urls import path
from tasks.views import TaskView

urlpatterns = [
    path("", TaskView.as_view(), name="tasks"),
    path("<uuid:task_id>/", TaskView.as_view(), name="tasks"),
]

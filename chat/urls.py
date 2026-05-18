from django.urls import path
from .views import chat_view, advisors_list

urlpatterns = [
    path('<int:user_id>/', chat_view, name='chat'),
]
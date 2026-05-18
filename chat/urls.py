from django.urls import path
from .views import chat_view, advisors_list, chat_list

urlpatterns = [
    path('', chat_list, name='chat_list'),   
    path('advisors/', advisors_list, name='advisors'),
    path('<int:user_id>/', chat_view, name='chat'),
]
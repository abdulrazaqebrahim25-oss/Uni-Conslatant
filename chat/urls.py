from django.urls import path
from .views import (
    chat_view, advisors_list, chat_list, fetch_messages, 
    ai_chat_page, ai_chat_api
)

urlpatterns = [
    path('', chat_list, name='chat_list'),
    path('advisors/', advisors_list, name='advisors'),
    path('fetch/<int:user_id>/', fetch_messages, name='fetch_messages'),
    
    # AI Chat URLs
    path('ai/<int:user_id>/', ai_chat_page, name='ai_chat_page'),
    path('ai/api/<int:user_id>/', ai_chat_api, name='ai_chat_api'),
    
    path('<int:user_id>/', chat_view, name='chat'),
]
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.db.models import Q

from .models import Message

User = get_user_model()


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    if request.user.id == other_user.id:
        return HttpResponse("Cannot chat with yourself")

    if request.user.role == "admin" or other_user.role == "admin":
        return HttpResponse("Admins cannot use chat")

    valid_pair = (
        (request.user.role == "student" and other_user.role == "advisor") or
        (request.user.role == "advisor" and other_user.role == "student")
    )

    if not valid_pair:
        return HttpResponse("Chat allowed only between student and advisor")

    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by("created_at")

    if request.method == "POST":
        content = request.POST.get("content")

        if content and content.strip():
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content.strip()
            )
            return redirect("chat", user_id=other_user.id)

    return render(request, "chat/chat.html", {
        "other_user": other_user,
        "messages": messages
    })


@login_required
def advisors_list(request):
    advisors = User.objects.filter(role="advisor")
    return render(request, "chat/advisors_list.html", {
        "advisors": advisors
    })


@login_required
def chat_list(request):
    user = request.user

    messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).order_by('-created_at')

    chat_users = {}

    for msg in messages:
        other = msg.receiver if msg.sender == user else msg.sender

        if other.id not in chat_users:
            chat_users[other.id] = {
                "user": other,
                "last_message": msg.content,
                "time": msg.created_at
            }

    return render(request, "chat/chat_list.html", {
        "chats": chat_users.values()
    })


@login_required
def fetch_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by("created_at")

    data = [
        {
            "sender": msg.sender.username,
            "content": msg.content,
            "mine": msg.sender == request.user
        }
        for msg in messages
    ]

    return JsonResponse({"messages": data})
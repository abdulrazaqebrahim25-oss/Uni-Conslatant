from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by('created_at')

    if request.method == "POST":
        content = request.POST.get("content")

        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )

            return redirect('chat', user_id=other_user.id)

    context = {
        'other_user': other_user,
        'messages': messages
    }

    return render(request, 'chat/chat.html', context)


@login_required
def advisors_list(request):
    advisors = User.objects.filter(advisor_profile__isnull=False)

    return render(request, "chat/advisors_list.html", {
        "advisors": advisors
    })
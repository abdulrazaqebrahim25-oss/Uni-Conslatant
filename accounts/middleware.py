from django.contrib.auth import logout
from django.shortcuts import redirect


class BlockSuperuserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # السماح للسوبر أدمن داخل لوحة الأدمن فقط
        if request.path.startswith("/admin/"):
            return self.get_response(request)

        if (
            hasattr(request, "user")
            and request.user.is_authenticated
            and request.user.is_superuser
        ):

            logout(request)

            return redirect("login")

        response = self.get_response(request)

        return response
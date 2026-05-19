from django.shortcuts import redirect
from django.contrib import messages


class BlockSuperuserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):


        allowed_paths = [
            "/admin/",
        ]

        if (
            request.user.is_authenticated
            and request.user.is_superuser
        ):

            if not request.path.startswith(tuple(allowed_paths)):

                messages.error(
                    request,
                    "Superuser cannot access the main website."
                )

                return redirect("/admin/")

        response = self.get_response(request)
        return response
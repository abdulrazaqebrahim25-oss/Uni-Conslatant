from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login"
    ),

    path(
        "dashboard/",
        views.dashboard_view,
        name="dashboard"
    ),

    path(
        "profile/",
        views.student_profile_view,
        name="student_profile"
    ),

    path(
        "profile/edit/",
        views.edit_student_profile_view,
        name="edit_student_profile"
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout"
    ),

    path(
        "redirect-dashboard/",
        views.redirect_dashboard_view,
        name="redirect_dashboard"
    ),

    path(
        "advisor-dashboard/",
        views.advisor_dashboard_view,
        name="advisor_dashboard"
    ),

    path(
        "advisor-profile/",
        views.advisor_profile_view,
        name="advisor_profile"
    ),

    path(
        "advisor-profile/edit/",
        views.edit_advisor_profile_view,
        name="edit_advisor_profile"
    ),

    path(
        "advisor/students/",
        views.advisor_students_view,
        name="advisor_students"
    ),

    path(
        "advisor/students/<int:student_id>/",
        views.advisor_student_detail,
        name="advisor_student_detail"
    ),

]


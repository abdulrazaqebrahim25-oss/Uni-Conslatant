import json
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from main_app.models import MajorCourse, Course

from .forms import RegisterForm, StudentProfileForm, AdvisorProfileForm
from .models import StudentProfile, AdvisorProfile


# ─── SEMESTER UTILITY ─────────────────────────────────────────────────────────

SEMESTER_WINDOWS = {
    "spring": (1, 5, 31),
    "summer": (6, 8, 31),
    "fall": (9, 12, 31),
}

SEMESTER_ORDER = ["spring", "summer", "fall"]


def get_elapsed_semesters(entry_semester, entry_year, preferred_per_year=3):

    today = date.today()

    active = (
        ["spring", "fall"]
        if int(preferred_per_year) == 2
        else ["spring", "summer", "fall"]
    )

    elapsed = []

    started = False

    for year in range(entry_year, today.year + 1):

        for sem in SEMESTER_ORDER:

            if not started:

                if year == entry_year and sem == entry_semester:
                    started = True
                else:
                    continue

            if sem not in active:
                continue

            _, end_month, end_day = SEMESTER_WINDOWS[sem]

            end_date = date(year, end_month, end_day)

            if end_date < today:

                elapsed.append({
                    "semester": sem,
                    "label": sem.capitalize(),
                    "year": year,
                })

    return elapsed


def get_current_semester():

    month = date.today().month

    if 1 <= month <= 5:
        return "spring"

    elif 6 <= month <= 8:
        return "summer"

    return "fall"


# ─── REGISTRATION ─────────────────────────────────────────────────────────────

def register_view(request):

    major_courses_map = {}

    for mc in (
        MajorCourse.objects
        .select_related("major", "course")
        .prefetch_related("course__prerequisites")
    ):

        key = str(mc.major.id)

        if key not in major_courses_map:
            major_courses_map[key] = []

        major_courses_map[key].append({
            "id": mc.course.id,
            "code": mc.course.code,
            "name": mc.course.name,
            "credits": mc.course.credit,
            "type": mc.type,
        })

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("login")

    else:

        form = RegisterForm()

    return render(request, "registration/register.html", {
        "form": form,
        "major_courses_json": json.dumps(major_courses_map),
    })


# ─── STUDENT VIEWS ────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):

    student = request.user.student_profile

    elapsed = get_elapsed_semesters(
        student.entry_semester,
        student.entry_year,
        student.preferred_semesters_per_year,
    )

    return render(request, "dashboard/dashboard.html", {
        "student": student,
        "elapsed_semesters": elapsed,
        "elapsed_count": len(elapsed),
        "current_semester": get_current_semester().capitalize(),
    })


@login_required
def student_profile_view(request):

    student = request.user.student_profile

    completed = student.completed_courses.all().order_by("code")

    return render(request, "dashboard/profile.html", {
        "student": student,
        "completed_courses": completed,
    })


@login_required
def student_completed_courses_view(request):
    """
    Displays the student's completed courses
    and allows updating them safely.
    """

    student = request.user.student_profile

    # student's major courses
    major_courses = []

    if student.major:

        major_courses = (
            MajorCourse.objects
            .filter(major=student.major)
            .select_related("course")
            .prefetch_related("course__prerequisites")
            .order_by("type", "course__code")
        )

    completed_ids = set(
        student.completed_courses.values_list("id", flat=True)
    )

    # ─── UPDATE COMPLETED COURSES ───────────────────────────────────────────

    if request.method == "POST":

        selected_ids = request.POST.getlist("completed_courses")

        # allow only courses from student's major
        valid_ids = {
            str(mc.course.id)
            for mc in major_courses
        }

        safe_ids = {
            int(course_id)
            for course_id in selected_ids
            if course_id in valid_ids
        }

        # lookup table
        major_course_lookup = {
            mc.course.id: mc.course
            for mc in major_courses
        }

        valid_completed = set()

        remaining = set(safe_ids)

        changed = True

        while changed:

            changed = False

            for course_id in list(remaining):

                course = major_course_lookup.get(course_id)

                if not course:
                    continue

                prereq_ids = set(
                    course.prerequisites.values_list("id", flat=True)
                )

                # prerequisites must already exist
                if prereq_ids.issubset(valid_completed):

                    valid_completed.add(course_id)

                    remaining.remove(course_id)

                    changed = True

        # SAVE COURSES
        student.completed_courses.set(valid_completed)

        return redirect("student_completed_courses")

    # ─── COURSE DISPLAY DATA ────────────────────────────────────────────────

    course_data = []

    for mc in major_courses:

        course = mc.course

        prereqs = course.prerequisites.all()

        is_completed = course.id in completed_ids

        prereqs_met = all(
            p.id in completed_ids
            for p in prereqs
        )

        course_data.append({
            "course": course,
            "type": mc.type,
            "is_completed": is_completed,
            "prerequisites": prereqs,
            "prereqs_met": prereqs_met,
            "can_take": not is_completed and prereqs_met,
        })

    elapsed = get_elapsed_semesters(
        student.entry_semester,
        student.entry_year,
        student.preferred_semesters_per_year,
    )

    return render(request, "dashboard/completed_courses.html", {
        "student": student,
        "course_data": course_data,
        "completed_ids": completed_ids,
        "elapsed_semesters": elapsed,
        "elapsed_count": len(elapsed),
    })


@login_required
def edit_student_profile_view(request):

    student = request.user.student_profile

    if request.method == "POST":

        form = StudentProfileForm(
            request.POST,
            instance=student
        )

        if form.is_valid():

            form.save()

            return redirect("student_profile")

    else:

        form = StudentProfileForm(instance=student)

    return render(
        request,
        "dashboard/edit_student_profile.html",
        {
            "form": form
        }
    )


# ─── REDIRECT ─────────────────────────────────────────────────────────────────

@login_required
def redirect_dashboard_view(request):

    if request.user.role == "advisor":
        return redirect("advisor_dashboard")

    return redirect("dashboard")


# ─── ADVISOR VIEWS ────────────────────────────────────────────────────────────

@login_required
def advisor_dashboard_view(request):

    advisor = request.user.advisor_profile

    return render(
        request,
        "dashboard/advisor_dashboard.html",
        {
            "advisor": advisor
        }
    )


@login_required
def advisor_profile_view(request):

    advisor = request.user.advisor_profile

    return render(
        request,
        "dashboard/advisor_profile.html",
        {
            "advisor": advisor
        }
    )


@login_required
def edit_advisor_profile_view(request):

    advisor = request.user.advisor_profile

    if request.method == "POST":

        form = AdvisorProfileForm(
            request.POST,
            instance=advisor
        )

        if form.is_valid():

            form.save()

            return redirect("advisor_profile")

    else:

        form = AdvisorProfileForm(instance=advisor)

    return render(
        request,
        "dashboard/edit_advisor_profile.html",
        {
            "form": form
        }
    )


@login_required
def advisor_students_view(request):

    advisor = request.user.advisor_profile

    students = (
        StudentProfile.objects
        .filter(advisor=advisor)
        .select_related("user", "major")
    )

    return render(
        request,
        "dashboard/advisor_students.html",
        {
            "students": students
        }
    )


@login_required
def advisor_student_detail(request, student_id):

    advisor = request.user.advisor_profile

    student = get_object_or_404(
        StudentProfile,
        id=student_id,
        advisor=advisor
    )

    completed_ids = set(
        student.completed_courses.values_list("id", flat=True)
    )

    course_data = []

    if student.major:

        major_courses = (
            MajorCourse.objects
            .filter(major=student.major)
            .select_related("course")
            .prefetch_related("course__prerequisites")
            .order_by("type", "course__code")
        )

        for mc in major_courses:

            course = mc.course

            prereqs = course.prerequisites.all()

            is_completed = course.id in completed_ids

            prereqs_met = all(
                p.id in completed_ids
                for p in prereqs
            )

            course_data.append({
                "course": course,
                "type": mc.type,
                "is_completed": is_completed,
                "prerequisites": prereqs,
                "prereqs_met": prereqs_met,
                "can_take": not is_completed and prereqs_met,
            })

    elapsed = get_elapsed_semesters(
        student.entry_semester,
        student.entry_year,
        student.preferred_semesters_per_year,
    )

    return render(request, "dashboard/advisor_student_detail.html", {
        "student": student,
        "course_data": course_data,
        "completed_courses": student.completed_courses.order_by("code"),
        "completed_count": len(completed_ids),
        "total_count": len(course_data),
        "elapsed_semesters": elapsed,
        "elapsed_count": len(elapsed),
    })
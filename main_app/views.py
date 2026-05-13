from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

from .models import Student, Advisor, MajorCourse, StudentCourse
from .forms import StudentRegistrationForm, LoginForm


# ─── REGISTRATION ───

def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():

            # Check if email is already taken
            if Student.objects.filter(email=form.cleaned_data['email']).exists():
                form.add_error('email', 'An account with this email already exists.')
                return render(request, 'main_app/register.html', {'form': form})

            # Create the student, hashing the password before saving
            student = Student.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                password=make_password(form.cleaned_data['password']),
                major=form.cleaned_data['major']
            )

            # Save each completed course
            for course in form.cleaned_data['completed_courses']:
                StudentCourse.objects.create(student=student, course=course)

            messages.success(request, 'Account created! Please log in.')
            return redirect('login_student')
    else:
        form = StudentRegistrationForm()

    return render(request, 'main_app/register.html', {'form': form})


# ─── LOGIN / LOGOUT ───

def login_student(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                student = Student.objects.get(email=email)
                if check_password(password, student.password):
                    # Store the student's ID in the session (like a login token)
                    request.session['student_id'] = student.id
                    return redirect('student_dashboard')
                else:
                    form.add_error('password', 'Incorrect password.')
            except Student.DoesNotExist:
                form.add_error('email', 'No student account found with this email.')
    else:
        form = LoginForm()

    return render(request, 'main_app/login_student.html', {'form': form})


def login_advisor(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                advisor = Advisor.objects.get(email=email)
                if check_password(password, advisor.password):
                    request.session['advisor_id'] = advisor.id
                    return redirect('advisor_dashboard')
                else:
                    form.add_error('password', 'Incorrect password.')
            except Advisor.DoesNotExist:
                form.add_error('email', 'No advisor account found with this email.')
    else:
        form = LoginForm()

    return render(request, 'main_app/login_advisor.html', {'form': form})


def logout_view(request):
    request.session.flush()  # wipe the session completely
    return redirect('login_student')


# ─── STUDENT DASHBOARD ───

def student_dashboard(request):
    # If not logged in, send them back to login
    if 'student_id' not in request.session:
        return redirect('login_student')

    student = get_object_or_404(Student, id=request.session['student_id'])

    # All courses in this student's major
    major_courses = MajorCourse.objects.filter(
        major=student.major
    ).select_related('course')

    # IDs of courses the student has already completed
    completed_ids = set(
        StudentCourse.objects.filter(student=student).values_list('course_id', flat=True)
    )

    course_data = []
    for mc in major_courses:
        course = mc.course
        is_completed = course.id in completed_ids

        # Check if every prerequisite has been completed
        prereqs = course.prerequisites.all()
        prereqs_met = all(p.id in completed_ids for p in prereqs)

        course_data.append({
            'course': course,
            'type': mc.type,
            'is_completed': is_completed,
            'prerequisites': prereqs,
            'prereqs_met': prereqs_met,
            # Can take = not done yet AND all prerequisites finished
            'can_take': not is_completed and prereqs_met,
        })

    return render(request, 'main_app/student_dashboard.html', {
        'student': student,
        'course_data': course_data,
    })


# ─── ADVISOR VIEWS ─── 

def advisor_dashboard(request):
    if 'advisor_id' not in request.session:
        return redirect('login_advisor')

    advisor = get_object_or_404(Advisor, id=request.session['advisor_id'])
    students = Student.objects.all().select_related('major').order_by('name')

    return render(request, 'main_app/advisor_dashboard.html', {
        'advisor': advisor,
        'students': students,
    })


def student_detail(request, student_id):
    # Only advisors can access this view
    if 'advisor_id' not in request.session:
        return redirect('login_advisor')

    student = get_object_or_404(Student, id=student_id)
    major_courses = MajorCourse.objects.filter(
        major=student.major
    ).select_related('course')

    completed_ids = set(
        StudentCourse.objects.filter(student=student).values_list('course_id', flat=True)
    )

    course_data = []
    for mc in major_courses:
        course = mc.course
        is_completed = course.id in completed_ids
        prereqs = course.prerequisites.all()
        prereqs_met = all(p.id in completed_ids for p in prereqs)

        course_data.append({
            'course': course,
            'type': mc.type,
            'is_completed': is_completed,
            'prerequisites': prereqs,
            'prereqs_met': prereqs_met,
            'can_take': not is_completed and prereqs_met,
        })

    return render(request, 'main_app/student_detail.html', {
        'student': student,
        'course_data': course_data,
    })
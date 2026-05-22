from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Prefetch
from django.views.decorators.http import require_POST

from services.deepseek_service import deepseek_chat

from .models import Message
from main_app.models import MajorCourse, Course
from accounts.models import StudentProfile  # Import StudentProfile

import json
import re

User = get_user_model()


# =====================================================
# NORMAL CHAT
# =====================================================

@login_required
def chat_view(request, user_id):
    """Regular chat between student and advisor"""
    
    other_user = get_object_or_404(User, id=user_id)

    if request.user.id == other_user.id:
        return HttpResponse("Cannot chat with yourself")

    if request.user.role == "admin" or other_user.role == "admin":
        return HttpResponse("Admins cannot use chat")

    valid_pair = (
        (
            request.user.role == "student"
            and other_user.role == "advisor"
        )
        or
        (
            request.user.role == "advisor"
            and other_user.role == "student"
        )
    )

    if not valid_pair:
        return HttpResponse(
            "Chat allowed only between student and advisor"
        )

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

    return render(
        request,
        "chat/chat.html",
        {
            "other_user": other_user,
            "messages": messages
        }
    )


# =====================================================
# ADVISORS LIST
# =====================================================

@login_required
def advisors_list(request):
    """Show list of all advisors"""
    
    advisors = User.objects.filter(role="advisor")
    return render(
        request,
        "chat/advisors_list.html",
        {"advisors": advisors}
    )


# =====================================================
# CHAT LIST
# =====================================================

@login_required
def chat_list(request):
    """Show list of all user's chats"""
    
    user = request.user
    messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).order_by("-created_at")

    chat_users = {}
    for msg in messages:
        other = msg.receiver if msg.sender == user else msg.sender
        if other.id not in chat_users:
            chat_users[other.id] = {
                "user": other,
                "last_message": msg.content,
                "time": msg.created_at
            }

    return render(
        request,
        "chat/chat_list.html",
        {"chats": chat_users.values()}
    )


# =====================================================
# FETCH MESSAGES
# =====================================================

@login_required
def fetch_messages(request, user_id):
    """Fetch messages between current user and another user"""
    
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


# =====================================================
# HELPER FUNCTIONS FOR STUDENT PROFILE
# =====================================================

def get_student_profile(user):
    """Get student profile safely"""
    try:
        if user.role == 'student':
            return user.student_profile
    except:
        pass
    return None


def get_student_major(user):
    """Get student's major from profile"""
    profile = get_student_profile(user)
    if profile and profile.major:
        return profile.major
    return None


def get_completed_course_codes(user):
    """Get set of course codes that student has already completed"""
    
    completed_codes = set()
    profile = get_student_profile(user)
    
    if profile:
        # Get from completed_courses ManyToMany field
        completed_courses = profile.completed_courses.all()
        for course in completed_courses:
            completed_codes.add(course.code)
    
    return completed_codes


def calculate_semester_credits(courses):
    """Calculate total credits for a list of course codes"""
    
    total = 0
    for code in courses:
        try:
            course = Course.objects.get(code=code)
            total += course.credit
        except Course.DoesNotExist:
            pass
    return total


def validate_course_selection(user, requested_codes):
    """Validate a list of courses for prerequisites and duplicates"""
    
    errors = []
    completed_codes = get_completed_course_codes(user)
    already_selected = set()

    for code in requested_codes:
        # Check if course exists
        try:
            course = Course.objects.get(code=code)
        except Course.DoesNotExist:
            errors.append(f"{code}: course does not exist")
            continue

        # Check if already completed
        if code in completed_codes:
            errors.append(f"{code}: already completed")

        # Check for duplicates
        if code in already_selected:
            errors.append(f"{code}: duplicated in plan")
        already_selected.add(code)

        # Check prerequisites
        prereqs = course.prerequisites.all()
        missing = []
        for prereq in prereqs:
            if prereq.code not in completed_codes and prereq.code not in requested_codes:
                missing.append(prereq.code)

        if missing:
            errors.append(f"{code}: missing prerequisites ({', '.join(missing)})")

    return errors


def validate_semester_plan(user, semesters):
    """Validate complete semester plan for credit limits and prerequisites"""
    
    errors = []
    completed_codes = get_completed_course_codes(user)
    taken = set(completed_codes)
    MAX_CREDITS = 18

    for sem in semesters:
        semester_number = sem.get("semester")
        semester_courses = sem.get("courses", [])

        # Calculate credits
        semester_credits = calculate_semester_credits(semester_courses)
        sem["total_credits"] = semester_credits

        # Check credit limit
        if semester_credits > MAX_CREDITS:
            errors.append(
                f"Semester {semester_number}: exceeds maximum credits "
                f"({semester_credits}/{MAX_CREDITS})"
            )

        # Validate each course
        for code in semester_courses:
            try:
                course = Course.objects.get(code=code)
            except Course.DoesNotExist:
                errors.append(f"{code}: course does not exist")
                continue

            # Check if already completed
            if code in completed_codes:
                errors.append(f"{code}: already completed")

            # Check prerequisites
            prereqs = course.prerequisites.all()
            missing = []
            for prereq in prereqs:
                if prereq.code not in taken:
                    missing.append(prereq.code)

            if missing:
                errors.append(
                    f"Semester {semester_number} - {code}: missing prerequisites "
                    f"({', '.join(missing)})"
                )

        # Mark semester courses as taken for future prerequisites
        taken.update(semester_courses)

    return errors


def extract_course_codes(text):
    """Extract course codes from text using regex pattern"""
    
    pattern = r'\b[A-Z]{2,4}\d{3}\b'
    return re.findall(pattern, text.upper())


# =====================================================
# REPAIR ENGINE
# =====================================================

def find_course_semester(plan, course_code):
    """Find which semester contains the given course"""
    
    for sem in plan:
        if course_code in sem.get("courses", []):
            return sem
    return None


def get_or_create_semester(plan, semester_number):
    """Get existing semester or create new one"""
    
    for sem in plan:
        if sem.get("semester") == semester_number:
            return sem
    
    new_sem = {"semester": semester_number, "courses": []}
    plan.append(new_sem)
    plan.sort(key=lambda x: x["semester"])
    return new_sem


def remove_duplicate_courses(plan):
    """Remove duplicate courses from the plan"""
    
    seen = set()
    for sem in plan:
        cleaned = []
        for code in sem.get("courses", []):
            if code not in seen:
                cleaned.append(code)
                seen.add(code)
        sem["courses"] = cleaned
    return plan


def move_course_to_semester(plan, course_code, target_semester):
    """Move a course from its current semester to a target semester"""
    
    # Remove from current semester
    for sem in plan:
        if course_code in sem["courses"]:
            sem["courses"].remove(course_code)
    
    # Add to target semester
    target = get_or_create_semester(plan, target_semester)
    if course_code not in target["courses"]:
        target["courses"].append(course_code)
    
    return plan


def repair_semester_plan(user, semesters):
    """Repair a semester plan by fixing prerequisite ordering"""
    
    # Remove duplicates
    semesters = remove_duplicate_courses(semesters)
    completed = get_completed_course_codes(user)
    
    changed = True
    max_iterations = 20
    iteration = 0
    
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        semesters.sort(key=lambda x: x["semester"])
        
        for sem in semesters:
            current_semester = sem["semester"]
            courses = list(sem.get("courses", []))
            
            for code in courses:
                try:
                    course = Course.objects.get(code=code)
                except Course.DoesNotExist:
                    continue
                
                prereqs = course.prerequisites.all()
                for prereq in prereqs:
                    prereq_code = prereq.code
                    
                    # Skip if already completed
                    if prereq_code in completed:
                        continue
                    
                    prereq_sem = find_course_semester(semesters, prereq_code)
                    
                    # Missing prerequisite - add it
                    if prereq_sem is None:
                        target_semester = max(1, current_semester - 1)
                        target = get_or_create_semester(semesters, target_semester)
                        if prereq_code not in target["courses"]:
                            target["courses"].append(prereq_code)
                            changed = True
                    else:
                        prereq_semester = prereq_sem["semester"]
                        # Prerequisite is scheduled too late
                        if prereq_semester >= current_semester:
                            new_semester = max(1, current_semester - 1)
                            move_course_to_semester(semesters, prereq_code, new_semester)
                            changed = True
    
    # Remove empty semesters
    semesters = [sem for sem in semesters if sem.get("courses")]
    
    # Re-number semesters sequentially
    semesters.sort(key=lambda x: x["semester"])
    for index, sem in enumerate(semesters, start=1):
        sem["semester"] = index
    
    return semesters


# =====================================================
# HELPER FUNCTIONS FOR WELCOME MESSAGE
# =====================================================

def calculate_remaining_credits(user, major_courses):
    """Calculate remaining credits needed for graduation"""
    
    completed_codes = get_completed_course_codes(user)
    remaining = 0
    
    for mc in major_courses:
        if mc.course.code not in completed_codes:
            remaining += mc.course.credit
    
    return remaining


def get_current_study_plan(user):
    """Get or generate current study plan for the student"""
    
    completed_codes = get_completed_course_codes(user)
    
    # Get remaining courses for the major
    major = get_student_major(user)
    if not major:
        return {'semesters': [], 'validation_errors': ['No major assigned']}
    
    major_courses = MajorCourse.objects.filter(major=major).select_related('course')
    remaining_courses = [mc.course.code for mc in major_courses if mc.course.code not in completed_codes]
    
    # Simple distribution of remaining courses across semesters
    suggested_plan = []
    semester = 1
    courses_per_semester = max(3, len(remaining_courses) // 8) if remaining_courses else 3
    
    for i in range(0, len(remaining_courses), courses_per_semester):
        semester_courses = remaining_courses[i:i+courses_per_semester]
        if semester_courses:
            suggested_plan.append({
                'semester': semester,
                'courses': semester_courses
            })
            semester += 1
    
    # Validate the suggested plan
    validation_errors = []
    if suggested_plan:
        validation_errors = validate_semester_plan(user, suggested_plan)
    
    return {
        'semesters': suggested_plan,
        'validation_errors': validation_errors
    }


def get_welcome_message(user):
    """Generate a personalized welcome message for the student"""
    
    # Get student profile
    profile = get_student_profile(user)
    
    # Get completed courses
    completed_codes = get_completed_course_codes(user)
    
    # Get major
    major = get_student_major(user)
    
    # If no profile or major, show setup message
    if not profile:
        welcome_text = f"""Hello! I'm your AI academic planning assistant.

⚠️ **Student profile not found**

Please complete your student profile setup:
1. Go to your profile settings
2. Add your major
3. Add your completed courses

Once your profile is set up, I can help you create a study plan!

How can I help you today?"""
        
        return {
            'text': welcome_text,
            'plan': {'semesters': [], 'validation_errors': []},
            'stats': {
                'completed': 0,
                'total': 0,
                'progress': 0,
                'remaining_credits': 0
            }
        }
    
    if not major:
        welcome_text = f"""Hello! I'm your AI academic planning assistant.

📊 **Your Academic Overview:**
- Student: {user.get_full_name() or user.username}
- Major: Not assigned yet

⚠️ **No major assigned to your profile**

Please contact your advisor or update your profile to set your major.

How can I help you today?"""
        
        return {
            'text': welcome_text,
            'plan': {'semesters': [], 'validation_errors': []},
            'stats': {
                'completed': 0,
                'total': 0,
                'progress': 0,
                'remaining_credits': 0
            }
        }
    
    # Get major courses
    major_courses = MajorCourse.objects.filter(major=major).select_related('course')
    
    # Calculate progress
    total_courses = major_courses.count()
    completed_count = len([c for c in major_courses if c.course.code in completed_codes])
    
    if total_courses > 0:
        progress = (completed_count / total_courses) * 100
    else:
        progress = 0
    
    # Get remaining credits
    remaining_credits = calculate_remaining_credits(user, major_courses)
    
    # Get first course code for example
    first_course_code = major_courses[0].course.code if major_courses else "COURSE101"
    
    # Build welcome message
    welcome_text = f"""Hello! I'm your AI academic planning assistant.

📊 **Your Academic Overview:**
- Student: {user.get_full_name() or user.username}
- Major: {major.name}
- GPA: {profile.gpa if profile.gpa else 'Not set'}
- Completed Courses: {completed_count} out of {total_courses} ({progress:.1f}%)
- Remaining Credits: {remaining_credits} hours

💡 **What I can help you with:**
- Create a complete study plan
- Help you choose courses for each semester
- Check prerequisites for courses
- Optimize your current plan

📝 **Try asking me:**
- "Suggest a study plan"
- "What courses should I take next semester?"
- "Can I take {first_course_code}?"
- "Validate my course selection"

How can I help you today?"""
    
    # Get current plan
    initial_plan = get_current_study_plan(user)
    
    return {
        'text': welcome_text,
        'plan': initial_plan,
        'stats': {
            'completed': completed_count,
            'total': total_courses,
            'progress': round(progress, 1),
            'remaining_credits': remaining_credits
        }
    }


# =====================================================
# AI CHAT VIEWS
# =====================================================

@login_required
def ai_chat_page(request, user_id):
    """Display the AI chat page with welcome message"""
    
    other_user = get_object_or_404(User, id=user_id)
    
    # Authorization checks
    if request.user.role == 'advisor':
        # Check if advisor has this student
        try:
            advisor_profile = request.user.advisor_profile
            student_profile = other_user.student_profile
            if student_profile.advisor != advisor_profile:
                return HttpResponse("You are not authorized to chat with this student", status=403)
        except:
            return HttpResponse("You are not authorized to chat with this student", status=403)
    elif request.user.role == 'student':
        if other_user.id != request.user.id:
            return HttpResponse("You can only chat with yourself", status=403)
    else:
        return HttpResponse("Unauthorized", status=403)
    
    # Generate welcome message
    try:
        welcome_message = get_welcome_message(other_user)
    except Exception as e:
        print(f"Error generating welcome message: {e}")
        welcome_message = {
            'text': f"Hello! I'm your AI academic planning assistant. How can I help you today?",
            'plan': {'semesters': [], 'validation_errors': []},
            'stats': {
                'completed': 0,
                'total': 0,
                'progress': 0,
                'remaining_credits': 0
            }
        }
    
    return render(request, 'ai_chat/ai_chat.html', {
        'other_user': other_user,
        'welcome_message': welcome_message,
    })


@login_required
@require_POST
def ai_chat_api(request, user_id):
    """API endpoint for AI chat messages"""
    
    user = get_object_or_404(User, id=user_id)
    
    # Authorization
    if request.user != user and not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    # Parse request
    try:
        body = json.loads(request.body)
        user_message = body.get("message", "").strip()
        conversation = body.get("conversation", [])
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    if not user_message:
        return JsonResponse({"error": "Message is required"}, status=400)
    
    # Get major safely
    major = get_student_major(user)
    
    if not major:
        return JsonResponse({
            "error": "No major assigned. Please update your profile first."
        }, status=400)
    
    # Load major courses
    major_courses = (
        MajorCourse.objects
        .filter(major=major)
        .select_related("course")
        .prefetch_related(
            Prefetch(
                "course__prerequisites",
                queryset=Course.objects.only("id", "code", "credit")
            )
        )
    )
    
    course_lines = []
    for mc in major_courses:
        prereqs = list(mc.course.prerequisites.all())
        prereq_codes = ", ".join(p.code for p in prereqs) if prereqs else "None"
        course_lines.append(
            f"- {mc.course.code} "
            f"({mc.type}, "
            f"{mc.course.credit} credits, "
            f"Prerequisites: {prereq_codes})"
        )
    
    # Completed courses
    completed_codes = get_completed_course_codes(user)
    completed_text = ", ".join(list(completed_codes)[:20]) if completed_codes else "None"
    
    # System prompt
    system_message = {
        "role": "system",
        "content": """
You are a university academic planning assistant.

Rules:
- Only discuss academic study plans
- Respect prerequisites strictly
- Completed courses cannot be changed
- Never schedule courses before prerequisites
- Maximum 18 credits per semester
- Be concise and structured
- Always mention course codes clearly

IMPORTANT:
You must ALWAYS return valid JSON only.

Response format:

{
  "message": "Short explanation here",
  "semesters": [
    {
      "semester": 1,
      "courses": ["CS101", "MATH101"]
    }
  ]
}

Do not include markdown.
Do not include triple backticks.
Return JSON only.
"""
    }
    
    # Student context
    student_data_message = {
        "role": "system",
        "content": f"""
Major: {major.name}

Available Courses:
{chr(10).join(course_lines) if course_lines else 'No courses found'}

Completed Courses:
{completed_text}
"""
    }
    
    # Build AI messages
    messages = [system_message, student_data_message]
    messages.extend(conversation)
    messages.append({"role": "user", "content": user_message})
    
    # AI request
    try:
        result = deepseek_chat(messages)
        choices = result.get("choices")
        
        if not choices:
            raise Exception("No AI response received")
        
        ai_raw = choices[0]["message"]["content"].strip()
        
        # Parse AI JSON
        try:
            ai_data = json.loads(ai_raw)
        except json.JSONDecodeError:
            return JsonResponse({
                "error": "AI returned invalid JSON",
                "raw": ai_raw
            }, status=500)
        
        semesters = ai_data.get("semesters", [])
        if not isinstance(semesters, list):
            return JsonResponse({
                "error": "Invalid semester structure"
            }, status=500)
        
        # Repair plan
        repaired_semesters = repair_semester_plan(user, semesters)
        ai_data["semesters"] = repaired_semesters
        
        # Validate repaired plan
        validation_errors = validate_semester_plan(user, repaired_semesters)
        ai_data["validation_errors"] = validation_errors
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
    # Final response
    return JsonResponse({
        "user_message": {
            "role": "user",
            "content": user_message
        },
        "ai_message": {
            "role": "assistant",
            "content": ai_data.get("message", "")
        },
        "plan": ai_data
    })
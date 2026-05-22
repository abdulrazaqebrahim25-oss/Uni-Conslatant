from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Prefetch
from django.views.decorators.http import require_POST

from services.deepseek_service import deepseek_chat

from .models import Message
from main_app.models import MajorCourse, Course
from accounts.models import StudentProfile

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
        try:
            course = Course.objects.get(code=code)
        except Course.DoesNotExist:
            errors.append(f"{code}: course does not exist")
            continue

        if code in completed_codes:
            errors.append(f"{code}: already completed")

        if code in already_selected:
            errors.append(f"{code}: duplicated in plan")
        already_selected.add(code)

        prereqs = course.prerequisites.all()
        missing = []
        for prereq in prereqs:
            if prereq.code not in completed_codes and prereq.code not in requested_codes:
                missing.append(prereq.code)

        if missing:
            errors.append(f"{code}: missing prerequisites ({', '.join(missing)})")

    return errors


def validate_semester_plan(user, semesters):
    """Validate semester plan including credit limits per semester type and prerequisites."""
    
    errors = []
    completed_codes = get_completed_course_codes(user)
    taken = set(completed_codes)
    
    # Credit limits per semester type
    limits = {
        'fall': {'min': 12, 'max': 18},
        'spring': {'min': 12, 'max': 18},
        'summer': {'min': 0, 'max': 9}
    }
    
    for sem in semesters:
        semester_number = sem.get("semester")
        semester_type = sem.get("semester_type", 'fall')
        semester_courses = sem.get("courses", [])
        
        # Calculate credits
        semester_credits = calculate_semester_credits(semester_courses)
        sem["total_credits"] = semester_credits
        
        # Check credit limits
        if semester_credits < limits[semester_type]['min']:
            errors.append(
                f"Semester {semester_number} ({semester_type}): below minimum credits "
                f"({semester_credits}/{limits[semester_type]['min']})"
            )
        if semester_credits > limits[semester_type]['max']:
            errors.append(
                f"Semester {semester_number} ({semester_type}): exceeds maximum credits "
                f"({semester_credits}/{limits[semester_type]['max']})"
            )
        
        # Validate each course
        for code in semester_courses:
            try:
                course = Course.objects.get(code=code)
            except Course.DoesNotExist:
                errors.append(f"{code}: course does not exist")
                continue
            
            if code in completed_codes:
                errors.append(f"{code}: already completed")
            
            # Prerequisites
            prereqs = course.prerequisites.all()
            missing = [p.code for p in prereqs if p.code not in taken]
            if missing:
                errors.append(
                    f"Semester {semester_number} - {code}: missing prerequisites "
                    f"({', '.join(missing)})"
                )
        
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


def get_or_create_semester(plan, semester_number, semester_type='fall'):
    """Get existing semester or create new one with type"""
    
    for sem in plan:
        if sem.get("semester") == semester_number:
            return sem
    
    new_sem = {"semester": semester_number, "semester_type": semester_type, "courses": []}
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
    
    for sem in plan:
        if course_code in sem["courses"]:
            sem["courses"].remove(course_code)
    
    target = get_or_create_semester(plan, target_semester, 'fall')
    if course_code not in target["courses"]:
        target["courses"].append(course_code)
    
    return plan


def enforce_credit_limits(plan):
    """Adjust courses between semesters to respect min/max credits per type."""
    limits = {'fall': {'min': 12, 'max': 18}, 'spring': {'min': 12, 'max': 18}, 'summer': {'min': 0, 'max': 9}}
    plan.sort(key=lambda x: x["semester"])
    
    for i, sem in enumerate(plan):
        sem_type = sem.get("semester_type", 'fall')
        total_credits = calculate_semester_credits(sem["courses"])
        if total_credits < limits[sem_type]['min']:
            # Borrow from next semester
            if i+1 < len(plan):
                next_sem = plan[i+1]
                for code in next_sem["courses"][:]:
                    try:
                        course_credit = Course.objects.get(code=code).credit
                    except Course.DoesNotExist:
                        continue
                    if total_credits + course_credit <= limits[sem_type]['max']:
                        sem["courses"].append(code)
                        next_sem["courses"].remove(code)
                        total_credits += course_credit
                        if total_credits >= limits[sem_type]['min']:
                            break
        elif total_credits > limits[sem_type]['max']:
            # Move excess to next semester (or create new)
            excess = total_credits - limits[sem_type]['max']
            moved = 0
            for code in reversed(sem["courses"][:]):
                try:
                    course_credit = Course.objects.get(code=code).credit
                except Course.DoesNotExist:
                    continue
                if moved + course_credit <= excess:
                    sem["courses"].remove(code)
                    if i+1 < len(plan):
                        plan[i+1]["courses"].insert(0, code)
                    else:
                        plan.append({"semester": sem["semester"]+1, "semester_type": 'fall', "courses": [code]})
                    moved += course_credit
                    if moved >= excess:
                        break
    
    # Re-number semesters
    for idx, sem in enumerate(plan, 1):
        sem["semester"] = idx
    # Remove empty semesters
    plan = [sem for sem in plan if sem.get("courses")]
    return plan


def repair_semester_plan(user, semesters):
    """Repair semester plan: prerequisites + credit limits."""
    # Remove duplicates
    semesters = remove_duplicate_courses(semesters)
    completed = get_completed_course_codes(user)
    
    # Prerequisite repair
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
                for prereq in course.prerequisites.all():
                    prereq_code = prereq.code
                    if prereq_code in completed:
                        continue
                    prereq_sem = find_course_semester(semesters, prereq_code)
                    if prereq_sem is None:
                        target_semester = max(1, current_semester - 1)
                        target = get_or_create_semester(semesters, target_semester, 'fall')
                        if prereq_code not in target["courses"]:
                            target["courses"].append(prereq_code)
                            changed = True
                    else:
                        prereq_semester = prereq_sem["semester"]
                        if prereq_semester >= current_semester:
                            new_semester = max(1, current_semester - 1)
                            move_course_to_semester(semesters, prereq_code, new_semester)
                            changed = True
    
    # Remove empty semesters
    semesters = [sem for sem in semesters if sem.get("courses")]
    # Re-number semesters
    semesters.sort(key=lambda x: x["semester"])
    for index, sem in enumerate(semesters, start=1):
        sem["semester"] = index
    
    # Enforce credit limits
    semesters = enforce_credit_limits(semesters)
    return semesters


# =====================================================
# ENRICH PLAN WITH COURSE NAMES AND CREDITS
# =====================================================

def enrich_plan_with_course_details(semesters):
    """Convert semester.courses from list of course codes to list of objects with code, name, credit."""
    enriched = []
    for sem in semesters:
        new_courses = []
        for code in sem.get("courses", []):
            try:
                course = Course.objects.get(code=code)
                new_courses.append({
                    "code": course.code,
                    "name": course.name,
                    "credit": course.credit
                })
            except Course.DoesNotExist:
                new_courses.append({
                    "code": code,
                    "name": "Unknown Course",
                    "credit": 0
                })
        enriched.append({
            "semester": sem["semester"],
            "semester_type": sem.get("semester_type", "fall"),
            "courses": new_courses,
            "total_credits": sem.get("total_credits", 0)
        })
    return enriched


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
    """Generate a study plan respecting min/max credits, including summer semesters."""
    
    completed_codes = get_completed_course_codes(user)
    
    major = get_student_major(user)
    if not major:
        return {'semesters': [], 'validation_errors': ['No major assigned']}
    
    major_courses = MajorCourse.objects.filter(major=major).select_related('course')
    remaining = []
    for mc in major_courses:
        if mc.course.code not in completed_codes:
            remaining.append({'code': mc.course.code, 'credit': mc.course.credit})
    
    if not remaining:
        return {'semesters': [], 'validation_errors': []}
    
    # Semester cycle: (type, min_credits, max_credits)
    semester_cycle = [('fall', 12, 18), ('spring', 12, 18), ('summer', 0, 9)]
    suggested_plan = []
    semester_number = 1
    idx = 0
    total = len(remaining)
    
    while idx < total:
        for sem_type, min_cred, max_cred in semester_cycle:
            if idx >= total:
                break
            semester_courses = []
            semester_credits = 0
            # Fill up to max credits
            while idx < total and semester_credits + remaining[idx]['credit'] <= max_cred:
                semester_courses.append(remaining[idx]['code'])
                semester_credits += remaining[idx]['credit']
                idx += 1
            # If below min and more courses exist, try to add more
            temp_idx = idx
            while semester_credits < min_cred and temp_idx < total:
                if semester_credits + remaining[temp_idx]['credit'] <= max_cred:
                    semester_courses.append(remaining[temp_idx]['code'])
                    semester_credits += remaining[temp_idx]['credit']
                    temp_idx += 1
                else:
                    break
            if temp_idx > idx:
                idx = temp_idx
            if semester_courses:
                suggested_plan.append({
                    'semester': semester_number,
                    'semester_type': sem_type,
                    'courses': semester_courses,
                    'total_credits': semester_credits
                })
                semester_number += 1
    
    # Validate
    simple_plan = [{'semester': p['semester'], 'semester_type': p['semester_type'], 'courses': p['courses']} for p in suggested_plan]
    validation_errors = validate_semester_plan(user, simple_plan) if simple_plan else []
    
    # Enrich with course names/credits
    enriched_plan = enrich_plan_with_course_details(simple_plan)
    
    return {
        'semesters': enriched_plan,
        'validation_errors': validation_errors
    }


def get_welcome_message(user):
    """Generate a personalized welcome message for the student"""
    
    profile = get_student_profile(user)
    completed_codes = get_completed_course_codes(user)
    major = get_student_major(user)
    
    if not profile:
        welcome_text = """Hello! I'm your AI academic planning assistant.

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
    
    major_courses = MajorCourse.objects.filter(major=major).select_related('course')
    total_courses = major_courses.count()
    completed_count = len([c for c in major_courses if c.course.code in completed_codes])
    progress = (completed_count / total_courses) * 100 if total_courses > 0 else 0
    remaining_credits = calculate_remaining_credits(user, major_courses)
    first_course_code = major_courses[0].course.code if major_courses else "COURSE101"
    
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
    
    if request.user.role == 'advisor':
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
    
    try:
        welcome_message = get_welcome_message(other_user)
    except Exception as e:
        print(f"Error generating welcome message: {e}")
        welcome_message = {
            'text': "Hello! I'm your AI academic planning assistant. How can I help you today?",
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
    
    if request.user != user and not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    try:
        body = json.loads(request.body)
        user_message = body.get("message", "").strip()
        conversation = body.get("conversation", [])
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    if not user_message:
        return JsonResponse({"error": "Message is required"}, status=400)
    
    major = get_student_major(user)
    if not major:
        return JsonResponse({"error": "No major assigned. Please update your profile first."}, status=400)
    
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
    
    completed_codes = get_completed_course_codes(user)
    completed_text = ", ".join(list(completed_codes)[:20]) if completed_codes else "None"
    
    system_message = {
        "role": "system",
        "content": """
You are a university academic planning assistant.

Rules:
- Only discuss academic study plans
- Respect prerequisites strictly
- Completed courses cannot be changed
- Never schedule courses before prerequisites
- Maximum credits: Fall/Spring 18, Summer 9
- Minimum credits: Fall/Spring 12, Summer 0
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
      "semester_type": "fall",
      "courses": ["CS101", "MATH101"]
    }
  ]
}

Valid semester_type: "fall", "spring", "summer". 
Do not include markdown. Return JSON only.
"""
    }
    
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
    
    messages = [system_message, student_data_message]
    messages.extend(conversation)
    messages.append({"role": "user", "content": user_message})
    
    try:
        result = deepseek_chat(messages)
        choices = result.get("choices")
        
        if not choices:
            raise Exception("No AI response received")
        
        ai_raw = choices[0]["message"]["content"].strip()
        
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
        
        # Ensure each semester has semester_type
        for sem in semesters:
            if "semester_type" not in sem:
                sem["semester_type"] = "fall"
        
        # Repair plan (prerequisites + credit limits)
        repaired_semesters = repair_semester_plan(user, semesters)
        
        # Prepare for validation and enrichment
        simple_plan = [{
            "semester": s["semester"],
            "semester_type": s.get("semester_type", "fall"),
            "courses": s["courses"]
        } for s in repaired_semesters]
        
        validation_errors = validate_semester_plan(user, simple_plan)
        enriched_plan = enrich_plan_with_course_details(simple_plan)
        final_plan = {"semesters": enriched_plan, "validation_errors": validation_errors}
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({
        "user_message": {
            "role": "user",
            "content": user_message
        },
        "ai_message": {
            "role": "assistant",
            "content": ai_data.get("message", "")
        },
        "plan": final_plan
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail

from .models import Student, Result
from .forms import StudentForm, ResultFormSet

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

import random
from django.contrib.auth.models import User

from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, Sum, Count
from django.db.models import Q
from .models import Student, Result, Notice
from .models import Student, Result, Notice, Complaint

from django.http import HttpResponse
from reportlab.pdfgen import canvas

from django.template.loader import render_to_string


def login_page(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(email=email)

            user = authenticate(
                request,
                username=user_obj.username,
                password=password
            )

        except User.DoesNotExist:
            user = None

        if user is not None:

            login(request, user)

            return redirect('home')

        return render(request, 'login.html', {
            'error': 'Invalid email or password'
        })

    return render(request, 'login.html')

def logout_user(request):

    logout(request)

    return redirect('login')

@login_required(login_url='login')
def home(request):

    query = request.GET.get('q')

    students = Student.objects.all()

    if query:

        students = students.filter(

            Q(usn__icontains=query) |
            Q(name__icontains=query) |
            Q(branch__icontains=query) |
            Q(semester__icontains=query)

        )

    total_students = Student.objects.count()

    total_backlogs = Result.objects.filter(
        result='BACKLOG'
    ).count()

    topper = Student.objects.annotate(
        total_marks=Sum('result__total_marks')
    ).order_by('-total_marks').first()

    topper_name = topper.name if topper else 'N/A'

    topper_percentage = 0

    if topper:

        topper_results = Result.objects.filter(
            student=topper
        )

        topper_total = sum(
            i.total_marks for i in topper_results
        )

        topper_subjects = topper_results.count()

        topper_max = topper_subjects * 100

        topper_percentage = (
            (topper_total / topper_max) * 100
            if topper_max > 0
            else 0
        )

    total_cgpa = 0

    student_count = Student.objects.count()

    placement_count = 0

    for student in Student.objects.all():

        results = Result.objects.filter(
            student=student
        )

        total = sum(
            i.total_marks for i in results
        )

        subjects = results.count()

        max_marks = subjects * 100

        percentage = (
            (total / max_marks) * 100
            if max_marks > 0
            else 0
        )

        cgpa = percentage / 10

        total_cgpa += cgpa

        backlog_count = results.filter(
            result='BACKLOG'
        ).count()

        if cgpa >= 6.5 and backlog_count == 0:

            placement_count += 1

    average_cgpa = (
        round(total_cgpa / student_count, 2)
        if student_count > 0
        else 0
    )

    branch_analytics = Student.objects.values(
        'branch'
    ).annotate(
        count=Count('id')
    )

    return render(request, 'home.html', {

        'students': students,
        'query': query,

        'total_students': total_students,
        'total_backlogs': total_backlogs,

        'topper_name': topper_name,

        'topper_percentage': round(
            topper_percentage,
            2
        ),

        'average_cgpa': average_cgpa,

        'placement_count': placement_count,

        'branch_analytics': branch_analytics

    })

@login_required(login_url='login')
def add_student(request):

    if not request.user.is_staff:
        return redirect('home')

    form = StudentForm()

    if request.method == 'POST':

        form = StudentForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('home')

    return render(request, 'add_student.html', {
        'form': form
    })


@login_required(login_url='login')
def update_student(request, id):

    if not request.user.is_staff:
        return redirect('home')

    student = get_object_or_404(Student, id=id)

    form = StudentForm(instance=student)

    if request.method == 'POST':

        form = StudentForm(
            request.POST,
            instance=student
        )

        if form.is_valid():
            form.save()
            return redirect('home')

    return render(request, 'add_student.html', {
        'form': form
    })


@login_required(login_url='login')
def delete_student(request, id):

    if not request.user.is_staff:
        return redirect('home')

    student = get_object_or_404(Student, id=id)

    student.delete()

    return redirect('home')

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@login_required(login_url='login')
def update_marks(request, id):

    if not request.user.is_staff:
        return redirect('home')

    student = get_object_or_404(Student, id=id)

    queryset = Result.objects.filter(
        student=student
    ).order_by(
        'semester',
        'subject_code'
    )

    formset = ResultFormSet(queryset=queryset)

    if request.method == 'POST':

        formset = ResultFormSet(
            request.POST,
            queryset=queryset
        )

        if formset.is_valid():

            forms = formset.save(commit=False)

            for form in formset.forms:

                if form.cleaned_data.get('DELETE'):

                    if form.instance.id:
                        form.instance.delete()

            for result in forms:

                if result.subject_code and result.subject_name:

                    result.student = student
                    result.save()

            # EMAIL SEND

            try:

                results = Result.objects.filter(student=student)

                total_marks = sum(
                    result.total_marks or 0
                    for result in results
                )

                max_marks = results.count() * 100

                percentage = 0

                if max_marks > 0:
                    percentage = (total_marks / max_marks) * 100

                cgpa = round((percentage / 9.5), 2)

                context = {

                    'student': student,
                    'total_marks': total_marks,
                    'max_marks': max_marks,
                    'percentage': round(percentage, 2),
                    'cgpa': cgpa,
                    'status': 'PASS'

                }

                html_content = render_to_string(
                    'result_email.html',
                    context
                )

                email = EmailMultiAlternatives(

                    'VTU Result Updated',

                    'Your VTU Result has been updated.',

                    'shreyashs182@gmail.com',

                    [student.email]

                )

                email.attach_alternative(
                    html_content,
                    "text/html"
                )

                email.send()

            except Exception as e:

                print("Mail Error:", e)

            return redirect(
                'student_result',
                id=student.id
            )

    return render(request, 'update_marks.html', {

        'student': student,
        'formset': formset

    })
@login_required(login_url='login')
def student_result(request, id):

    student = get_object_or_404(Student, id=id)

    old_results = Result.objects.filter(student=student)

    for r in old_results:
        r.save()

    results = Result.objects.filter(
        student=student
    ).order_by(
        'semester',
        'subject_code'
    )

    semester_data = {}

    for sem in range(1, 9):

        sem_results = results.filter(
            semester=sem
        )

        if sem_results.exists():

            sem_total = sum(
                i.total_marks
                for i in sem_results
            )

            sem_subjects = sem_results.count()

            sem_max_marks = sem_subjects * 100

            sem_percentage = (
                (sem_total / sem_max_marks) * 100
                if sem_max_marks > 0
                else 0
            )

            sem_sgpa = sem_percentage / 10

            semester_data[sem] = {
                'results': sem_results,
                'total': sem_total,
                'subjects': sem_subjects,
                'max_marks': sem_max_marks,
                'percentage': round(sem_percentage, 2),
                'sgpa': round(sem_sgpa, 2)
            }

    total = sum(i.total_marks for i in results)

    subjects = results.count()

    max_marks = subjects * 100

    percentage = (
        (total / max_marks) * 100
        if max_marks > 0
        else 0
    )

    cgpa = percentage / 10

    backlog = results.filter(result='BACKLOG')

    backlog_count = backlog.count()

    pass_count = results.filter(result='PASS').count()

    pass_percentage = (
        (pass_count / subjects) * 100
        if subjects > 0
        else 0
    )

    fail_percentage = (
        (backlog_count / subjects) * 100
        if subjects > 0
        else 0
    )

    weak_subjects = results.order_by('total_marks')[:3]

    placement_eligible = (
        cgpa >= 6.5 and
        backlog_count == 0
    )

    scholarship_eligible = (
        percentage >= 85 and
        backlog_count == 0
    )

    if percentage >= 90 and backlog_count == 0:
        achievement_badge = "🏆 Outstanding Performer"

    elif percentage >= 75 and backlog_count == 0:
        achievement_badge = "⭐ Distinction Performer"

    elif backlog_count == 0:
        achievement_badge = "✅ Pass Performer"

    else:
        achievement_badge = "⚠️ Improvement Required"

    if backlog_count > 0:
        backlog_alert = "You have backlog subjects."

    else:
        backlog_alert = "No backlogs. Good academic standing."

    if weak_subjects:

        weakest = weak_subjects[0]

        if weakest.total_marks < 40:

            study_recommendation = (
                "Focus more on " +
                weakest.subject_name +
                ". This subject needs urgent improvement."
            )

        elif weakest.total_marks < 60:

            study_recommendation = (
                "Improve " +
                weakest.subject_name +
                " with extra practice and revision."
            )

        else:
            study_recommendation = "Performance is good."

    else:
        study_recommendation = "No subject data available."

    status = (
        'PASS'
        if backlog_count == 0
        else 'BACKLOG'
    )

    sms_message = (
        f"Hello {student.name}, "
        f"your VTU result is updated. "
        f"CGPA: {round(cgpa, 2)}, "
        f"Status: {status}."
    )

    return render(request, 'student_result.html', {
        'student': student,
        'semester_data': semester_data,
        'total': total,
        'subjects': subjects,
        'max_marks': max_marks,
        'percentage': round(percentage, 2),
        'cgpa': round(cgpa, 2),
        'backlog': backlog,
        'backlog_count': backlog_count,
        'weak_subjects': weak_subjects,
        'placement_eligible': placement_eligible,
        'scholarship_eligible': scholarship_eligible,
        'achievement_badge': achievement_badge,
        'backlog_alert': backlog_alert,
        'pass_count': pass_count,
        'pass_percentage': round(pass_percentage, 2),
        'fail_percentage': round(fail_percentage, 2),
        'study_recommendation': study_recommendation,
        'sms_message': sms_message
    })


@login_required(login_url='login')
def backlog_results(request):

    results = Result.objects.filter(
        result='BACKLOG'
    ).order_by(
        'student__usn'
    )

    return render(request, 'backlog.html', {
        'results': results
    })


@login_required(login_url='login')
def rank_list(request):

    selected_semester = request.GET.get('semester', '').strip()

    selected_branch = request.GET.get('branch', '').strip()

    subject_code = request.GET.get('subject_code', '').strip().upper()

    rank_data = []

    subject_rank_data = []

    if selected_semester:

        students = Student.objects.filter(
            semester=int(selected_semester)
        )

        if selected_branch:

            students = students.filter(
                branch__iexact=selected_branch
            )

        for student in students:

            results = Result.objects.filter(
                student=student
            )

            total = sum(i.total_marks for i in results)

            subjects = results.count()

            max_marks = subjects * 100

            percentage = (
                (total / max_marks) * 100
                if max_marks > 0
                else 0
            )

            cgpa = percentage / 10

            backlog_count = results.filter(
                result='BACKLOG'
            ).count()

            rank_data.append({
                'student': student,
                'total': total,
                'subjects': subjects,
                'max_marks': max_marks,
                'percentage': round(percentage, 2),
                'cgpa': round(cgpa, 2),
                'backlog_count': backlog_count
            })

        rank_data = sorted(
            rank_data,
            key=lambda x: x['percentage'],
            reverse=True
        )

    if selected_semester and subject_code:

        subject_results = Result.objects.filter(
            semester=int(selected_semester),
            subject_code__iexact=subject_code
        )

        if selected_branch:

            subject_results = subject_results.filter(
                student__branch__iexact=selected_branch
            )

        subject_results = subject_results.order_by(
            '-total_marks'
        )

        for result in subject_results:

            subject_rank_data.append({
                'student': result.student,
                'subject_code': result.subject_code,
                'subject_name': result.subject_name,
                'marks': result.total_marks,
                'grade': result.grade,
                'result': result.result
            })

    return render(request, 'rank_list.html', {
        'rank_data': rank_data,
        'subject_rank_data': subject_rank_data,
        'selected_semester': selected_semester,
        'selected_branch': selected_branch,
        'subject_code': subject_code
    })



@login_required(login_url='login')
def admin_dashboard(request):

    query = request.GET.get('q', '').strip()
    selected_college = request.GET.get('college', '').strip()

    if request.method == 'POST' and request.user.is_staff:

        title = request.POST.get('notice_title')
        message = request.POST.get('notice_message')

        if title and message:
            Notice.objects.create(
                title=title,
                message=message
            )

        return redirect('home')

    students = Student.objects.all()

    if selected_college:
        students = students.filter(
            college__iexact=selected_college
        )

    if query:
        students = students.filter(
            Q(usn__icontains=query) |
            Q(name__icontains=query) |
            Q(branch__icontains=query) |
            Q(semester__icontains=query) |
            Q(college__icontains=query) |
            Q(degree__icontains=query) |
            Q(scheme__icontains=query)
        )

    student_list = []

    for student in students:

        results = Result.objects.filter(student=student)

        total = sum(i.total_marks for i in results)
        subjects = results.count()
        max_marks = subjects * 100

        percentage = (
            (total / max_marks) * 100
            if max_marks > 0
            else 0
        )

        student.percentage = round(percentage, 2)

        student_list.append(student)

    student_list = sorted(
        student_list,
        key=lambda x: x.percentage,
        reverse=True
    )

    rank = 1

    for student in student_list:
        student.rank = rank
        rank += 1

    all_students = Student.objects.all()
    all_results = Result.objects.all()

    total_students = all_students.count()
    total_backlogs = all_results.filter(result='BACKLOG').count()

    topper_name = "No Data"
    topper_percentage = 0
    average_cgpa = 0
    placement_count = 0
    percentages = []

    for student in all_students:

        results = Result.objects.filter(student=student)

        total = sum(i.total_marks for i in results)
        subjects = results.count()
        max_marks = subjects * 100

        percentage = (
            (total / max_marks) * 100
            if max_marks > 0
            else 0
        )

        cgpa = percentage / 10
        backlog_count = results.filter(result='BACKLOG').count()

        if subjects > 0:
            percentages.append(percentage)

        if percentage > topper_percentage:
            topper_percentage = percentage
            topper_name = student.name

        if cgpa >= 6.5 and backlog_count == 0:
            placement_count += 1

    if percentages:
        average_cgpa = sum(percentages) / len(percentages) / 10

    branch_analytics = []

    branches = [
        'CSE',
        'ISE',
        'ECE',
        'EEE',
        'MECHANICAL',
        'CIVIL',
        'AIML',
        'DS'
    ]

    for branch in branches:
        count = Student.objects.filter(
            branch__iexact=branch
        ).count()

        branch_analytics.append({
            'branch': branch,
            'count': count
        })

    colleges = [
        'JVIT',
        'ACS',
        'RR',
        'BMSCE',
        'RVCE',
        'MSRIT',
        'PES University'
    ]

    notices = Notice.objects.all().order_by('-date')

    return render(request, 'home.html', {
        'students': student_list,
        'query': query,
        'selected_college': selected_college,
        'colleges': colleges,
        'total_students': total_students,
        'total_backlogs': total_backlogs,
        'topper_name': topper_name,
        'topper_percentage': round(topper_percentage, 2),
        'average_cgpa': round(average_cgpa, 2),
        'placement_count': placement_count,
        'branch_analytics': branch_analytics,
        'notices': notices,
         'complaint_count': Complaint.objects.filter(
         is_read=False)
         .count()
    })


@login_required(login_url='login')
def student_dashboard(request):

    try:
        student = Student.objects.get(
            email=request.user.email
        )

        return redirect(
            'student_result',
            id=student.id
        )

    except Student.DoesNotExist:

        return render(request, 'student_dashboard.html', {
            'message': 'No student result found for your email.'
        })
    
    import random

otp_store = {}

otp_store = {}


def forgot_password(request):

    message = ''
    error = ''

    if request.method == 'POST':

        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            otp = random.randint(100000, 999999)

            otp_store[email] = otp

            request.session['reset_email'] = email

            send_mail(
                'VTU Portal Password Reset OTP',
                f'Your OTP is {otp}',
                'VTU Result Portal <shreyashs182@gmail.com>',
                [email],
                fail_silently=False
            )

            return redirect('verify_otp')

        except User.DoesNotExist:
            error = 'Email not found'

    return render(request, 'forgot_password.html', {
        'message': message,
        'error': error
    })

def verify_otp(request):

    error = ''

    email = request.session.get('reset_email')

    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':

        entered_otp = request.POST.get('otp')

        if str(otp_store.get(email)) == str(entered_otp):

            request.session['otp_verified'] = True

            return redirect('reset_password')

        else:
            error = 'Invalid OTP'

    return render(request, 'verify_otp.html', {
        'error': error
    })


def reset_password(request):

    error = ''
    message = ''

    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified')

    if not email or not otp_verified:
        return redirect('forgot_password')

    if request.method == 'POST':

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:

            error = 'Passwords do not match'

        else:

            user = User.objects.get(email=email)

            user.set_password(password1)

            user.save()

            otp_store.pop(email, None)

            request.session.pop('reset_email', None)
            request.session.pop('otp_verified', None)

            message = 'Password changed successfully'

            return redirect('login')

    return render(request, 'reset_password.html', {
        'error': error,
        'message': message
    })

@login_required(login_url='login')
def delete_notice(request, id):

    if not request.user.is_staff:
        return redirect('home')

    notice = get_object_or_404(Notice, id=id)

    notice.delete()

    return redirect('home')


@login_required(login_url='login')
def edit_notice(request, id):

    if not request.user.is_staff:
        return redirect('home')

    notice = get_object_or_404(Notice, id=id)

    if request.method == 'POST':

        notice.title = request.POST.get('notice_title')
        notice.message = request.POST.get('notice_message')
        notice.save()

        return redirect('home')

    return render(request, 'edit_notice.html', {
        'notice': notice
    })

@login_required(login_url='login')
def complaint_page(request):

    message = ''

    if request.user.is_staff:

        Complaint.objects.filter(
            is_read=False
        ).update(
            is_read=True
        )

        complaints = Complaint.objects.all().order_by(
            '-date'
        )

        return render(request, 'admin_complaint.html', {
            'complaints': complaints
        })

    if request.method == 'POST':

        subject = request.POST.get('subject')
        complaint_message = request.POST.get('message')

        student = Student.objects.filter(
            email=request.user.email
        ).first()

        Complaint.objects.create(
            student=student,
            subject=subject,
            message=complaint_message,
            is_read=False
        )

        message = 'Complaint submitted successfully.'

    return render(request, 'complaint.html', {
        'message': message
    })

def register_page(request):

    error = ''

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        usn = request.POST.get('usn', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        college = request.POST.get('college', '').strip()
        branch = request.POST.get('branch', '').strip()
        semester = request.POST.get('semester', '').strip()
        password = request.POST.get('password', '').strip()

        if (
            not name or
            not usn or
            not email or
            not phone or
            not college or
            not branch or
            not semester or
            not password
        ):

            error = 'All fields are required'

        elif User.objects.filter(email=email).exists():

            error = 'Email already registered'

        elif Student.objects.filter(email=email).exists():

            error = 'Student email already exists'

        elif Student.objects.filter(usn=usn).exists():

            error = 'USN already registered'

        elif len(password) < 6:

            error = 'Password must be at least 6 characters'

        else:

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )

            user.is_staff = False
            user.is_superuser = False
            user.save()

            Student.objects.create(
                usn=usn,
                name=name,
                email=email,
                phone=phone,
                college=college,
                branch=branch,
                semester=int(semester)
            )

            return redirect('login')

    return render(request, 'register.html', {
        'error': error
    })

@login_required(login_url='login')
def registered_users(request):

    if not request.user.is_staff:
        return redirect('home')

    selected_semester = request.GET.get(
        'semester',
        ''
    ).strip()

    selected_branch = request.GET.get(
        'branch',
        ''
    ).strip()

    students = Student.objects.all().order_by(
        '-id'
    )

    if selected_semester:

        students = students.filter(
            semester=selected_semester
        )

    if selected_branch:

        students = students.filter(
            branch__iexact=selected_branch
        )

    return render(
        request,
        'registered_users.html',
        {

            'students': students,

            'selected_semester': selected_semester,

            'selected_branch': selected_branch

        }
    )

@login_required(login_url='login')
def profile_page(request):

    student = Student.objects.filter(
        email=request.user.email
    ).first()

    if not student:
        return render(request, 'profile.html', {
            'student': None
        })

    results = Result.objects.filter(student=student)

    total = sum(i.total_marks for i in results)
    subjects = results.count()
    max_marks = subjects * 100

    percentage = (
        (total / max_marks) * 100
        if max_marks > 0
        else 0
    )

    cgpa = percentage / 10

    backlog_count = results.filter(
        result='BACKLOG'
    ).count()

    status = (
        'PASS'
        if backlog_count == 0
        else 'BACKLOG'
    )

    return render(request, 'profile.html', {
        'student': student,
        'total': total,
        'max_marks': max_marks,
        'percentage': round(percentage, 2),
        'cgpa': round(cgpa, 2),
        'backlog_count': backlog_count,
        'status': status
    })

@login_required(login_url='login')
def download_marks_pdf(request, id):

    student = get_object_or_404(Student, id=id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{student.usn}_marks_card.pdf"'

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 800, "VTU Result Portal")

    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Name: {student.name}")
    p.drawString(50, 740, f"USN: {student.usn}")
    p.drawString(50, 720, f"College: {student.college}")
    p.drawString(50, 700, f"Branch: {student.branch}")
    p.drawString(50, 680, f"Semester: {student.semester}")

    y = 640

    results = Result.objects.filter(student=student).order_by('semester', 'subject_code')

    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Sem")
    p.drawString(80, y, "Code")
    p.drawString(160, y, "Subject")
    p.drawString(340, y, "Internal")
    p.drawString(410, y, "External")
    p.drawString(480, y, "Total")
    p.drawString(530, y, "Grade")

    y -= 20
    p.setFont("Helvetica", 10)

    total = 0

    for r in results:
        total += r.total_marks

        p.drawString(40, y, str(r.semester))
        p.drawString(80, y, r.subject_code)
        p.drawString(160, y, r.subject_name[:25])
        p.drawString(340, y, str(r.internal_marks))
        p.drawString(410, y, str(r.external_marks))
        p.drawString(480, y, str(r.total_marks))
        p.drawString(530, y, r.grade)

        y -= 20

        if y < 80:
            p.showPage()
            y = 760

    subjects = results.count()
    max_marks = subjects * 100
    percentage = (total / max_marks) * 100 if max_marks > 0 else 0
    cgpa = percentage / 10

    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, f"Total Marks: {total} / {max_marks}")
    p.drawString(50, y - 20, f"Percentage: {round(percentage, 2)}%")
    p.drawString(50, y - 40, f"CGPA: {round(cgpa, 2)}")

    p.save()

    return response

@login_required(login_url='login')
def semester_marks_card(request, id, sem):

    student = get_object_or_404(Student, id=id)

    results = Result.objects.filter(
        student=student,
        semester=sem
    ).order_by('subject_code')

    total = sum(i.total_marks for i in results)
    subjects = results.count()
    max_marks = subjects * 100

    percentage = (
        (total / max_marks) * 100
        if max_marks > 0
        else 0
    )

    sgpa = percentage / 10

    backlogs = Result.objects.filter(
        student=student,
        result='BACKLOG'
    ).order_by('semester', 'subject_code')

    return render(request, 'semester_marks_card.html', {
        'student': student,
        'sem': sem,
        'results': results,
        'total': total,
        'subjects': subjects,
        'max_marks': max_marks,
        'percentage': round(percentage, 2),
        'sgpa': round(sgpa, 2),
        'backlogs': backlogs
    })
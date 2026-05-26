from django.contrib import admin

from .models import Student, Result, Notice
from .models import Student, Result, Notice, Complaint


class StudentAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'usn',
        'name',
        'college',
        'degree',
        'branch',
        'scheme',
        'semester'
    ]

    search_fields = [
        'usn',
        'name',
        'college'
    ]

    list_filter = [
        'college',
        'degree',
        'branch',
        'scheme',
        'semester'
    ]


class ResultAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'student',
        'subject_code',
        'subject_name',
        'total_marks',
        'result'
    ]

    search_fields = [
        'student__usn',
        'subject_code',
        'subject_name'
    ]

    list_filter = [
        'result'
    ]


class NoticeAdmin(admin.ModelAdmin):

    list_display = [
        'id',
        'title',
        'date'
    ]

    search_fields = [
        'title',
        'message'
    ]


admin.site.register(Student, StudentAdmin)

admin.site.register(Result, ResultAdmin)

admin.site.register(Notice, NoticeAdmin)

admin.site.register(Complaint)
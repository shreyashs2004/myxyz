from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_user, name='logout'),

    path('', views.admin_dashboard, name='home'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),

    path('add-student/', views.add_student, name='add_student'),
    path('update-student/<int:id>/', views.update_student, name='update_student'),
    path('delete-student/<int:id>/', views.delete_student, name='delete_student'),
    path('update-marks/<int:id>/', views.update_marks, name='update_marks'),
    path('student-result/<int:id>/', views.student_result, name='student_result'),
    path('backlog/', views.backlog_results, name='backlog'),
    path('rank-list/', views.rank_list, name='rank_list'),
    path('complaints/', views.complaint_page, name='complaints'),

    path('edit-notice/<int:id>/', views.edit_notice, name='edit_notice'),
    path('delete-notice/<int:id>/', views.delete_notice, name='delete_notice'),

    path('register/', views.register_page, name='register'),
    path('registered-users/', views.registered_users, name='registered_users'),
    path('profile/', views.profile_page, name='profile'),
   path('marks-card/<int:id>/<int:sem>/',views.semester_marks_card,name='semester_marks_card'),
]
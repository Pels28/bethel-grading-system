from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("students/" , views.students, name="students"),
    path("results/", views.results, name="results"),
    path("students/<slug:slug>", views.add_student, name="add-student"),
    path("results/<slug:slug>", views.class_results, name="class-results"),
    path("results/<slug:slug>/add", views.add_result, name="add-results"),
    path("results/<slug:slug>/view", views.view_results, name="view-results"),
    path("students/<slug:slug>/view-report/<int:id>/", views.view_report, name="view-report"),
    path('api/get-scores/', views.get_scores, name='get-scores'),
    path('api/get-subjects/', views.get_subjects, name='get-subjects'),
    path('submit-grades/', views.submit_grades, name='submit-grades'),
    path("students/<slug:slug>/export-csv/", views.export_students_csv, name="export-students-csv"),
    path("students/<slug:slug>/import-csv/", views.import_students_csv, name="import-students-csv"),
    path("students/<slug:slug>/add-result/<int:id>", views.enter_indv_student_result, name="enter-indv-student-result"),
    path('students/<slug:slug>/print-all-reports/', views.print_all_reports, name="print-all-reports"),
   path('export-grades/<slug:slug>/', views.export_grades_csv, name="export-grades-csv"),
    path('import-grades/<slug:slug>/', views.import_grades_csv, name="import-grades-csv"),
  path("add-subject/", views.add_subject, name="add_subject"),
]

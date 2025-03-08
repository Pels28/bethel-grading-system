from django.contrib import admin

from .models import  Exams, ClassName,Student, Subject, Results, MidTermExams
# Register your models here.


    
class ExamsAdmin(admin.ModelAdmin):
    list_filter = ("student_name", "semester", "class_name")
    list_display = ("student_name", "class_to_30", "exames_to_70", "class_name", "semester", "total_score", "subject_name", "academic_year")
    
    def get_queryset(self, request):
        """Order results by total_marks in descending order"""
        queryset = super().get_queryset(request)
        return queryset.order_by('-total_score')
    
class ClassAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    
class StudentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "class_name", "gender")
    list_filter = ("first_name", "last_name", "class_name",)
    
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("subject_name", "teacher_name")

class ResultsAdmin(admin.ModelAdmin):
    list_filter = ("student_name", "class_name")
    list_display = ("student_name", "class_name", "position", "total_marks", "academic_year")
    
    def get_queryset(self, request):
        """Order results by total_marks in descending order"""
        queryset = super().get_queryset(request)
        return queryset.order_by('-total_marks')
    
class MidTermExamsAdmin(admin.ModelAdmin):
    list_display = ("student", "scores", "class_name", "subject", "semester", "academic_year")

admin.site.register(Exams, ExamsAdmin)
admin.site.register(ClassName, ClassAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Results, ResultsAdmin)
admin.site.register(MidTermExams, MidTermExamsAdmin)


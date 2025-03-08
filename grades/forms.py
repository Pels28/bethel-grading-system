from django import forms
from .models import Student, ClassName

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'gender']
        
class ClassNameForm(forms.ModelForm):
    class Meta:
        model = ClassName
        fields = ['name', 'teacher']

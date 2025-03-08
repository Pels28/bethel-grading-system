from django.db import models
from django.utils.text import slugify
from django.core.validators import RegexValidator

# Create your models here.
class ClassName(models.Model):
    name = models.CharField(max_length=50)
    teacher = models.CharField(max_length=50)
    slug = models.SlugField(null=True, editable=False, db_index=True)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Class Names"
    
class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    

        
class Subject(models.Model):
    subject_name = models.CharField(max_length=20)
    teacher_name = models.CharField(max_length=50)
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, null=True)
    
    def __str__(self):
        return self.subject_name
        
        
class Exams(models.Model):
    student_name = models.ForeignKey(Student, on_delete=models.CASCADE, null=True)
    class_score = models.DecimalField(max_digits=5, decimal_places=2) 
    class_to_30 = models.DecimalField(max_digits=5, decimal_places=2,editable= False, null=True)
    exams_score = models.DecimalField(max_digits=5, decimal_places=2)
    exames_to_70 = models.DecimalField(max_digits=5, decimal_places=2, editable=False, null=True)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, editable=False, null= True)
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, null=True)
    subject_name = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True)
    semester = models.IntegerField()
    academic_year = models.CharField(
        null=True,
        max_length=5,
        validators=[
            RegexValidator(
                regex=r'^\d{2}/\d{2}$',  # Matches the format YY/YY
                message="Academic year must be in the format 'YY/YY' (e.g., '24/25')."
            )
        ],
        help_text="Format: YY/YY (e.g., 24/25)"
    )
    
    def save(self, *args, **kwargs):
        self.class_to_30 = (self.class_score /100) * 30
        self.exames_to_70 = (self.exams_score / 100) * 70
        self.total_score = self.class_to_30 + self.exames_to_70
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name_plural = "Exams"
        
    def __str__(self):
        return f"{self.student_name} {self.class_to_30} {self.exames_to_70} {self.total_score} {self.class_name} {self.subject_name}"
        
class Results(models.Model):
    student_name = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE)
    semester = models.IntegerField()
    total_marks = models.DecimalField(max_digits=5 , decimal_places=2)
    position=  models.CharField(max_length=5)
    academic_year = models.CharField(
        null=True,
        max_length=5,
        validators=[
            RegexValidator(
                regex=r'^\d{2}/\d{2}$',  # Matches the format YY/YY
                message="Academic year must be in the format 'YY/YY' (e.g., '24/25')."
            )
        ],
        help_text="Format: YY/YY (e.g., 24/25)"
    )
    
    class Meta:
        verbose_name_plural = "Results"
        
class MidTermExams(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    scores = models.DecimalField(max_digits=4, decimal_places=2)
    semester = models.IntegerField()
    academic_year = models.CharField(
        null=True,
        max_length=5,
        validators=[
            RegexValidator(
                regex=r'^\d{2}/\d{2}$',  # Matches the format YY/YY
                message="Academic year must be in the format 'YY/YY' (e.g., '24/25')."
            )
        ],
        help_text="Format: YY/YY (e.g., 24/25)"
    )
    
    def __str__(self):
        return f"{self.student}, {self.subject}, {self.scores}, {self.semester}, {self.academic_year}"
    
    class Meta:
        verbose_name_plural = "MidTermExams"
    
    
    
    
    
    
    
    
    
    
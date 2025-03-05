from django.shortcuts import render, redirect, get_object_or_404
from .models import ClassName, Results, Student, Exams, Subject, MidTermExams
from django.db.models import Sum
from .forms import StudentForm
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import csv
import json
from django.urls import reverse

from django.contrib import messages

from datetime import datetime
from .utils import calculate_student_position

def update_student_positions(class_name, semester, academic_year):
    # Fetch all students' results in this class for the given semester and year
    results = Results.objects.filter(
        class_name=class_name,
        semester=semester,
        academic_year=academic_year
    ).order_by("-total_marks")  # Sort in descending order (higher marks first)

    rank = 1
    prev_marks = None
    position = 1

    for result in results:
        if prev_marks is not None and result.total_marks < prev_marks:
            rank += 1  # Increase rank only if total marks are different

        result.position = rank
        result.save()

        prev_marks = result.total_marks


# Create your views here.
def index(request):
    return render(request, "grades/index.html",)

def students(request):
    classes = ClassName.objects.all()
    return render(request, "grades/students.html", {"class_names": classes})

def results(request):
    classes = ClassName.objects.all()
    return render(request, "grades/results.html", {"classes": classes})

def class_results(request, slug):
    classes = get_object_or_404(ClassName, slug=slug)
    return render(request, "grades/class_results.html", {"class_name": classes})

def add_student(request, slug):
    class_info = get_object_or_404(ClassName, slug=slug)
    students_in_class = class_info.student_set.all().order_by('first_name', 'last_name')

    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            gender = form.cleaned_data['gender']  # Assuming gender is a field in Student
            
            # Use update_or_create to either update an existing student or create a new one
            Student.objects.update_or_create(
                first_name=first_name,
                last_name=last_name,
                class_name=class_info,  # Ensure student belongs to the correct class
                defaults={"gender": gender}  # Update gender if student exists
            )

            return redirect('add-student', slug=slug)  # Refresh page after adding/updating student
    else:
        form = StudentForm()

    return render(request, "grades/add-student.html", {
        "students_in_class": students_in_class,
        "form": form,
        "class_info": class_info,
    })
    
def add_result(request, slug):
    class_name = get_object_or_404(ClassName, slug=slug)
    class_students = Student.objects.filter(class_name=class_name)
    subjects = Subject.objects.all()
    
    if request.method == "POST":
        student_id = request.POST.get('student_name')
        subject_id = request.POST.get('subject')
        semester = request.POST.get('semester')
        class_score = request.POST.get('class_score')
        exam_score = request.POST.get('exam_score')
        academic_year = request.POST.get('academic_year')
        
        student = Student.objects.get(pk=student_id)
        subject = Subject.objects.get(pk=subject_id)
        
        Exams.objects.update_or_create(
            student_name=student,
            subject_name=subject,
            semester= int(semester),
            defaults={
                'class_score': float(class_score),
                'exams_score': float(exam_score),
                'class_name': class_name,
                'academic_year':academic_year,
                
    }
)
        
    
    return render(request, "grades/add-results.html", {"students": class_students, "subjects": subjects, "class_name": class_name})



def view_results(request, slug):
    class_name = get_object_or_404(ClassName, slug=slug)
    
    # Get available academic years dynamically
    available_years = Exams.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    # Get selected academic year and semester from request
    selected_academic_year = request.GET.get('academic_year', available_years.first() if available_years else "2024")  # Default to latest or 2024
    selected_semester = int(request.GET.get('semester', 1))  # Default to Semester 1
    
    print(selected_academic_year)

    # Get all students in the class
    class_students = Student.objects.filter(class_name=class_name)

    # Get recorded exam scores for the selected academic year and semester
    recorded_scores = {
        record['student_name_id']: record['total_score']
        for record in Exams.objects.filter(class_name=class_name, semester=selected_semester, academic_year=selected_academic_year)
        .values('student_name_id')
        .annotate(total_score=Sum('total_score'))
    }

    # Combine all students with their scores, default to 0 if no record exists
    student_scores = []
    for student in class_students:
        total_score = recorded_scores.get(student.id, 0)  # Use recorded score or 0
        student_scores.append({
            'student_name_id': student.id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'total_score': total_score
        })

    # Sort by total_score in descending order
    student_scores.sort(key=lambda x: x['total_score'], reverse=True)

    # Assign rankings (positions)
    previous_score = None
    rank = 0
    for student in student_scores:
        if student['total_score'] != previous_score:
            rank += 1  # Increase rank only for different scores
        student['position'] = rank
        previous_score = student['total_score']

        # Save/update results
        student_instance = Student.objects.get(id=student['student_name_id'])
        Results.objects.update_or_create(
            student_name=student_instance,
            class_name=class_name,
            semester=selected_semester,
            academic_year=selected_academic_year,
            defaults={'total_marks': student['total_score'], 'position': str(student['position'])}
        )

    return render(request, "grades/view-results.html", {
        "class_students": class_students,
        "class_name": class_name,
        "student_scores": student_scores,
        "selected_semester": selected_semester,
        "selected_academic_year": selected_academic_year,
        "available_years": available_years,  # Send academic years to template
    })









def view_report(request, slug, id):
    class_name = get_object_or_404(ClassName, slug=slug)
    student = get_object_or_404(Student, pk=id)
    print()
    
    available_years = Exams.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Get the selected semester and academic year from request
    selected_semester = int(request.GET.get('semester', 1))  # Default to semester 1
    selected_academic_year = request.GET.get('academic_year', "25/26")

    # Get all subjects
    all_subjects = Subject.objects.all()

    # Initialize a list to store exam data for all subjects
    exams_data = []
    final_score = 0  # Total combined score for the student

    for subject in all_subjects:
        # Filter exams based on student, subject, semester, and academic year
        exam = Exams.objects.filter(
            student_name=student,
            subject_name=subject,
            semester=selected_semester,
            academic_year=selected_academic_year
        ).first()

        if exam:
            exams_data.append({
                'subject_name': subject.subject_name,
                'class_score': exam.class_score,
                'exams_score': exam.exams_score,
                'class_to_30': exam.class_to_30,  # Add this field
                'exames_to_70': exam.exames_to_70,  # Add this field
                'total_score': exam.total_score,
            })
            final_score += exam.total_score
        else:
            exams_data.append({
                'subject_name': subject.subject_name,
                'class_score': 0,
                'exams_score': 0,
                'class_to_30': 0,  # Default to 0 if no exam exists
                'exames_to_70': 0,  # Default to 0 if no exam exists
                'total_score': 0,
            })

    # Get overall student rankings within the class
    student_position = None
    if final_score > 0:
        results_of_students = Results.objects.filter(
            class_name=class_name,
            semester=selected_semester,
            academic_year=selected_academic_year  # Ensure filtering by academic year
        ).values(
            'student_name', 'student_name__first_name', 'student_name__last_name'
        ).annotate(total_score=Sum('total_marks')).order_by('-total_score')

        # Rank students based on total scores
        student_positions = {}
        previous_score = None
        rank = 0

        for index, student_result in enumerate(results_of_students):
            if student_result['total_score'] != previous_score:
                rank = index + 1  # Update rank if score changes
            student_positions[student_result['student_name']] = rank
            previous_score = student_result['total_score']

        student_position = student_positions.get(student.id, None)

    # Calculate subject-wise rankings
    subject_positions = {}
    for subject in all_subjects:
        # Get all exams for this subject in the same class, semester, and year
        subject_exams = Exams.objects.filter(
            class_name=class_name,
            subject_name=subject,
            semester=selected_semester,
            academic_year=selected_academic_year  # Ensure correct filtering
        ).values('student_name').annotate(total_score=Sum('total_score')).order_by('-total_score')

        if not subject_exams.exists():
            # If no records exist, set subject position to None
            subject_positions[subject.subject_name] = None
            continue

        # Rank students within the subject
        subject_position_mapping = {}
        previous_subject_score = None
        subject_rank = 0

        for index, subject_result in enumerate(subject_exams):
            if subject_result['total_score'] != previous_subject_score:
                subject_rank = index + 1  # Update subject rank if score changes
            subject_position_mapping[subject_result['student_name']] = subject_rank
            previous_subject_score = subject_result['total_score']

        # If student does not exist in subject records, set position to None
        subject_positions[subject.subject_name] = subject_position_mapping.get(student.id, None)

    context = {
        'student': student,
        'total_combined_score': f"{final_score:.2f}",  # Round to 2 decimal places
        'position': student_position,
        'exams': exams_data,
        'subject_positions': subject_positions,
        'selected_semester': selected_semester,
        'selected_academic_year': selected_academic_year,
        "available_years": available_years, 
    }
    
    return render(request, "grades/view-report.html", context)


def get_scores(request):
    student_id = request.GET.get('student_id')
    subject_id = request.GET.get('subject_id')
    academic_year = request.GET.get('academic_year')
    semester = request.GET.get('semester')

    if student_id and subject_id  and semester:
        exam = Exams.objects.filter(
            student_name_id=student_id,
            subject_name_id=subject_id,
        
            semester=semester
        ).first()

        if exam:
            return JsonResponse({
                'class_score': exam.class_score,
                'exam_score': exam.exams_score,
            })
        else:
            return JsonResponse({
                'class_score': None,
                'exam_score': None,
            })
    else:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    

def get_subjects(request):
    student_id = request.GET.get('student_id')
    student = get_object_or_404(Student, id=student_id)

    # Fetch all subjects (or filter based on your logic)
    subjects = Subject.objects.all()

    # Return subjects as JSON
    return JsonResponse({
        'subjects': [
            {'id': subject.id, 'subject_name': subject.subject_name}
            for subject in subjects
        ]
    })
    




@csrf_exempt
def submit_grades(request):
    if request.method == "POST":
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        academic_year = request.POST.get('academic_year')
        semester = request.POST.get('semester')
        class_score = request.POST.get('class_score')
        exam_score = request.POST.get('exam_score')

        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        class_name = student.class_name

        # Save or update the exam record
        Exams.objects.update_or_create(
            student_name=student,
            subject_name=subject,
            academic_year=academic_year,
            semester=semester,
            defaults={
                'class_score': float(class_score),
                'exams_score': float(exam_score),
                'class_name': class_name,
            }
        )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def export_students_csv(request, slug):
    class_info = get_object_or_404(ClassName, slug=slug)
    students = Student.objects.filter(class_name=class_info)

    # Create the HttpResponse object with CSV headers
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{class_info.name}_students.csv"'

    # Create a CSV writer
    writer = csv.writer(response)
    writer.writerow(["First Name", "Last Name", "Gender"])

    # Write student data to the CSV file
    # for student in students:
    #     writer.writerow([student.first_name, student.last_name, student.gender])

    return response

def import_students_csv(request, slug):
    class_info = get_object_or_404(ClassName, slug=slug)

    if request.method == "POST":
        csv_file = request.FILES["csv_file"]

        # Read the CSV file
        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        # Import students from the CSV file
        for row in reader:
            Student.objects.update_or_create(
                first_name=row["First Name"],
                last_name=row["Last Name"],
                gender=row["Gender"],
                class_name=class_info,
            )

        return HttpResponseRedirect(reverse("add-student", args=[slug]))

    return HttpResponseRedirect(reverse("add-student", args=[slug]))





def enter_indv_student_result(request, slug, id):
    student = get_object_or_404(Student, pk=id)
    subjects = Subject.objects.all()
    class_name = get_object_or_404(ClassName, slug=slug)

    if request.method == "POST":
        semester = request.POST.get("semester")
        academic_year = request.POST.get("academic_year")
        total_marks = 0  # To store total marks for this student

        for subject in subjects:
            class_score = request.POST.get(f"class_score_{subject.id}")
            exams_score = request.POST.get(f"exam_score_{subject.id}")

            if class_score and exams_score:
                class_score = float(class_score)
                exams_score = float(exams_score)

                # Calculate derived fields
                class_to_30 = round(class_score * 0.3, 2)
                exams_to_70 = round(exams_score * 0.7, 2)
                total_score = class_to_30 + exams_to_70
                total_marks += total_score  # Add to total marks for the student

                # Save result in the Exams model
                Exams.objects.update_or_create(
                    student_name=student,
                    subject_name=subject,
                    semester=semester,
                    academic_year=academic_year,
                    defaults={
                        "class_score": class_score,
                        "class_to_30": class_to_30,
                        "exams_score": exams_score,
                        "exames_to_70": exams_to_70,
                        "total_score": total_score,
                        "class_name": class_name,
                    },
                )

        # ✅ Update or create the Results model
        result, created = Results.objects.update_or_create(
            student_name=student,
            class_name=class_name,
            semester=semester,
            academic_year=academic_year,
            defaults={"total_marks": total_marks}
        )

        # ✅ Update positions of all students
        update_student_positions(class_name, semester, academic_year)

        messages.success(request, "✅ Results successfully recorded!")
        return redirect("add-student", slug=slug)

    # Fetch existing results for the student
    existing_results = Exams.objects.filter(student_name=student)
    results_dict = {}

    for result in existing_results:
        key = f"{result.subject_name.id}_{result.semester}_{result.academic_year}"
        results_dict[key] = {
            "class_score": float(result.class_score),  
            "class_to_30": float(result.class_to_30),  
            "exams_score": float(result.exams_score),  
            "exames_to_70": float(result.exames_to_70),  
            "total_score": float(result.total_score),  
        }

    # Current academic year (defaults to current year in YY/YY format)
    current_year = datetime.now().year
    default_academic_year = f"{str(current_year)[-2:]}/{str(current_year + 1)[-2:]}"  

    return render(
        request,
        "grades/add-student-result.html",
        {
            "subjects": subjects,
            "student": student,
            "class_name": class_name,
            "default_academic_year": "24/25",
            "results_dict": json.dumps(results_dict),  # Ensure results_dict is JSON
        },
    )
    



def print_all_reports(request, slug):
    class_info = get_object_or_404(ClassName, slug=slug)
    students = Student.objects.filter(class_name=class_info).order_by('first_name', 'last_name')

    # Get available academic years dynamically
    available_years = Exams.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    # Get selected semester and academic year from request
    selected_semester = int(request.GET.get('semester', 1))  # Default to 1
    selected_academic_year = request.GET.get('academic_year', available_years.first() if available_years else "2024")  # Default to latest or 2024

    all_subjects = Subject.objects.all()
    all_reports = []
    student_scores = []
    subject_scores = {}

    # Collect student exam results
    for student in students:
        exams_data = []
        final_score = 0

        for subject in all_subjects:
            exam = Exams.objects.filter(
                student_name=student,
                subject_name=subject,
                semester=selected_semester,
                academic_year=selected_academic_year
            ).first()

            if exam:
                total_subject_score = exam.class_to_30 + exam.exames_to_70  # 30% + 70%
                exams_data.append({
                    'subject_name': subject.subject_name,
                    'class_score': exam.class_to_30,
                    'exams_score': exam.exames_to_70,
                    'total_score': total_subject_score,
                })
                final_score += total_subject_score

                # Store subject scores for ranking
                if subject.subject_name not in subject_scores:
                    subject_scores[subject.subject_name] = []
                subject_scores[subject.subject_name].append((student.id, total_subject_score))
            else:
                exams_data.append({
                    'subject_name': subject.subject_name,
                    'class_score': 0,
                    'exams_score': 0,
                    'total_score': 0,
                })

        # Store for ranking
        student_scores.append({
            'student': student,
            'total_score': final_score,
            'exams': exams_data
        })

    # Rank students based on total score
    student_scores.sort(key=lambda x: x['total_score'], reverse=True)
    previous_score = None
    rank = 0
    student_positions = {}

    for index, student_result in enumerate(student_scores):
        if student_result['total_score'] != previous_score:
            rank = index + 1  # Rank increases only when score changes
        student_positions[student_result['student'].id] = rank
        previous_score = student_result['total_score']

    # Rank students within each subject
    subject_positions = {}

    for subject_name, scores in subject_scores.items():
        scores.sort(key=lambda x: x[1], reverse=True)  # Sort by total subject score
        previous_subject_score = None
        subject_rank = 0
        subject_position_mapping = {}

        for index, (student_id, total_subject_score) in enumerate(scores):
            if total_subject_score != previous_subject_score:
                subject_rank = index + 1  # Rank increases only when score changes
            
            subject_position_mapping[student_id] = subject_rank
            previous_subject_score = total_subject_score

        subject_positions[subject_name] = subject_position_mapping

    # Assign correct rankings and prepare final data
    for student_data in student_scores:
        student_id = student_data['student'].id
        student_subject_positions = {}

        for subject in all_subjects:
            student_subject_positions[subject.subject_name] = subject_positions.get(subject.subject_name, {}).get(student_id, None)

        all_reports.append({
            'student': student_data['student'],
            'total_combined_score': f"{student_data['total_score']:.2f}",
            'position': student_positions.get(student_id, None),
            'exams': student_data['exams'],
            'subject_positions': student_subject_positions,
        })

    return render(request, "grades/print-all-reports.html", {
        'class_info': class_info,
        'all_reports': all_reports,
        'selected_semester': selected_semester,
        'selected_academic_year': selected_academic_year,
        'available_years': available_years,  # Send academic years to template
    })
    
def export_grades_csv(request, slug):
    # Get students in the class
    students = Student.objects.filter(class_name__slug=slug).order_by('first_name', 'last_name')
    subjects = Subject.objects.all()
    
    # Define CSV headers
    headers = ['No', 'First Name', 'Last Name', 'Semester', 'Academic Year']
    for subject in subjects:
        headers.append(f'{subject.subject_name} - Class Score')
        headers.append(f'{subject.subject_name} - Exams Score')
    
    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="grades_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(headers)
    
    number_of_students = 0
    
    # Populate student names but leave scores empty
    for student in students:
        number_of_students+=1
        row = [number_of_students,  student.first_name, student.last_name, '1', '25/26']  # Empty semester & year
        row.extend(['', ''] * len(subjects))  # Empty scores
        writer.writerow(row)
    
    return response

def import_grades_csv(request, slug):
    class_name = get_object_or_404(ClassName, slug=slug)

    if request.method == 'POST' and request.FILES.get('grades_csv'):
        csv_file = request.FILES['grades_csv']
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        # Read headers
        headers = next(reader)
        subjects = Subject.objects.all()

        for row in reader:
            # Skip empty rows
            if not any(row):
                continue

            # Ensure the row has at least the first 5 columns (No, First Name, Last Name, Semester, Academic Year)
            if len(row) < 5:
                continue

            # Extract first name, last name, semester, academic year
            _, first_name, last_name, semester, academic_year = row[:5]

            # Fetch student by first & last name in the given class
            student = Student.objects.filter(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                class_name=class_name
            ).first()

            if not student:
                print(f"Student {first_name} {last_name} not found in class {class_name.name}, skipping...")
                continue

            # Process subject scores (each subject has two columns: Class Score, Exams Score)
            for i, subject in enumerate(subjects):
                class_score_index = 5 + (i * 2)
                exams_score_index = 6 + (i * 2)

                if class_score_index >= len(row) or exams_score_index >= len(row):
                    print(f"Missing scores for {subject.subject_name} for {first_name} {last_name}, skipping...")
                    continue

                class_score = row[class_score_index].strip()
                exams_score = row[exams_score_index].strip()

                if not class_score and not exams_score:
                    continue  # Skip if both are empty

                try:
                    class_score = float(class_score) if class_score else 0
                    exams_score = float(exams_score) if exams_score else 0
                except ValueError:
                    print(f"Invalid scores for {subject.subject_name} for {first_name} {last_name}, skipping...")
                    continue

                # Save scores to Exams model
                exam, created = Exams.objects.update_or_create(
                    student_name=student,
                    subject_name=subject,
                    semester=int(semester),
                    academic_year=academic_year,
                    class_name=class_name,
                    defaults={
                        'class_score': class_score,
                        'exams_score': exams_score,
                    }
                )

            # After processing all subjects, calculate and save the average to Results
            exams = Exams.objects.filter(student_name=student, semester=semester, academic_year=academic_year)
            total_marks = sum(exam.total_score for exam in exams)
            total_subjects = exams.count()

            if total_subjects > 0:
                average_marks = total_marks / total_subjects
                Results.objects.update_or_create(
                    student_name=student,
                    class_name=class_name,
                    semester=int(semester),
                    academic_year=academic_year,
                    defaults={'total_marks': average_marks}
                )

        messages.success(request, "Grades imported successfully.")
        return redirect('add-student', class_name.slug)

    messages.error(request, "Invalid request.")
    return redirect('add-student', class_name.slug)


# @csrf_exempt
# def add_subject(request):
#     if request.method == "POST":
#         subject_name = request.POST.get("subject_name")
#         teacher_name = request.POST.get("teacher_name")
#         student_id = request.POST.get("student_id")
#         class_name = request.POST.get("class_name")
        
#         print("SubjectName", subject_name)

#         if subject_name and teacher_name:
#             subject = Subject.objects.create(subject_name=subject_name, teacher_name=teacher_name)
#             messages.success(request, "Subject added successfully")
#             return reverse("enter-indv-student-result", args=[class_name, student_id])
#         # else:
#         #     messages.error("Inavlid Data")
#         #     return JsonResponse({"success": False, "error": "Invalid data"})
#     # return JsonResponse({"success": False, "error": "Invalid request method"})

@csrf_exempt
def add_subject(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse the JSON body
            subject_name = data.get("subject_name")
            teacher_name = data.get("teacher_name")

            if subject_name and teacher_name:
                subject = Subject.objects.create(subject_name=subject_name, teacher_name=teacher_name)
                messages.success(request, f"Subject '{subject_name}' added successfully!")  # Add success message
                return JsonResponse({"success": True, "subject_id": subject.id})
            else:
                return JsonResponse({"success": False, "error": "Invalid data"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"})

    return JsonResponse({"success": False, "error": "Invalid request method"})

def exams_type(request, slug):
    class_name = get_object_or_404(ClassName, slug=slug)
    return render(request, "grades/exams_type.html", {"class": class_name})

def students_mid_terms(request, slug):
    class_info = get_object_or_404(ClassName, slug=slug)
    students_in_class = class_info.student_set.all().order_by('first_name', 'last_name')

    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            gender = form.cleaned_data['gender']  # Assuming gender is a field in Student
            
            # Use update_or_create to either update an existing student or create a new one
            Student.objects.update_or_create(
                first_name=first_name,
                last_name=last_name,
                class_name=class_info,  # Ensure student belongs to the correct class
                defaults={"gender": gender}  # Update gender if student exists
            )

            return redirect('students-mid-term', slug=slug)  # Refresh page after adding/updating student
    else:
        form = StudentForm()

    return render(request, "grades/students_mid_term.html", {
        "students_in_class": students_in_class,
        "form": form,
        "class_info": class_info,
    })
    
    
def export_grades_csv_mid_term(request, slug):
    # Get students in the class
    students = Student.objects.filter(class_name__slug=slug).order_by('first_name', 'last_name')
    subjects = Subject.objects.all()

    # Define CSV headers
    headers = ['No', 'First Name', 'Last Name', 'Semester', 'Academic Year']
    for subject in subjects:
        headers.append(f'{subject.subject_name} - Score')

    # Create the CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="grades_template.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)

    # Populate student rows with a proper count (1, 2, 3, ...)
    number_of_student = 0  # Start at 0 so first student is 1

    for student in students:
        number_of_student += 1  # Increment before writing the row
        row = [number_of_student, student.first_name, student.last_name, '1', '25/26']  # Empty semester & year
        row.extend([''] * len(subjects))  # Empty scores
        writer.writerow(row)

    return response


def import_grades_csv_mid_term(request, slug):
    class_name = get_object_or_404(ClassName, slug=slug)

    if request.method == 'POST' and request.FILES.get('grades_csv'):
        csv_file = request.FILES['grades_csv']
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        # Read headers
        headers = next(reader)

        # Fetch all subjects in the system
        subjects = Subject.objects.all()

        for row in reader:
            if not any(row):
                continue  # Skip completely empty rows

            if len(row) < 5:
                print(f"Skipping incomplete row: {row}")
                continue

            number, first_name, last_name, semester, academic_year = row[:5]

            try:
                student = Student.objects.get(
                    first_name=first_name,
                    last_name=last_name,
                    class_name=class_name
                )
            except Student.DoesNotExist:
                print(f"Student not found: {first_name} {last_name}")
                continue

            # Process scores for each subject
            for idx, subject in enumerate(subjects):
                score_column_index = 5 + idx  # Start after basic columns
                if score_column_index >= len(row):
                    print(f"Missing score for {subject.subject_name}, skipping")
                    continue

                score = row[score_column_index]

                if not score.strip():
                    # If no score provided, skip this subject for this student
                    continue

                try:
                    score = float(score)
                except ValueError:
                    print(f"Invalid score '{score}' for {subject.subject_name}, skipping")
                    continue

                # Save to MidTermExams
                exam, created = MidTermExams.objects.update_or_create(
                    student=student,
                    class_name=class_name,
                    subject=subject,
                    semester=int(semester),
                    academic_year=academic_year,
                    defaults={
                        'scores': score
                    }
                )
                
                print("Pels")

                print(f"Saved {subject.subject_name} score for {student.first_name}: {score}")

        messages.success(request, "Mid-Term grades imported successfully.")
        return redirect('students-mid-term', class_name.slug)

    messages.error(request, "Invalid request.")
    return redirect('students-mid-term', class_name.slug)


def mid_term_indv_result(request, slug, id):
    student = get_object_or_404(Student, pk=id)
    subjects = Subject.objects.all()
    class_name = get_object_or_404(ClassName, slug=slug)

    if request.method == "POST":
        semester = request.POST.get("semester")
        academic_year = request.POST.get("academic_year")

        for subject in subjects:
            score = request.POST.get(f"score_{subject.id}")

            if score:
                MidTermExams.objects.update_or_create(
                    student=student,
                    subject=subject,
                    class_name=class_name,
                    semester=semester,
                    academic_year=academic_year,
                    defaults={
                        "scores": float(score)
                    },
                )

        messages.success(request, "✅ Mid-Term Results successfully recorded!")
        return redirect("students-mid-term", slug=slug)

    # Fetch existing mid-term results
    existing_results = MidTermExams.objects.filter(student=student)

    results_dict = {}
    for result in existing_results:
        key = f"{result.subject.id}_{result.semester}_{result.academic_year}"
        results_dict[key] = {
            "score": float(result.scores) if result.scores is not None else None
        }

    # Default academic year
    current_year = datetime.now().year
    default_academic_year = f"{str(current_year)[-2:]}/{str(current_year + 1)[-2:]}"  

    return render(
        request,
        "grades/mid_term_indv_result.html",
        {
            "subjects": subjects,
            "student": student,
            "class_name": class_name,
            "default_academic_year": default_academic_year,  # You can also use `default_academic_year` variable if you want dynamic
            "results_dict": json.dumps(results_dict),  # Make sure results_dict is passed as JSON string
        },
    )
    
    
def mid_term_view_report(request, slug, id):
    class_name = get_object_or_404(ClassName, slug=slug)
    student = get_object_or_404(Student, pk=id)

    available_years = MidTermExams.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    selected_semester = int(request.GET.get('semester', 1))
    selected_academic_year = request.GET.get('academic_year', "25/26")

    all_subjects = Subject.objects.all()

    exams_data = []
    final_score = 0

    for subject in all_subjects:
        midterm_exam = MidTermExams.objects.filter(
            student=student,
            subject=subject,
            semester=selected_semester,
            academic_year=selected_academic_year
        ).first()

        if midterm_exam:
            exams_data.append({
                'subject_name': subject.subject_name,
                'scores': midterm_exam.scores
            })
            final_score += float(midterm_exam.scores)
        else:
            exams_data.append({
                'subject_name': subject.subject_name,
                'scores': 0
            })

    student_position = None
    if final_score > 0:
        all_students_scores = MidTermExams.objects.filter(
            class_name=class_name,
            semester=selected_semester,
            academic_year=selected_academic_year
        ).values(
            'student'
        ).annotate(total_score=Sum('scores')).order_by('-total_score')

        student_positions = {}
        previous_score = None
        rank = 0

        for index, result in enumerate(all_students_scores):
            if result['total_score'] != previous_score:
                rank = index + 1
            student_positions[result['student']] = rank
            previous_score = result['total_score']

        student_position = student_positions.get(student.id, None)

    subject_positions = {}
    for subject in all_subjects:
        subject_scores = MidTermExams.objects.filter(
            class_name=class_name,
            subject=subject,
            semester=selected_semester,
            academic_year=selected_academic_year
        ).values(
            'student'
        ).annotate(total_score=Sum('scores')).order_by('-total_score')

        if not subject_scores.exists():
            subject_positions[subject.subject_name] = None
            continue

        subject_rankings = {}
        previous_subject_score = None
        subject_rank = 0

        for index, subject_result in enumerate(subject_scores):
            if subject_result['total_score'] != previous_subject_score:
                subject_rank = index + 1
            subject_rankings[subject_result['student']] = subject_rank
            previous_subject_score = subject_result['total_score']

        subject_positions[subject.subject_name] = subject_rankings.get(student.id, None)

    context = {
        'student': student,
        'total_combined_score': f"{final_score:.2f}",
        'position': student_position,
        'exams': exams_data,
        'subject_positions': subject_positions,
        'selected_semester': selected_semester,
        'selected_academic_year': selected_academic_year,
        "available_years": available_years,
    }

    return render(request, "grades/mid_term_view_report.html", context)


def mid_term_print_all_reports(request, slug):
    class_info = get_object_or_404(ClassName, slug=slug)
    students = Student.objects.filter(class_name=class_info).order_by('first_name', 'last_name')

    # Get available academic years dynamically
    available_years = MidTermExams.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    # Get selected semester and academic year from request
    selected_semester = int(request.GET.get('semester', 1))  # Default to 1
    selected_academic_year = request.GET.get('academic_year', available_years.first() if available_years else "25/26")  # Default to latest or 2024

    all_subjects = Subject.objects.all()
    all_reports = []
    student_scores = []
    subject_scores = {}

    # Collect student exam results
    for student in students:
        exams_data = []
        final_score = 0

        for subject in all_subjects:
            exam = MidTermExams.objects.filter(
                student=student,
                subject=subject,
                semester=selected_semester,
                academic_year=selected_academic_year
            ).first()  # Use filter().first() instead of get()

            if exam:
                total_subject_score = exam.scores  # 30% + 70%
                exams_data.append({
                    'subject_name': subject.subject_name,
                    'scores': total_subject_score,
                })
                final_score += total_subject_score

                # Store subject scores for ranking
                if subject.subject_name not in subject_scores:
                    subject_scores[subject.subject_name] = []
                subject_scores[subject.subject_name].append((student.id, total_subject_score))
            else:
                exams_data.append({
                    'subject_name': subject.subject_name,
                    'scores': 0,
                })

        # Store for ranking
        student_scores.append({
            'student': student,
            'scores': final_score,
            'exams': exams_data
        })

    # Rank students based on total score
    student_scores.sort(key=lambda x: x['scores'], reverse=True)
    previous_score = None
    rank = 0
    student_positions = {}

    for index, student_result in enumerate(student_scores):
        if student_result['scores'] != previous_score:
            rank = index + 1  # Rank increases only when score changes
        student_positions[student_result['student'].id] = rank
        previous_score = student_result['scores']

    # Rank students within each subject
    subject_positions = {}

    for subject_name, scores in subject_scores.items():
        scores.sort(key=lambda x: x[1], reverse=True)  # Sort by total subject score
        previous_subject_score = None
        subject_rank = 0
        subject_position_mapping = {}

        for index, (student_id, total_subject_score) in enumerate(scores):
            if total_subject_score != previous_subject_score:
                subject_rank = index + 1  # Rank increases only when score changes
            
            subject_position_mapping[student_id] = subject_rank
            previous_subject_score = total_subject_score

        subject_positions[subject_name] = subject_position_mapping

    # Assign correct rankings and prepare final data
    for student_data in student_scores:
        student_id = student_data['student'].id
        student_subject_positions = {}

        for subject in all_subjects:
            student_subject_positions[subject.subject_name] = subject_positions.get(subject.subject_name, {}).get(student_id, None)

        all_reports.append({
            'student': student_data['student'],
            'total_combined_score': f"{student_data['scores']:.2f}",
            'position': student_positions.get(student_id, None),
            'exams': student_data['exams'],
            'subject_positions': student_subject_positions,
        })

    return render(request, "grades/mid_term_print_all_reports.html", {
        'class_info': class_info,
        'all_reports': all_reports,
        'selected_semester': selected_semester,
        'selected_academic_year': selected_academic_year,
        'available_years': available_years,  # Send academic years to template
    })
    
def results_exam_type(request, slug):
    class_info = get_object_or_404(ClassName, slug=slug)
    
    return render(request, "grades/results_exam_type.html", {"class": class_info})


def view_mid_term_results(request, slug):
    class_name = get_object_or_404(ClassName, slug=slug)
    
    # Get available academic years dynamically
    available_years = MidTermExams.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    # Get selected academic year and semester from request
    selected_academic_year = request.GET.get('academic_year', available_years.first() if available_years else "2024")  # Default to latest or 2024
    selected_semester = int(request.GET.get('semester', 1))  # Default to Semester 1
    
    print(selected_academic_year)

    # Get all students in the class
    class_students = Student.objects.filter(class_name=class_name)

    # Get recorded exam scores for the selected academic year and semester
    recorded_scores = {
        record['student_id']: record['total_score']
        for record in MidTermExams.objects.filter(class_name=class_name, semester=selected_semester, academic_year=selected_academic_year)
        .values('student_id')
        .annotate(total_score=Sum('scores'))
    }

    # Combine all students with their scores, default to 0 if no record exists
    student_scores = []
    for student in class_students:
        total_score = recorded_scores.get(student.id, 0)  # Use recorded score or 0
        student_scores.append({
            'student_name_id': student.id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'total_score': total_score
        })

    # Sort by total_score in descending order
    student_scores.sort(key=lambda x: x['total_score'], reverse=True)

    # Assign rankings (positions)
    previous_score = None
    rank = 0
    for student in student_scores:
        if student['total_score'] != previous_score:
            rank += 1  # Increase rank only for different scores
        student['position'] = rank
        previous_score = student['total_score']

    return render(request, "grades/mid_term_class_results.html", {
        "class_students": class_students,
        "class_name": class_name,
        "student_scores": student_scores,
        "selected_semester": selected_semester,
        "selected_academic_year": selected_academic_year,
        "available_years": available_years,  # Send academic years to template
    })
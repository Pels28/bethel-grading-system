from .models import Exams, Student

def calculate_student_position(student, class_info):
    # Get all students in the class
    students = Student.objects.filter(class_name=class_info)

    # Create a dictionary to store total scores
    student_scores = {}

    for student in students:
        exams = Exams.objects.filter(student_name=student)
        total_score = sum(exam.total_score for exam in exams)  # Sum all subject scores
        student_scores[student.id] = total_score  # Store total score

    # Sort students by total score (highest first)
    ranked_students = sorted(student_scores.items(), key=lambda x: x[1], reverse=True)

    # Assign positions
    position = 1
    last_score = None
    position_dict = {}

    for idx, (student_id, score) in enumerate(ranked_students):
        if last_score is not None and score < last_score:
            position = idx + 1  # Rank updates only if score is different
        position_dict[student_id] = position
        last_score = score

    return position_dict.get(student.id, "N/A")  # Return the student's position

// document.addEventListener("DOMContentLoaded", function () {
//     const studentSelect = document.getElementById("student_name");
//     const subjectSelect = document.getElementById("subject");
//     const semesterSelect = document.getElementById("semester");
//     const classScoreInput = document.getElementById("class_score");
//     const examScoreInput = document.getElementById("exam_score");
  
//     // Function to fetch scores
//     function fetchScores() {
//       const studentId = studentSelect.value;
//       const subjectId = subjectSelect.value;
//       const semester = semesterSelect.value;
  
//       if (studentId && subjectId && semester) {
//         const url = `/api/get-scores/?student_id=${studentId}&subject_id=${subjectId}&semester=${semester}`;
  
//         fetch(url)
//           .then((response) => response.json())
//           .then((data) => {
//             if (data.class_score !== null) {
//               classScoreInput.value = data.class_score;
//             } else {
//               classScoreInput.value = "";
//             }
  
//             if (data.exams_score !== null) {
//               examScoreInput.value = data.exams_score;
//             } else {
//               examScoreInput.value = "";
//             }
//           })
//           .catch((error) => {
//             console.error("Error fetching scores:", error);
//           });
//       } else {
//         // Clear the fields if any of the dropdowns are not selected
//         classScoreInput.value = "";
//         examScoreInput.value = "";
//       }
//     }
  
//     // Add event listeners to the dropdowns
//     studentSelect.addEventListener("change", fetchScores);
//     subjectSelect.addEventListener("change", fetchScores);
//     semesterSelect.addEventListener("change", fetchScores);
//   });

document.addEventListener("DOMContentLoaded", function () {
    const studentLinks = document.querySelectorAll(".student-link");
    const subjectList = document.getElementById("subjectList");
    const subjectListContent = document.getElementById("subjectListContent");
    const gradeForm = document.getElementById("gradeForm");
    const gradeFormContent = document.getElementById("gradeFormContent");
    const studentIdInput = document.getElementById("studentId");
    const subjectIdInput = document.getElementById("subjectId");
    const academicYearSelect = document.getElementById("academic-year");
    const semesterSelect = document.getElementById("semester");
    const classScoreInput = document.getElementById("class_score");
    const examScoreInput = document.getElementById("exam_score");

    // Remove highlight from all students
    function clearStudentHighlight() {
        studentLinks.forEach(link => link.classList.remove("selected-student"));
    }

    // Remove highlight from all subjects
    function clearSubjectHighlight() {
        document.querySelectorAll(".subject-link").forEach(link => link.classList.remove("selected-subject"));
    }

    // Reset form fields
    function resetFormFields() {
        academicYearSelect.value = "";
        semesterSelect.value = "";
        classScoreInput.value = "";
        examScoreInput.value = "";
    }

    // Fetch subjects for a student
    function fetchSubjects(studentId, studentElement) {
        fetch(`/api/get-subjects/?student_id=${studentId}`)
            .then(response => response.json())
            .then(data => {
                // Clear previous subjects
                subjectListContent.innerHTML = "";

                // Highlight selected student
                clearStudentHighlight();
                studentElement.classList.add("selected-student");

                // Add subjects to the list
                data.subjects.forEach(subject => {
                    const li = document.createElement("li");
                    const a = document.createElement("a");
                    a.href = "#";
                    a.textContent = subject.subject_name;
                    a.dataset.subjectId = subject.id;
                    a.classList.add("subject-link");
                    li.appendChild(a);
                    subjectListContent.appendChild(li);
                });

                // Show the subject list
                subjectList.style.display = "block";
            })
            .catch(error => console.error("Error fetching subjects:", error));
    }

    // Fetch scores for a student, subject, and semester
    function fetchScores(studentId, subjectId, academicYear, semester) {
        fetch(`/api/get-scores/?student_id=${studentId}&subject_id=${subjectId}&academic_year=${academicYear}&semester=${semester}`)
            .then(response => response.json())
            .then(data => {
                if (data.class_score !== null) {
                    classScoreInput.value = data.class_score;
                } else {
                    classScoreInput.value = "";
                }

                if (data.exam_score !== null) {
                    examScoreInput.value = data.exam_score;
                } else {
                    examScoreInput.value = "";
                }
            })
            .catch(error => console.error("Error fetching scores:", error));
    }

    // Handle student link clicks
    studentLinks.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const studentId = this.dataset.studentId;

            // Set the student ID in the hidden input
            studentIdInput.value = studentId;

            // Fetch and display subjects for the selected student
            fetchSubjects(studentId, this);
        });
    });

    // Handle subject link clicks dynamically (event delegation)
    subjectListContent.addEventListener("click", function (e) {
        if (e.target.classList.contains("subject-link")) {
            e.preventDefault();
            const subjectId = e.target.dataset.subjectId;

            // Set the subject ID in the hidden input
            subjectIdInput.value = subjectId;

            // Highlight selected subject
            clearSubjectHighlight();
            e.target.classList.add("selected-subject");

            // Reset form fields
            resetFormFields();

            // Show the grade form
            gradeForm.style.display = "block";
        }
    });

    // Handle changes in academic year or semester
    academicYearSelect.addEventListener("change", function () {
        const studentId = studentIdInput.value;
        const subjectId = subjectIdInput.value;
        const academicYear = academicYearSelect.value;
        const semester = semesterSelect.value;

        if (studentId && subjectId && academicYear && semester) {
            fetchScores(studentId, subjectId, academicYear, semester);
        }
    });

    semesterSelect.addEventListener("change", function () {
        const studentId = studentIdInput.value;
        const subjectId = subjectIdInput.value;
        const academicYear = academicYearSelect.value;
        const semester = semesterSelect.value;

        if (studentId && subjectId && academicYear && semester) {
            fetchScores(studentId, subjectId, academicYear, semester);
        }
    });

    // Handle form submission
    gradeFormContent.addEventListener("submit", function (e) {
        e.preventDefault();

        const formData = new FormData(this);

        fetch("/submit-grades/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Grades submitted successfully!");
                    // Clear the form
                    gradeFormContent.reset();
                    // Hide the form
                    gradeForm.style.display = "none";
                } else {
                    alert("Error submitting grades.");
                }
            })
            .catch(error => console.error("Error submitting grades:", error));
    });
});
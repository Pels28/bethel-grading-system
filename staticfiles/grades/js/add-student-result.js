document.addEventListener("DOMContentLoaded", function () {
    const semesterDropdown = document.getElementById("semester");
    const academicYearDropdown = document.getElementById("academic_year");

    // Function to update form fields based on selected semester and academic year
    function updateFormFields() {
        const semester = semesterDropdown.value;
        const academicYear = academicYearDropdown.value;

        if (semester && academicYear) {
            document.querySelectorAll("tbody tr").forEach((row) => {
                const subjectId = row.dataset.subjectId;
                const key = `${subjectId}_${semester}_${academicYear}`;
                const existingData = resultsDict[key];

                if (existingData) {
                    row.querySelector(".class-score").value = existingData.class_score || "";
                    row.querySelector(".exam-30").value = existingData.class_to_30 || "";
                    row.querySelector(".exam-score").value = existingData.exams_score || "";
                    row.querySelector(".exam-70").value = existingData.exames_to_70 || "";
                    row.querySelector(".total-score").value = existingData.total_score || "";
                } else {
                    row.querySelector(".class-score").value = "";
                    row.querySelector(".exam-30").value = "";
                    row.querySelector(".exam-score").value = "";
                    row.querySelector(".exam-70").value = "";
                    row.querySelector(".total-score").value = "";
                }
            });
        }
    }

    // Function to calculate derived scores (30% of class score, 70% of exam score, and total score)
    function calculateDerivedScores() {
        document.querySelectorAll("tbody tr").forEach((row) => {
            const classScoreInput = row.querySelector(".class-score");
            const examScoreInput = row.querySelector(".exam-score");
            const class30Input = row.querySelector(".exam-30");
            const exam70Input = row.querySelector(".exam-70");
            const totalInput = row.querySelector(".total-score");

            // Calculate 30% of class score and total score when class score changes
            classScoreInput.addEventListener("input", function () {
                const classScore = parseFloat(this.value) || 0;
                class30Input.value = (classScore * 0.3).toFixed(2);
                totalInput.value = (parseFloat(class30Input.value) + parseFloat(exam70Input.value || 0)).toFixed(2);
            });

            // Calculate 70% of exam score and total score when exam score changes
            examScoreInput.addEventListener("input", function () {
                const examScore = parseFloat(this.value) || 0;
                exam70Input.value = (examScore * 0.7).toFixed(2);
                totalInput.value = (parseFloat(class30Input.value || 0) + parseFloat(exam70Input.value)).toFixed(2);
            });
        });
    }

    // Update form fields when semester or academic year changes
    semesterDropdown.addEventListener("change", updateFormFields);
    academicYearDropdown.addEventListener("change", updateFormFields);

    // Call functions on page load
    updateFormFields();
    calculateDerivedScores();

    // Modal functionality
    const addSubjectButton = document.getElementById("addSubjectButton");
    const modal = document.getElementById("addSubjectModal");
    const closeModal = document.querySelector(".close");
    const addSubjectForm = document.getElementById("addSubjectForm");
    const gradeForm = document.getElementById("gradeForm");

    // Open modal when "Add Subject" button is clicked
    addSubjectButton.addEventListener("click", function () {
        modal.style.display = "block";
    });

    // Close modal when the close button is clicked
    closeModal.addEventListener("click", function () {
        modal.style.display = "none";
    });

    // Close modal when clicking outside the modal
    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });

    // Handle form submission for adding a new subject
    addSubjectForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const subjectName = document.getElementById("subjectName").value;
        const teacherName = document.getElementById("teacherName").value;
        const className = document.getElementById("className").value;

        fetch("/add-subject/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}",
            },
            body: JSON.stringify({
                subject_name: subjectName,
                teacher_name: teacherName,
                class_name: className,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    // Add a new row to the table
                    const tableBody = document.querySelector("#gradesTable tbody");
                    const newRow = document.createElement("tr");
                    newRow.setAttribute("data-subject-id", data.subject_id);

                    newRow.innerHTML = `
                        <td>${subjectName}</td>
                        <td><input type="number" name="class_score_${data.subject_id}" class="class-score" min="0" max="100"></td>
                        <td><input type="number" class="exam-30" readonly></td>
                        <td><input type="number" name="exam_score_${data.subject_id}" class="exam-score" min="0" max="100"></td>
                        <td><input type="number" class="exam-70" readonly></td>
                        <td><input type="number" class="total-score" readonly></td>
                        <td><button type="button" class="delete-btn">Delete</button></td>
                    `;

                    tableBody.appendChild(newRow);
                    modal.style.display = "none";
                    addSubjectForm.reset();

                    // Clear existing success messages
                    const existingMessages = document.querySelectorAll(".alert-success");
                    existingMessages.forEach((message) => message.remove());

                    // Display a success message
                    const messageContainer = document.createElement("div");
                    messageContainer.className = "alert alert-success";
                    messageContainer.setAttribute("role", "alert");
                    messageContainer.textContent = `Subject '${subjectName}' added successfully!`;

                    // Insert the message at the top of the container
                    const container = document.querySelector(".container");
                    container.insertBefore(messageContainer, container.firstChild);

                    // Remove the message after 5 seconds
                    setTimeout(() => {
                        messageContainer.remove();
                    }, 5000);

                    // Recalculate derived scores for the new row
                    calculateDerivedScores();

                    // Trigger form submission to include the new input field
                    gradeForm.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
                } else {
                    alert(data.error || "Failed to add subject. Please try again.");
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                alert("An error occurred. Please try again.");
            });
    });

    // Add event listeners for delete buttons
    const tableBody = document.querySelector("#gradesTable tbody");
    tableBody.addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-btn")) {
            const row = event.target.closest("tr");
            const subjectId = row.dataset.subjectId;

            // Confirm deletion
            const confirmDelete = confirm("Are you sure you want to delete this subject?");
            if (confirmDelete) {
                deleteSubject(subjectId, row);
            }
        }
    });

    // Function to delete a subject
    function deleteSubject(subjectId, row) {
        fetch(`/delete-subject/${subjectId}/`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    // Remove the row from the table
                    row.remove();

                    // Clear existing success messages
                    const existingMessages = document.querySelectorAll(".alert-success");
                    existingMessages.forEach((message) => message.remove());

                    // Display a success message
                    const messageContainer = document.createElement("div");
                    messageContainer.className = "alert alert-success";
                    messageContainer.setAttribute("role", "alert");
                    messageContainer.textContent = "Subject deleted successfully!";

                    // Insert the message at the top of the container
                    const container = document.querySelector(".container");
                    container.insertBefore(messageContainer, container.firstChild);

                    // Remove the message after 5 seconds
                    setTimeout(() => {
                        messageContainer.remove();
                    }, 5000);
                } else {
                    alert(data.error || "Failed to delete subject. Please try again.");
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                alert("An error occurred. Please try again.");
            });
    }
});
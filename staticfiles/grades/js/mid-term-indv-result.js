document.addEventListener("DOMContentLoaded", function () {
    const semesterDropdown = document.getElementById("semester");
    const academicYearDropdown = document.getElementById("academic_year");

    function updateFormFields() {
        const semester = semesterDropdown.value;
        const academicYear = academicYearDropdown.value;

        if (semester && academicYear) {
            document.querySelectorAll("tbody tr").forEach((row) => {
                const subjectId = row.dataset.subjectId;
                const key = `${subjectId}_${semester}_${academicYear}`;
                const existingData = resultsDict[key];

                if (existingData) {
                    row.querySelector(".score").value = existingData.score || "";
                } else {
                    row.querySelector(".score").value = "";
                }
            });
        }
    }

    semesterDropdown.addEventListener("change", updateFormFields);
    academicYearDropdown.addEventListener("change", updateFormFields);

    updateFormFields();  // Call on load in case default semester/year is selected


  const addSubjectButton = document.getElementById("addSubjectButton");
  const modal = document.getElementById("addSubjectModal");
  const closeModal = document.querySelector(".close");
  const addSubjectForm = document.getElementById("addSubjectForm");

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
  // Handle form submission for adding a new subject
  addSubjectForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const subjectName = document.getElementById("subjectName").value;
    const teacherName = document.getElementById("teacherName").value;

    fetch("/add-subject/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": "{{ csrf_token }}",
      },
      body: JSON.stringify({
        subject_name: subjectName,
        teacher_name: teacherName,
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
                <td><input type="number" name="class_score_${data.subject_id}" class="score" min="0" max="100"></td>
            `;

          tableBody.appendChild(newRow);
          modal.style.display = "none";
          addSubjectForm.reset();

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
        } else {
          alert(data.error || "Failed to add subject. Please try again.");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
      });
  });
});

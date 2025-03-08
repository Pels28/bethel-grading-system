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

      console.log("Class Name:", className);

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
                      <td><input type="number" name="score_${data.subject_id}" class="score" min="0" max="100"></td>
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
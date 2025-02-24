function printResults() {
    var printContents = document.body.innerHTML;

    // Hide the navbar before printing
    var navbar = document.querySelector(".nav-links");
    if (navbar) {
        navbar.style.display = "none";
    }

    // Trigger print
    window.print();

    // Restore the navbar after printing
    if (navbar) {
        navbar.style.display = "";
    }
}

function redirectToReport(classSlug, studentId) {
    let semester = document.getElementById("semester").value;
    let academicYear = document.getElementById("academic_year").value;
    
    // Redirect with semester and academic year as query params
    window.location.href = `/students/${classSlug}/view-report/${studentId}/?semester=${semester}&academic_year=${academicYear}`;
}

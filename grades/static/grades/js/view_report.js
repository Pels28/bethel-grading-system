function printReport() {
    const reportContainer = document.querySelector(".report-container"); // Select only the report section
    const originalContents = document.body.innerHTML; // Save the full page content
    const reportContents = reportContainer.innerHTML; // Get only the report content

    document.body.innerHTML = reportContents; // Replace full page with report content
    window.print(); // Trigger print dialog
    document.body.innerHTML = originalContents; // Restore original page after printing
}

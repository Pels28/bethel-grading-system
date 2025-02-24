document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        var message = document.getElementById("success-message");
        if (message) {
            message.style.opacity = "0";
            setTimeout(() => message.style.display = "none", 1000); 
        }
    }, 3000); // Message disappears after 3 seconds
});
// 📌 Sidebar Toggle (for Mobile)
document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.getElementById("sidebar");

    menuToggle.addEventListener("click", function () {
        sidebar.classList.toggle("open");
    });
});

// 📌 Toggle Language Visibility
function toggleLang(lang) {
    document.querySelectorAll(`.${lang}`).forEach(el => {
        el.style.display = (el.style.display === "none") ? "block" : "none";
    });
}

// 📌 Smooth scrolling and blinking effect for commentaries
function highlightCommentary(id) {
    let commentary = document.getElementById(id);
    
    if (commentary) {
        // Scroll smoothly to the commentary
        commentary.scrollIntoView({ behavior: "smooth", block: "center" });

        // Apply blinking effect
        commentary.style.animation = "blink 1s alternate 3";
        
        // Remove animation after blinking is done
        setTimeout(() => commentary.style.animation = "", 3000);
    }
}



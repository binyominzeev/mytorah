document.addEventListener("DOMContentLoaded", function () {
    const chapterIndicator = document.getElementById("chapter-indicator");
    const chapters = document.querySelectorAll(".bilingual-table tr"); // All chapter rows

    function updateChapterIndicator() {
        let currentChapter = null;

        // Loop through all chapter headings
        for (let i = 0; i < chapters.length; i++) {
            const row = chapters[i];
            const hungarianHeading = row.querySelector("td.hungarian h1");

            if (hungarianHeading) {
                const hungarianText = hungarianHeading.innerText.trim();
                const chapterMatch = hungarianText.match(/^(\d+)\. fejezet/);

                if (chapterMatch) {
                    const chapterNumber = chapterMatch[1];
                    const rect = row.getBoundingClientRect();

                    // ✅ If the chapter is at the top OR the closest one above it, update it
                    if (rect.top <= 120) {  
                        currentChapter = chapterNumber;
                    }
                }
            }
        }

        if (currentChapter) {
            chapterIndicator.innerText = "Chapter: " + currentChapter;
            chapterIndicator.classList.remove("hidden");
        } else {
            chapterIndicator.classList.add("hidden"); // Hide when no chapter is detected
        }
    }

    // ✅ Set the first chapter on page load
    function setInitialChapter() {
        for (let row of chapters) {
            const hungarianHeading = row.querySelector("td.hungarian h1");

            if (hungarianHeading) {
                const hungarianText = hungarianHeading.innerText.trim();
                const chapterMatch = hungarianText.match(/^(\d+)\. fejezet/);

                if (chapterMatch) {
                    const firstChapter = chapterMatch[1];
                    chapterIndicator.innerText = "Chapter: " + firstChapter;
                    chapterIndicator.classList.remove("hidden");
                    break; // Stop after finding the first chapter
                }
            }
        }
    }

    window.addEventListener("scroll", updateChapterIndicator);
    setInitialChapter(); // ✅ Show the first chapter immediately
});


// 📌 Toggle Language Visibility
function toggleLang(lang) {
    document.querySelectorAll(`.${lang}`).forEach(el => {
        el.style.display = (el.style.display === "none") ? "block" : "none";
    });
}

// 📌 Smooth scrolling and blinking effect for commentaries
function highlightCommentary(commentaryId) {
    let commentary = document.getElementById(commentaryId);
    
    if (commentary) {
        // Scroll smoothly to the selected commentary
        commentary.scrollIntoView({ behavior: "smooth", block: "center" });

        // Apply blinking highlight effect
        commentary.classList.add("blink");

        // Remove highlight after a short time
        setTimeout(() => {
            commentary.classList.remove("blink");
        }, 1500);
    }
}


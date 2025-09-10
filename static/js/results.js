/** @format */

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const candidateCards = document.querySelectorAll(".candidate-card");

    searchInput.addEventListener("input", () => {
        const searchTerm = searchInput.value.toLowerCase();

        candidateCards.forEach((card) => {
            const candidateName = card.getAttribute("data-name");
            if (candidateName.includes(searchTerm)) {
                card.style.display = "block";
            } else {
                card.style.display = "none";
            }
        });
    });
});
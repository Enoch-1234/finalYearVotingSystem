/** @format */

const sections = document.querySelectorAll(".votes-cards");
const nextBtn = document.getElementById("nextBtn");
const prevBtn = document.getElementById("prevBtn");
let currentIndex = 0;

function updateButtonLabels() {
  nextBtn.textContent = currentIndex === sections.length - 1 ? "Submit" : "Next";
  prevBtn.textContent = "Previous";
  prevBtn.disabled = currentIndex === 0;
  prevBtn.style.display = currentIndex > 0 ? "inline-block" : "none";
  nextBtn.style.display = "inline-block";
}

function showSection(index, direction) {
  sections.forEach((section) => {
    section.classList.remove("active");
    if (direction === "next") {
      section.classList.add("fade-out-left");
    } else if (direction === "prev") {
      section.classList.add("fade-out-right");
    }
  });

  setTimeout(() => {
    sections.forEach((section) => {
      section.classList.remove("fade-out-left", "fade-out-right");
    });
    sections[index].classList.add("active");
    updateButtonLabels();

    const activeRadios = sections[index].querySelectorAll('input[type="radio"]');
    activeRadios.forEach((radio) => {
      radio.addEventListener("change", () => {
        nextBtn.style.display = "inline-block";
        prevBtn.style.display = currentIndex > 0 ? "inline-block" : "none";
      });
    });
  }, 500);
}

// Initialize the first section
showSection(currentIndex, null);

nextBtn.addEventListener("click", () => {
  if (currentIndex < sections.length - 1) {
    const currentSection = sections[currentIndex];
    const selected = currentSection.querySelector('input[type="radio"]:checked');
    if (!selected) {
      alert("Please select a candidate before proceeding.");
      return;
    }
    currentIndex++;
    showSection(currentIndex, "next");
  } else {
    const allSelected = Array.from(sections).every((section) =>
      section.querySelector('input[type="radio"]:checked')
    );
    if (!allSelected) {
      alert("Please vote in all categories before submitting.");
      return;
    }
    document.querySelector("form").submit();
  }
});

prevBtn.addEventListener("click", () => {
  if (currentIndex > 0) {
    currentIndex--;
    showSection(currentIndex, "prev");
  }
});

const totalVotesDivs = document.querySelectorAll(".total-votes .card");
totalVotesDivs.forEach((div) => {
  div.addEventListener("click", (e) => {
    if (e.target.tagName !== "INPUT") {
      const radio = div.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        nextBtn.style.display = "inline-block";
        prevBtn.style.display = currentIndex > 0 ? "inline-block" : "none";
      }
    }
  });
});
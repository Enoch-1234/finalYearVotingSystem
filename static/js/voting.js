// static/js/voting.js
document.addEventListener('DOMContentLoaded', function () {
  const sections = document.querySelectorAll('.category-section');
  let currentIndex = 0;

  function showSection(index) {
    sections.forEach((section, i) => {
      section.classList.toggle('active', i === index);
    });
  }

  document.getElementById('nextBtn').addEventListener('click', () => {
    if (currentIndex < sections.length - 1) {
      currentIndex++;
      showSection(currentIndex);
    }
  });

  document.getElementById('prevBtn').addEventListener('click', () => {
    if (currentIndex > 0) {
      currentIndex--;
      showSection(currentIndex);
    }
  });

  showSection(currentIndex);
});

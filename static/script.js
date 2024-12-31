function toggleAnswer(button) {
  const targetId = button.getAttribute('data-target');
  const answerBox = document.getElementById(targetId);

  answerBox.classList.toggle('hidden');
  button.innerText = button.innerText.replace(/Show|Hide/, match => match === 'Show' ? 'Hide' : 'Show');
}

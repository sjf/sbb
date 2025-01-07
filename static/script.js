function toggleVisible(button) {
  // Click to show/hide any associated div.
  const targetId = button.getAttribute('data-target');
  const target = document.getElementById(targetId);
  target.classList.toggle('hidden');
  button.innerText = button.innerText.replace(/Show|Hide/, match => match === 'Show' ? 'Hide' : 'Show');

  const oppositeButtonId = button.getAttribute('data-opposite-button');
  const oppositeButton = document.getElementById(oppositeButtonId);
  hide(oppositeButton);
}

function hide(button) {
  if (button.innerText.startsWith('Hide')) {
    const targetId = button.getAttribute('data-target');
    const target = document.getElementById(targetId);
    target.classList.add('hidden');
    button.innerText = button.innerText.replace(/Hide/, 'Show');
  }
}

function revealAnswer(element) {
  // On the game page, reveals the answer for a clue.
  const answer = element.getAttribute('data-answer');  // Get the full answer
  const emptyBoxes = element.querySelectorAll('.empty-box');

  // Fill the empty boxes starting from the second letter
  for (let i = 0; i < emptyBoxes.length; i++) {
    emptyBoxes[i].textContent = answer[i+1];
  }
}

function toggleClueAnswer(element) {
  // On the clue page, reveals the answer.
  const answer = element.getAttribute('data-answer');
  const emptyBoxes = element.querySelectorAll('.empty-box');
  const filledBoxes = element.querySelectorAll('.filled-box');
  const definition = document.getElementById(element.dataset.definition);

  emptyBoxes.forEach((box, index) => {
    box.textContent = answer[index + 1];  // Fill box with letter
    box.classList.remove('empty-box');
    box.classList.add('filled-box');
  });

  filledBoxes.forEach((box, index) => {
    box.textContent = '';
    box.classList.add('empty-box');
    box.classList.remove('filled-box');
  });

  definition.classList.toggle('hidden');
}

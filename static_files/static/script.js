function toggleVisible(button) {
  // Click to show/hide any associated div.
  const targetId = button.getAttribute('data-target');
  const target = document.getElementById(targetId);
  target.classList.toggle('hidden');
  replaceText(button, /Show|Hide/, match => match === 'Show' ? 'Hide' : 'Show');
  replaceText(button, /▶|▼/, match => match === '▶' ? '▼' : '▶');

  const oppositeId = button.getAttribute('data-opposite-button');
  if (oppositeId) {
    const oppositeButton = document.getElementById(oppositeId);
    // Just always hide it, even if this toggle is also hidding the target.
    hide(oppositeButton);
  }
}

function hide(button) {
  const targetId = button.getAttribute('data-target');
  const target = document.getElementById(targetId);
  target.classList.add('hidden');
  replaceText(button, /Hide/, 'Show');
  replaceText(button, /▶/, '▼');
}

function toggleClueAnswer(element) {
  const emptyBoxes = element.querySelectorAll('.empty-box');
  const filledBoxes = element.querySelectorAll('.filled-box');
  const icons = element.querySelectorAll('.eye');
  const definition = document.getElementById(element.dataset.definition);

  emptyBoxes.forEach((box, index) => {
    box.textContent = box.getAttribute('data-letter');
    box.classList.remove('empty-box');
    box.classList.add('filled-box');
  });

  filledBoxes.forEach((box, index) => {
    box.textContent = '';
    box.classList.add('empty-box');
    box.classList.remove('filled-box');
  });

  icons.forEach((icon, index) => {
    icon.classList.toggle('hidden');
  });

  if (definition) {
    definition.classList.toggle('hidden');
  }
}

function toggleHintAnswers(element) {
  const targetId = element.getAttribute('data-target');
  const answers = document.getElementById(targetId);
  if (answers.classList.contains('hidden')) {
    answers.classList.remove('hidden');
    setTimeout(() => answers.classList.add('opacity-100'), 10);
  } else {
    answers.classList.remove('opacity-100');
    answers.classList.add('opacity-0');
    // Wait for transition to finish before hiding the element
    setTimeout(() => answers.classList.add('hidden'), 300);
  }

  let icons = element.querySelectorAll('.eye');
  if (icons.length === 0) {
    icons = element.nextElementSibling.querySelectorAll('.eye');
  }
  icons.forEach((icon, index) => {
    icon.classList.toggle('hidden');
  });
}

function ffocus(id) {
  document.getElementById(id).focus();
}

function replaceText(e, pattern, f) {
  let span = e.querySelector("span");
  if (span) {
    span.textContent = span.textContent.replace(pattern, f);
  }
}

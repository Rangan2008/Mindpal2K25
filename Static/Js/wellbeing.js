// wellbeing.js

document.addEventListener("DOMContentLoaded", () => {
  const bubble = document.getElementById("bubble");
  const breathingInstruction = document.getElementById("breathing-instruction");
  const quote = document.getElementById("daily-quote");
  const journalContent = document.getElementById("journal-content");
  const saveJournalBtn = document.getElementById("save-journal-btn");
  const journalStatus = document.getElementById("journal-status");

  // Breathing animation
  window.startBreathing = function () {
    if (breathingInstruction) {
      breathingInstruction.style.display = 'block';
    }
    bubble.animate([
      { transform: "scale(1)" },
      { transform: "scale(1.6)" },
      { transform: "scale(1)" }
    ], {
      duration: 8000,
      iterations: Infinity
    });
  };

  // Fetch a motivational quote
  fetch("https://api.quotable.io/random?tags=motivational|inspirational")
    .then(res => res.json())
    .then(data => {
      quote.textContent = `"${data.content}" — ${data.author}`;
    })
    .catch(() => {
      quote.textContent = "You're doing great. Keep going!";
    });

  // Journal functionality
  if (saveJournalBtn && journalContent) {
    saveJournalBtn.addEventListener('click', saveJournalEntry);
    
    // Auto-resize textarea
    journalContent.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = this.scrollHeight + 'px';
    });
  }

  function saveJournalEntry() {
    const content = journalContent.value.trim();
    
    if (!content) {
      showJournalStatus('Please write something before saving!', 'error');
      return;
    }

    // Get current mood if selected
    const moodSelect = document.getElementById('mood-select');
    const currentMood = moodSelect ? moodSelect.value : null;

    // Show saving state
    showJournalStatus('Saving your entry...', 'saving');
    saveJournalBtn.disabled = true;

    // Send to backend
    fetch('/api/journal/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: content,
        mood: currentMood
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showJournalStatus('✨ Entry saved successfully!', 'success');
        journalContent.value = ''; // Clear the textarea
        journalContent.style.height = 'auto'; // Reset height
      } else {
        throw new Error(data.error || 'Failed to save entry');
      }
    })
    .catch(error => {
      console.error('Error saving journal entry:', error);
      showJournalStatus('Failed to save entry. Please try again.', 'error');
    })
    .finally(() => {
      saveJournalBtn.disabled = false;
    });
  }

  function showJournalStatus(message, type) {
    journalStatus.textContent = message;
    journalStatus.className = `journal-status ${type}`;
    
    // Clear status after 3 seconds for success/error, keep saving status
    if (type !== 'saving') {
      setTimeout(() => {
        journalStatus.textContent = '';
        journalStatus.className = 'journal-status';
      }, 3000);
    }
  }
});


    const tips = [
      "Drink a glass of water slowly.",
      "Take a 5-minute walk outside.",
      "Stretch your arms and legs.",
      "Write down 3 things you love.",
      "Listen to calming music."
    ];
    let tipIndex = 0;

    function nextTip() {
      tipIndex = (tipIndex + 1) % tips.length;
      document.getElementById("tip-display").textContent = tips[tipIndex];
    }

    let gratCount = 0;
    function incrementGratitude() {
      gratCount++;
      document.getElementById("grat-count").textContent = gratCount;
    }
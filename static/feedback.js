function feedbackClean(text) {
  return String(text || "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}

function feedbackStarsHtml(rating) {
  const value = Math.max(0, Math.min(5, Number(rating) || 0));
  return Array.from({ length: 5 }, (_, index) => `<span class="fb-star ${index < value ? "filled" : ""}">&#9733;</span>`).join("");
}

function feedbackFormatDate(isoString) {
  if (!isoString) return "";
  try {
    return new Date(isoString).toLocaleString("en-IN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit"
    });
  } catch {
    return "";
  }
}

async function feedbackRequestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) }
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong. Please try again.");
  }
  return data;
}

async function loadFeedbackList() {
  const list = document.getElementById("feedbackList");
  if (!list) return;
  try {
    const entries = await feedbackRequestJson("/api/feedback");
    list.innerHTML = entries.length ? entries.map(entry => `
      <article class="feedback-item">
        <div class="feedback-item-head">
          <strong>${feedbackClean(entry.playerName)}</strong>
          <span class="feedback-stars">${feedbackStarsHtml(entry.rating)}</span>
        </div>
        <span class="feedback-item-date">${feedbackFormatDate(entry.createdAt)}</span>
        ${entry.message ? `<p>${feedbackClean(entry.message)}</p>` : ""}
      </article>
    `).join("") : `<p class="feedback-empty">No feedback yet. Be the first to share yours!</p>`;
  } catch (error) {
    list.innerHTML = `<p class="feedback-empty">${feedbackClean(error.message)}</p>`;
  }
}

function initFeedbackForm() {
  const form = document.getElementById("feedbackForm");
  const starsWrap = document.getElementById("feedbackStars");
  const formMessage = document.getElementById("feedbackFormMessage");
  if (!form || !starsWrap) return;

  let selectedRating = 0;
  const starButtons = Array.from(starsWrap.querySelectorAll(".star"));

  function paintStars(rating) {
    starButtons.forEach(button => {
      button.classList.toggle("active", Number(button.dataset.star) <= rating);
    });
  }

  starButtons.forEach(button => {
    button.addEventListener("click", () => {
      selectedRating = Number(button.dataset.star);
      paintStars(selectedRating);
    });
    button.addEventListener("mouseenter", () => paintStars(Number(button.dataset.star)));
  });
  starsWrap.addEventListener("mouseleave", () => paintStars(selectedRating));

  form.addEventListener("submit", async event => {
    event.preventDefault();
    formMessage.textContent = "";

    const playerName = document.getElementById("feedbackName").value.trim();
    const message = document.getElementById("feedbackMessage").value.trim();

    if (!playerName) {
      formMessage.textContent = "Please enter your player name.";
      return;
    }
    if (!selectedRating) {
      formMessage.textContent = "Please select a star rating.";
      return;
    }

    const submitButton = form.querySelector(".feedback-submit");
    submitButton.disabled = true;
    submitButton.textContent = "Submitting...";

    try {
      await feedbackRequestJson("/api/feedback", {
        method: "POST",
        body: JSON.stringify({ player_name: playerName, rating: selectedRating, message })
      });
      form.reset();
      selectedRating = 0;
      paintStars(0);
      formMessage.textContent = "Thanks for your feedback!";
      await loadFeedbackList();
    } catch (error) {
      formMessage.textContent = error.message;
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Submit Feedback";
    }
  });
}

initFeedbackForm();
loadFeedbackList();

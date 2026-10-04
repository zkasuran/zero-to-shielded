// pages/guard.js: Phrase Guard. One situation at a time, Safe or Scam, instant feedback.
import { burst } from "../fx.js";

const root = document.querySelector("[data-guard]");
if (root) init(root);

function init(root) {
  const cards = [...root.querySelectorAll("[data-gq]")];
  const dots = [...root.querySelectorAll(".guard-dots li")];
  const picks = [...root.querySelectorAll("[data-g-pick]")];
  const actions = root.querySelector("[data-g-actions]");
  const next = root.querySelector("[data-g-next]");
  const feedback = root.querySelector("[data-g-feedback]");
  const scoreEl = root.querySelector("[data-g-score]");
  const end = root.querySelector("[data-g-end]");
  const finalEl = root.querySelector("[data-g-final]");
  const msg = root.querySelector("[data-g-msg]");
  let i = 0;
  let score = 0;

  root.classList.add("is-live");

  function show() {
    cards.forEach((c, j) => {
      c.classList.toggle("is-current", j === i);
      c.classList.remove("is-answered", "is-right", "is-wrong");
    });
    dots.forEach((d, j) => d.classList.toggle("is-here", j === i));
    picks.forEach((p) => { p.disabled = false; p.classList.remove("is-chosen"); });
    actions.hidden = false;
    end.hidden = true;
    feedback.textContent = "";
    feedback.className = "guard-feedback";
    next.hidden = true;
  }

  function restart() {
    i = 0;
    score = 0;
    scoreEl.textContent = "0";
    dots.forEach((d) => d.classList.remove("is-right", "is-wrong"));
    root.classList.remove("is-over");
    next.textContent = "Next";
    show();
    cards[0].querySelector(".gq-text")?.focus?.();
  }

  picks.forEach((p) => p.addEventListener("click", () => {
    const card = cards[i];
    const right = p.dataset.gPick === card.dataset.answer;
    picks.forEach((x) => (x.disabled = true));
    p.classList.add("is-chosen");
    card.classList.add("is-answered", right ? "is-right" : "is-wrong");
    dots[i].classList.add(right ? "is-right" : "is-wrong");
    if (right) score += 1;
    scoreEl.textContent = String(score);
    feedback.className = `guard-feedback ${right ? "is-right" : "is-wrong"}`;
    feedback.textContent = right ? "Right." : "Not quite. Read why above.";
    next.textContent = i === cards.length - 1 ? "See your score" : "Next";
    next.hidden = false;
    next.focus({ preventScroll: true });
  }));

  next.addEventListener("click", () => {
    if (root.classList.contains("is-over")) { restart(); return; }
    if (i < cards.length - 1) { i += 1; show(); return; }
    root.classList.add("is-over");
    cards.forEach((c) => c.classList.remove("is-current"));
    actions.hidden = true;
    end.hidden = false;
    finalEl.textContent = String(score);
    msg.textContent = score === cards.length
      ? "Perfect. Your phrase is safe with you."
      : score >= 4
        ? "Good. Read the ones you missed once more."
        : "Worth another go. Your phrase is the one thing that must stay yours.";
    feedback.textContent = "";
    next.textContent = "Try again";
    if (score === cards.length) burst(root, { count: 80 });
  });

  show();
}

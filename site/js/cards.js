// cards.js: mark an episode card "Done" once every step it teaches is ticked.
import { EPISODES } from "./episodes.js";
import { readProgress, onProgress } from "./store.js";

export function initEpisodeCards() {
  const cards = [...document.querySelectorAll(".ep-card[data-ep]")];
  if (!cards.length) return;
  const paint = (done) => {
    for (const card of cards) {
      const e = EPISODES.find((x) => x.id === card.dataset.ep);
      const chip = card.querySelector("[data-ep-done]");
      if (!e || !chip) continue;
      chip.hidden = !(e.steps.length && e.steps.every((s) => done.has(s)));
    }
  };
  paint(readProgress());
  onProgress((done) => paint(done));
}

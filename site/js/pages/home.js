// pages/home.js: hero field, hero player and the "done" chips on episode cards.
import { heroField } from "../hero-field.js";
import { initPlayers } from "../player.js";
import { initEpisodeCards } from "../cards.js";

const hero = document.querySelector("#hero");
if (hero) heroField(hero.querySelector("[data-hero-field]"), hero);
initPlayers(document.querySelector("#hero") || document);
initEpisodeCards();

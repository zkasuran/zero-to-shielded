// player.js: behaviour for the players rendered by markup.js.
// YouTube loads only after a click (a facade), from youtube-nocookie.com, and the iframe
// sends the origin as referrer because the YouTube embed refuses to play without one.

const YT_ID = /^[A-Za-z0-9_-]{11}$/;

function ytSrc(id, start = 0, autoplay = true) {
  const p = new URLSearchParams({ rel: "0", playsinline: "1", modestbranding: "1" });
  if (autoplay) p.set("autoplay", "1");
  if (start > 0) p.set("start", String(Math.floor(start)));
  return `https://www.youtube-nocookie.com/embed/${id}?${p}`;
}

export function makePlayer(el) {
  if (!el) return null;
  const mode = el.dataset.mode;
  const listeners = new Set();
  const api = { el, mode, canSeek: mode === "video" || mode === "youtube", seek() {}, onTime(fn) { listeners.add(fn); } };

  if (mode === "video") {
    const video = el.querySelector("video");
    api.seek = (t) => {
      try {
        video.currentTime = t;
        const p = video.play();
        if (p && p.catch) p.catch(() => {});
      } catch { /* not seekable yet */ }
    };
    video.addEventListener("timeupdate", () => listeners.forEach((fn) => fn(video.currentTime)));
  }

  if (mode === "youtube") {
    const id = el.dataset.youtube;
    if (!YT_ID.test(id || "")) return api;
    const title = el.querySelector("[data-yt-play]")?.getAttribute("aria-label") || "Video";
    const mount = (start) => {
      let frame = el.querySelector("iframe");
      if (!frame) {
        el.replaceChildren();
        frame = document.createElement("iframe");
        frame.title = title.replace(/\. Loads.*$/, "");
        frame.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
        frame.allowFullscreen = true;
        frame.referrerPolicy = "strict-origin-when-cross-origin";
        frame.loading = "eager";
        el.appendChild(frame);
      }
      frame.src = ytSrc(id, start);
    };
    el.querySelector("[data-yt-play]")?.addEventListener("click", () => mount(0));
    api.seek = (t) => mount(t);
  }
  return api;
}

export function initPlayers(scope = document) {
  return [...scope.querySelectorAll("[data-player]")].map(makePlayer);
}

// nav.js: the category menu. One state source (`openId`) drives every submenu; the DOM
// is only ever painted from it. Submenus open on mouse hover, keyboard focus and tap or
// click. Escape closes and returns focus. Under 960px the same markup becomes the
// hamburger panel and the categories work as an accordion.

export function initNav() {
  const nav = document.querySelector(".nav");
  if (!nav) return;
  const header = document.querySelector(".site-header");
  const menuBtn = document.querySelector("[data-menu-toggle]");
  const items = [...nav.querySelectorAll("[data-nav-item]")];
  const mobile = matchMedia("(max-width: 959px)");
  const root = document.documentElement;

  let openId = null;
  let openedBy = null;
  let openedAt = 0;
  let menuOpen = false;
  let timer = 0;
  let quiet = false; // true while focus is handed back after Escape, so it does not reopen

  const triggerOf = (id) => nav.querySelector(`[data-nav-item="${id}"] .nav-trigger`);

  function paint() {
    for (const item of items) {
      const on = item.dataset.navItem === openId;
      item.classList.toggle("is-open", on);
      item.querySelector(".nav-trigger").setAttribute("aria-expanded", String(on));
    }
    root.classList.toggle("menu-open", menuOpen);
    if (menuBtn) {
      menuBtn.setAttribute("aria-expanded", String(menuOpen));
      menuBtn.setAttribute("aria-label", menuOpen ? "Close menu" : "Open menu");
    }
  }

  function setOpen(id, by = null) {
    clearTimeout(timer);
    if (id !== openId) { openedBy = by; openedAt = performance.now(); }
    openId = id;
    paint();
  }

  function closeSoon() {
    clearTimeout(timer);
    timer = setTimeout(() => setOpen(null), 200);
  }

  function setMenu(open) {
    menuOpen = open;
    if (!open) openId = null;
    else if (!openId) {
      const current = items.find((i) => i.querySelector(".nav-trigger.is-current"));
      openId = current ? current.dataset.navItem : null;
    }
    paint();
  }

  for (const item of items) {
    const id = item.dataset.navItem;
    const trigger = item.querySelector(".nav-trigger");

    item.addEventListener("pointerenter", (e) => {
      if (e.pointerType === "mouse" && !mobile.matches) setOpen(id, "hover");
    });
    item.addEventListener("pointerleave", (e) => {
      if (e.pointerType === "mouse" && !mobile.matches && openId === id) closeSoon();
    });

    trigger.addEventListener("click", () => {
      // A mouse that just opened this by hovering should not close it with the click.
      const fresh = openedBy === "hover" && performance.now() - openedAt < 700;
      if (openId === id && !fresh) setOpen(null);
      else setOpen(id, "click");
    });

    // keyboard focus opens (a mouse click focus does not match :focus-visible)
    item.addEventListener("focusin", (e) => {
      if (mobile.matches || quiet) return;
      if (e.target === trigger && !trigger.matches(":focus-visible")) return;
      setOpen(id, "focus");
    });
    item.addEventListener("focusout", (e) => {
      if (mobile.matches) return;
      if (!item.contains(e.relatedTarget) && openId === id) setOpen(null);
    });

    trigger.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setOpen(id, "key");
        const first = item.querySelector(".nav-panel a");
        if (first) first.focus();
      }
    });
    item.querySelector(".nav-panel").addEventListener("keydown", (e) => {
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      const links = [...item.querySelectorAll(".nav-panel a")];
      const i = links.indexOf(document.activeElement);
      if (i < 0) return;
      e.preventDefault();
      const next = e.key === "ArrowDown" ? (i + 1) % links.length : (i - 1 + links.length) % links.length;
      links[next].focus();
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (openId && !mobile.matches) {
      const t = triggerOf(openId);
      setOpen(null);
      quiet = true;
      if (t) t.focus();
      quiet = false;
    } else if (menuOpen) {
      setMenu(false);
      if (menuBtn) menuBtn.focus();
    }
  });

  document.addEventListener("click", (e) => {
    if (openId && !mobile.matches && !nav.contains(e.target)) setOpen(null);
    if (menuOpen && header && !header.contains(e.target)) setMenu(false);
  });

  nav.addEventListener("click", (e) => {
    if (e.target.closest("a")) { menuOpen = false; openId = null; paint(); }
  });

  if (menuBtn) menuBtn.addEventListener("click", () => setMenu(!menuOpen));
  mobile.addEventListener("change", () => { menuOpen = false; openId = null; paint(); });

  // header shadow once the page scrolls
  if (header) {
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        header.classList.toggle("is-scrolled", window.scrollY > 4);
        ticking = false;
      });
    };
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  nav.setAttribute("data-nav-ready", "");
  paint();
}

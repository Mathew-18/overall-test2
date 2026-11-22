(() => {
  const header = document.querySelector(".dh-header");
  if (!header) return;
  header.classList.add("dh-enhanced");
  const toggle = header.querySelector(".dh-toggle");
  const services = header.querySelector(".dh-services");
  const summary = services.querySelector("summary");
  const mobile = window.matchMedia("(max-width: 991px)");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const controls = [...header.querySelectorAll("[data-dh-nav]")];
  const active = controls.find(control => control.hasAttribute("data-dh-active"));

  function updateElevation() {
    header.classList.toggle("dh-scrolled", scrollY > 8);
  }
  window.addEventListener("scroll", updateElevation, { passive: true });
  updateElevation();

  function reflectDisclosure() {
    summary.setAttribute("aria-expanded", String(services.open));
  }
  services.addEventListener("toggle", reflectDisclosure);
  reflectDisclosure();

  function setMenu(open) {
    toggle.setAttribute("aria-expanded", String(open));
    header.querySelector("#dh-menu").inert = mobile.matches && !open;
    if (!open) services.open = false;
  }

  function resetLayout() {
    const focused = document.activeElement;
    toggle.hidden = !mobile.matches;
    if (mobile.matches && focused.closest("#dh-menu")) toggle.focus();
    if (!mobile.matches && services.open && focused.closest("#dh-service-links")) summary.focus();
    setMenu(false);
    if (!mobile.matches && focused === toggle) (active || summary).focus();
  }

  toggle.addEventListener("click", () => {
    setMenu(toggle.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("click", event => {
    if (!services.contains(event.target)) services.open = false;
    if (!header.contains(event.target)) setMenu(false);
  });

  header.addEventListener("keydown", event => {
    if (event.key === "ArrowDown" && event.target === summary) {
      event.preventDefault();
      services.open = true;
      // Wait until the native disclosure has exposed the panel to focus.
      requestAnimationFrame(() => {
        if (services.open && document.activeElement === summary) {
          services.querySelector("a").focus();
        }
      });
    }
    if (event.key !== "Escape") return;
    if (services.open) {
      summary.focus();
      services.open = false;
    } else if (mobile.matches && toggle.getAttribute("aria-expanded") === "true") {
      toggle.focus();
      setMenu(false);
    }
  });

  header.addEventListener("focusout", event => {
    if (!event.relatedTarget) return;
    if (!services.contains(event.relatedTarget)) services.open = false;
    if (!header.contains(event.relatedTarget)) setMenu(false);
  });

  mobile.addEventListener("change", resetLayout);
  window.addEventListener("pageshow", event => { if (event.persisted) resetLayout(); });
  resetLayout();

  // Remember the departing section for same-tab navigation across static documents.
  const storageKey = "dh-navigation-transition";

  function animateIndicator() {
    let arrival;
    try {
      arrival = JSON.parse(sessionStorage.getItem(storageKey));
      sessionStorage.removeItem(storageKey);
    } catch {
      return;
    }
    if (reducedMotion.matches || mobile.matches || arrival?.path !== location.pathname) return;
    const from = controls.find(control => control.dataset.dhNav === arrival.section);
    const line = active.querySelector(".dh-indicator");
    if (!from || from === active || !line?.animate) return;
    const oldRect = from.getBoundingClientRect();
    const newRect = active.getBoundingClientRect();
    // Both indicator edges are inset by the same amount on every desktop item.
    const fromWidth = oldRect.width - 24;
    const toWidth = newRect.width - 24;
    line.animate([
      { transform: `translateX(${oldRect.left - newRect.left}px) scaleX(${fromWidth / toWidth})` },
      { transform: "none" },
    ], { duration: 460, easing: "cubic-bezier(.22, 1, .36, 1)" });
  }

  if (!active) return;
  const indicator = document.createElement("span");
  indicator.className = "dh-indicator";
  indicator.setAttribute("aria-hidden", "true");
  active.append(indicator);
  animateIndicator();

  document.addEventListener("click", event => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey ||
        event.altKey || event.shiftKey || reducedMotion.matches || mobile.matches) return;
    const link = event.target.closest("a[href]");
    if (!link || link.hasAttribute("download") || (link.target && link.target !== "_self")) return;
    const destination = new URL(link.href);
    if (destination.origin !== location.origin || destination.pathname === location.pathname) return;
    try {
      sessionStorage.setItem(storageKey, JSON.stringify({
        path: destination.pathname, section: active.dataset.dhNav,
      }));
    } catch {
      // The active style is rendered on the destination even without storage.
    }
  });
})();

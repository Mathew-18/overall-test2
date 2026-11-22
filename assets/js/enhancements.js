(() => {
  "use strict";
  const main = document.querySelector("main");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  function enableButton(node, callback) {
    node.setAttribute("role", "button");
    node.tabIndex = 0;
    node.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        node.click();
      }
    });
    if (callback) node.addEventListener("click", callback);
  }

  // Keep the page's original accordion animation and expose its actual state.
  main.querySelectorAll(".faq-item").forEach((item, index) => {
    const question = item.querySelector(".faq-q");
    const answer = item.querySelector(".faq-a");
    if (!question || !answer) return;
    answer.id ||= "faq-answer-" + (index + 1);
    enableButton(question);
    question.setAttribute("aria-controls", answer.id);
    function reflect() {
      const open = item.classList.contains("active");
      question.setAttribute("aria-expanded", String(open));
      answer.inert = !open;
    }
    reflect();
    new MutationObserver(reflect).observe(item, {attributes: true, attributeFilter: ["class"]});
  });

  for (const button of main.querySelectorAll(".gal-btn, .filter-btn, .est-opt")) {
    const sync = () => button.setAttribute("aria-pressed", String(button.classList.contains("active")));
    sync();
    new MutationObserver(sync).observe(button, {attributes: true, attributeFilter: ["class"]});
  }

  // Reuse the exact in-page image for display at its original source resolution.
  let viewer;
  function openViewer(trigger, title, content) {
    if (!viewer) {
      viewer = document.createElement("dialog");
      viewer.className = "dh-view";
      document.body.append(viewer);
      viewer.addEventListener("click", event => {
        if (event.target === viewer) viewer.close();
      });
    }
    const caption = document.createElement("p");
    caption.textContent = title;
    caption.id = "dh-view-caption";
    viewer.setAttribute("aria-labelledby", caption.id);
    const close = document.createElement("button");
    close.type = "button";
    close.textContent = "Close";
    close.addEventListener("click", () => viewer.close());
    viewer.replaceChildren(content, caption, close);
    viewer.addEventListener("close", () => trigger.focus({preventScroll:true}), {once:true});
    viewer.showModal();
    close.focus({preventScroll:true});
  }
  for (const tile of main.querySelectorAll(".gal-item,.proj-img,.mat-img")) {
    const image = tile.querySelector("img");
    if (!image || tile.querySelector("a, button")) continue;
    const caption = tile.textContent.trim() || image.alt || "Project image";
    tile.setAttribute("aria-label", "Enlarge " + caption);
    tile.setAttribute("aria-haspopup", "dialog");
    tile.dataset.photoView = "";
    // The named enlargement control already describes its thumbnail.
    image.setAttribute("aria-hidden", "true");
    enableButton(tile, () => {
      const full = new Image();
      full.alt = image.alt || caption;
      full.src = image.currentSrc || image.src;
      openViewer(tile, caption, full);
    });
  }
  for (const link of main.querySelectorAll(".proj-card-foot a")) {
    const card = link.closest(".proj-card");
    const details = card.querySelector(".proj-card-body");
    if (!details || !link.href.startsWith("tel:")) continue;
    link.setAttribute("aria-haspopup","dialog");
    link.addEventListener("click", event => {
      event.preventDefault();
      const copy = details.cloneNode(true);
      const call = document.createElement("a");
      call.href = link.href;
      call.textContent = "Call about this project";
      copy.append(call);
      openViewer(link, card.querySelector("h4").textContent.trim(), copy);
    });
  }

  // About originally prints these totals. Animate their numeric text only;
  // the original suffix, value and adjacent label remain in the document.
  if (reduced.matches) {
    for (const stat of main.querySelectorAll("[data-count], .counter[data-target]")) {
      const value = Number(stat.dataset.count || stat.dataset.target);
      stat.textContent = value >= 1000 ? value.toLocaleString("en-IN") : String(value);
    }
  }
  const stats = main.querySelectorAll("#stats .stat-num");
  if (stats.length && !reduced.matches && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const stat = entry.target;
        observer.unobserve(stat);
        const number = stat.firstChild;
        const end = Number(number.textContent);
        if (!Number.isFinite(end)) continue;
        const start = performance.now();
        function tick(now) {
          const progress = reduced.matches ? 1 : Math.min(1, (now - start) / 850);
          number.textContent = Math.round(end * (1 - (1 - progress) ** 3));
          if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      }
    }, {threshold: .25});
    stats.forEach(stat => observer.observe(stat));
  }
})();

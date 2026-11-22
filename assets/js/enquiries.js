/* Drafts stay in page memory until the visitor chooses the WhatsApp handoff. */
(() => {
  "use strict";

  function validate(control) {
    control.setCustomValidity("");
    const value = control.value.trim();
    if (control.required && !value) control.setCustomValidity("Complete this field to continue.");
    if (control.type === "tel" && value) {
      const digits = value.replace(/[\s().-]/g, "");
      // Accept ten-digit local mobiles or an international number with a country code.
      if (!/^(?:\d{10}|\+?[1-9]\d{10,14})$/.test(digits) || /^0+$/.test(digits)) {
        control.setCustomValidity("Enter a 10-digit mobile number or include the country code.");
      }
    }
  }

  function draftURL(base, subject, entries) {
    const url = new URL(base);
    const lines = entries.filter(([, value]) => value).map(([label, value]) => label + ": " + value);
    url.searchParams.set("text", ["Hello DH Construction,", subject, "", ...lines].join("\n"));
    return url.href;
  }

  function handoff(button, status, url) {
    button.disabled = true;
    // Some browsers return null for a successful noopener launch as well as a blocked one.
    try {
      window.open(url, "_blank", "noopener,noreferrer");
    } catch {
      // Keep the same user-initiated, accessible draft link in restricted browsers.
    }
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "open your draft here";
    status.replaceChildren("Your draft is ready. If WhatsApp did not open, ", link, ". Press Send in WhatsApp to share it.");
  }

  document.querySelectorAll(".dh-enquiry").forEach(form => {
    const fieldset = form.querySelector("fieldset");
    const controls = Array.from(form.querySelectorAll("[data-label]"));
    const button = form.querySelector('[type="submit"]');
    const status = form.querySelector('[role="status"]');
    form.addEventListener("input", event => {
      if (controls.includes(event.target)) validate(event.target);
      button.disabled = false;
      status.replaceChildren();
    });
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (button.disabled) return;
      controls.forEach(validate);
      if (!form.reportValidity()) return;
      const entries = controls.map(control => [control.dataset.label, control.value.trim()]);
      handoff(button, status, draftURL(form.dataset.whatsapp, form.dataset.enquiry, entries));
    });
    form.querySelector(".dh-enquiry-direct").hidden = true;
    fieldset.disabled = false;
  });

  const assistant = document.querySelector(".dh-guide");
  if (!assistant) return;
  const fields = [
    { label: "Service", question: "Hi! What kind of work are you planning?", options: ["New Construction", "Home Renovation", "Interior Design", "Painting", "Plumbing", "Electrical Work", "Other Services"] },
    { label: "Property type", question: "And what kind of property is this for?", options: ["Residential", "Commercial", "Other"] },
    { label: "Location", question: "Where is the property?", type: "text", hint: "Area or locality" },
    { label: "Requirements", question: "What would you like us to work on?", type: "textarea", hint: "Describe the work you have in mind" },
    { label: "Expected budget", question: "Do you have a budget in mind?", type: "text", hint: "An estimate is fine", optional: true },
    { label: "Preferred start", question: "When would you like to start?", options: ["Immediately", "Within one month", "Within three months", "Just exploring"] },
    { label: "Name", question: "What is your name?", type: "text", autocomplete: "name" },
    { label: "Mobile", question: "What is your mobile number?", type: "tel", autocomplete: "tel", hint: "10 digits or include the country code" },
  ];
  const panel = assistant.querySelector('[role="dialog"]');
  const welcome = assistant.querySelector(".dh-guide-welcome");
  const launch = assistant.querySelector(".dh-guide-launch");
  const body = assistant.querySelector(".dh-guide-body");
  let step = 0;
  let editing = false;
  let answers = fields.map(() => "");
  let consent = false;
  let shared = false;

  let closing = false;
  const motion = window.matchMedia("(prefers-reduced-motion: reduce)");

  async function hide(reset) {
    if (closing) return;
    closing = true;
    panel.inert = true;
    if (!motion.matches && panel.animate) {
      await panel.animate([
        {opacity: 1, transform: "translateY(0)"},
        {opacity: 0, transform: "translateY(8px)"},
      ], {duration: 120, easing: "ease-in"}).finished;
    }
    panel.hidden = true;
    panel.inert = false;
    closing = false;
    launch.hidden = false;
    launch.setAttribute("aria-expanded", "false");
    if (reset) {
      answers = fields.map(() => "");
      consent = shared = editing = false;
      step = 0;
      body.replaceChildren();
    }
    launch.focus();
  }
  function element(tag, text, className) {
    const el = document.createElement(tag);
    if (text) el.textContent = text;
    if (className) el.className = className;
    return el;
  }
  function action(label, run, className) {
    const button = element("button", label, className);
    button.type = "button";
    button.addEventListener("click", run);
    return button;
  }

  function draw() {
    body.replaceChildren();
    if (step === fields.length) {
      const title = element("h2", "Review your enquiry");
      title.tabIndex = -1;
      const list = element("dl", "", "dh-guide-summary");
      fields.forEach(({ label }, index) => {
        const term = element("dt", label);
        const edit = action("Edit", () => {
          step = index;
          editing = true;
          draw();
        });
        edit.setAttribute("aria-label", "Edit " + label.toLowerCase());
        term.append(edit);
        list.append(term, element("dd", answers[index] || "Skipped"));
      });
      const label = element("label", "", "dh-consent");
      const check = element("input");
      check.type = "checkbox";
      check.checked = consent;
      label.append(check, " I agree to share these details with DH Construction through WhatsApp.");
      const note = element("p", "Review the draft and press Send in WhatsApp.", "dh-eq-hint");
      const status = element("p", "", "dh-eq-status");
      status.setAttribute("role", "status");
      const entries = fields.map((field, index) => [field.label, answers[index]]);
      const send = action("Submit via WhatsApp", () => {
        if (!consent || shared) return;
        shared = true;
        handoff(send, status, draftURL(assistant.dataset.whatsapp, "Guided project enquiry", entries));
      }, "dh-eq-action");
      send.disabled = !consent || shared;
      check.addEventListener("change", () => {
        consent = check.checked;
        if (!consent) {
          status.replaceChildren();
          shared = false;
        }
        send.disabled = !consent || shared;
      });
      body.append(title, list, label, note, send, status);
      title.focus();
      return;
    }
    const field = fields[step];
    const progress = element("p", "Question " + (step + 1) + " of " + fields.length, "dh-guide-progress");
    const form = element("form");
    if (step && !editing && answers[step - 1]) {
      const previous = element("p", answers[step - 1], "dh-chat-reply");
      previous.setAttribute("aria-label", "Your previous answer: " + answers[step - 1]);
      body.append(previous);
    }
    const label = element("label", field.question, "dh-guide-question");
    label.htmlFor = "dh-guide-answer";
    const input = element(field.type === "textarea" ? "textarea" : "input");
    if (field.type !== "textarea") input.type = field.type || "text";
    input.maxLength = field.type === "textarea" ? 1200 : field.type === "tel" ? 25 : 120;
    input.placeholder = field.hint || (field.options ? "Choose below or type your answer" : "Type your reply");
    if (field.autocomplete) input.autocomplete = field.autocomplete;
    input.id = label.htmlFor;
    input.required = !field.optional;
    input.value = answers[step];
    input.addEventListener("input", () => {
      validate(input);
      if (input.value.trim() !== answers[step]) {
        consent = shared = false;
      }
      answers[step] = input.value;
    });
    const actions = element("div", "", "dh-guide-actions");
    if (step > 0 && !editing) actions.append(action("Back", () => {
      step--;
      draw();
    }, "dh-eq-secondary"));
    const next = element("button", editing ? "Review changes" : step === fields.length - 1 ? "Review enquiry" : "Continue", "dh-eq-action");
    next.type = "submit";
    actions.append(next);
    form.addEventListener("submit", event => {
      event.preventDefault();
      validate(input);
      if (!form.reportValidity()) return;
      answers[step] = input.value.trim();
      step = editing ? fields.length : step + 1;
      editing = false;
      draw();
    });
    form.append(label);
    if (field.options) {
      const suggestions = element("div", "", "dh-chat-choices");
      for (const option of field.options) {
        const choice = action(option, () => {
          input.value = option;
          input.dispatchEvent(new Event("input", {bubbles: true}));
          form.requestSubmit();
        });
        suggestions.append(choice);
      }
      form.append(suggestions);
    }
    if (field.optional) {
      const skip = action("Skip budget", () => {
        input.value = "";
        input.dispatchEvent(new Event("input", {bubbles: true}));
        form.requestSubmit();
      }, "dh-eq-secondary");
      actions.insertBefore(skip, next);
    }
    form.append(input, actions);
    body.append(progress, form);
    input.focus({preventScroll:true});
  }

  welcome.querySelector(".dh-invite").addEventListener("click", () => launch.click());
  welcome.querySelector("[aria-label]").addEventListener("click", () => {
    welcome.hidden = true;
    launch.focus();
  });
  launch.addEventListener("click", () => {
    welcome.hidden = launch.hidden = true;
    panel.hidden = false;
    if (!motion.matches && panel.animate) {
      panel.animate([
        {opacity: 0, transform: "translateY(8px)"},
        {opacity: 1, transform: "translateY(0)"},
      ], {duration: 160, easing: "ease-out"});
    }
    launch.setAttribute("aria-expanded", "true");
    if (!body.childElementCount) draw();
    else (body.querySelector("input:not([type=checkbox]), select, textarea, h2") || panel.querySelector("button")).focus();
  });
  panel.querySelector("[data-minimize]").addEventListener("click", () => hide(false));
  panel.querySelector("[data-close]").addEventListener("click", () => hide(true));
  panel.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      event.preventDefault();
      hide(false);
    }
  });
  assistant.hidden = false;
})();

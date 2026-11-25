(() => {
  document.documentElement.classList.add("js");

  const nav = document.querySelector("#site-nav");
  const menuButton = document.querySelector(".menu-toggle");

  if (nav && menuButton) {
    menuButton.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      menuButton.setAttribute("aria-expanded", String(open));
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        menuButton.setAttribute("aria-expanded", "false");
        menuButton.focus();
      }
    });
  }

  document.querySelectorAll(".message-close").forEach((button) => {
    button.addEventListener("click", () => button.closest(".message")?.remove());
  });

  const revealItems = document.querySelectorAll("[data-reveal]");
  if (!("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-in"));
    return;
  }
  const observer = new IntersectionObserver((entries, currentObserver) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-in");
        currentObserver.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  revealItems.forEach((item) => observer.observe(item));
})();

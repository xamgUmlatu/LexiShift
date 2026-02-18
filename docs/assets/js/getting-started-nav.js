(() => {
  const root = document.querySelector("[data-guide-nav]");
  if (!root) {
    return;
  }

  const links = Array.from(root.querySelectorAll(".guide-rail__link[href^='#']"));
  if (!links.length) {
    return;
  }

  const sections = links
    .map((link) => {
      const id = link.getAttribute("href").slice(1);
      return document.getElementById(id);
    })
    .filter(Boolean);

  if (!sections.length) {
    return;
  }

  root.setAttribute("data-guide-nav-ready", "true");

  const linkById = new Map(
    links.map((link) => [link.getAttribute("href").slice(1), link]),
  );
  const sectionById = new Map(sections.map((section) => [section.id, section]));

  let activeId = sections[0].id;

  const setActive = (id) => {
    const nextLink = linkById.get(id);
    const nextSection = sectionById.get(id);
    if (!nextLink || !nextSection) {
      return;
    }
    links.forEach((link) => link.classList.toggle("is-active", link === nextLink));
    sections.forEach((section) =>
      section.classList.toggle("is-current", section === nextSection),
    );
    activeId = id;
  };

  const updateActive = () => {
    const threshold = window.scrollY + 140;
    let candidate = sections[0];

    sections.forEach((section) => {
      if (section.offsetTop <= threshold) {
        candidate = section;
      }
    });

    if (candidate.id !== activeId) {
      setActive(candidate.id);
    }
  };

  links.forEach((link) => {
    link.addEventListener("click", () => {
      const id = link.getAttribute("href").slice(1);
      setActive(id);
    });
  });

  setActive(activeId);
  window.addEventListener("scroll", updateActive, { passive: true });
  window.addEventListener("resize", updateActive);
  updateActive();
})();

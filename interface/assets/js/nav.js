(function () {
  function initSectionNav() {
    const navs = document.querySelectorAll("[data-section-nav]");

    navs.forEach(function (nav) {
      const buttons = Array.from(nav.querySelectorAll("[data-nav-target]"));
      const panelSelector = nav.getAttribute("data-panel-scope") || "[data-panel]";
      const panels = Array.from(document.querySelectorAll(panelSelector));

      if (!buttons.length || !panels.length) {
        return;
      }

      function activate(target) {
        buttons.forEach(function (button) {
          button.classList.toggle("is-active", button.dataset.navTarget === target);
        });

        panels.forEach(function (panel) {
          panel.classList.toggle("hidden", panel.dataset.panel !== target);
        });
      }

      buttons.forEach(function (button) {
        button.addEventListener("click", function () {
          activate(button.dataset.navTarget);
        });
      });

      const defaultButton = buttons.find(function (button) {
        return button.hasAttribute("data-nav-default");
      }) || buttons[0];

      activate(defaultButton.dataset.navTarget);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSectionNav);
  } else {
    initSectionNav();
  }
})();

(function (root, factory) {
  const setMockState = factory();
  if (typeof module === "object" && module.exports) module.exports = { setMockState };
  if (root && root.document) {
    root.document.addEventListener("click", (event) => {
      const button = event.target.closest("[data-state-switch]");
      if (button) setMockState(button.dataset.stateSwitch, root.document);
    });
  }
})(typeof globalThis === "object" ? globalThis : this, function () {
  const states = new Set(["idle", "loading", "error", "success"]);

  function setMockState(name, root) {
    if (!states.has(name)) throw new RangeError(`Unknown preview state: ${name}`);
    for (const panel of root.querySelectorAll("[data-state-panel]")) {
      panel.hidden = panel.dataset.statePanel !== name;
    }
    for (const button of root.querySelectorAll("[data-state-switch]")) {
      button.setAttribute("aria-pressed", String(button.dataset.stateSwitch === name));
    }
  }

  return setMockState;
});

const test = require("node:test");
const assert = require("node:assert/strict");
const { setMockState } = require("./mockup.js");

function fixtureRoot() {
  const panels = ["idle", "loading", "error", "success"].map((name) => ({
    dataset: { statePanel: name },
    hidden: name !== "idle",
  }));
  const buttons = ["idle", "loading", "error", "success"].map((name) => ({
    dataset: { stateSwitch: name },
    pressed: String(name === "idle"),
    setAttribute(attribute, value) {
      if (attribute === "aria-pressed") this.pressed = value;
    },
  }));
  return {
    panels,
    buttons,
    querySelectorAll(selector) {
      return selector === "[data-state-panel]" ? panels : buttons;
    },
  };
}

test("selects each known state and updates the announced control state", () => {
  const root = fixtureRoot();

  for (const state of ["idle", "loading", "error", "success"]) {
    setMockState(state, root);
    assert.deepEqual(root.panels.filter((panel) => !panel.hidden).map((panel) => panel.dataset.statePanel), [state]);
    assert.deepEqual(root.buttons.filter((button) => button.pressed === "true").map((button) => button.dataset.stateSwitch), [state]);
  }
});

test("rejects unknown states without changing the preview", () => {
  const root = fixtureRoot();
  const beforePanels = root.panels.map((panel) => panel.hidden);
  const beforeButtons = root.buttons.map((button) => button.pressed);

  assert.throws(() => setMockState("unknown", root), RangeError);
  assert.deepEqual(root.panels.map((panel) => panel.hidden), beforePanels);
  assert.deepEqual(root.buttons.map((button) => button.pressed), beforeButtons);
});

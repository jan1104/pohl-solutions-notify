// Exercise the actual frontend methods; no claim of browser or visual testing.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const elements = new Map();
const context = {
  HTMLElement: class {},
  window: {customElements: {get: name => elements.get(name), define: (name, ctor) => elements.set(name, ctor)}, addEventListener() {}},
  setInterval: () => 0, clearInterval() {},
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../custom_components/alarm_system/frontend/panel.js'), 'utf8'), context);
const Panel = elements.get('alarm-system-panel');
const panel = Object.create(Panel.prototype);

function draft(extra = {}) {
  return {platform: 'android', notify_action: 'notify.mobile_app_phone', user_id: 'user',
    name: 'Phone', push: true, popup: false, sound: false, speech: true, browsers: [], ...extra};
}
function verify(step, value) {
  panel.wizard = {kind: 'device', step, draft: value};
  return panel.validateWizard();
}

test('Android renders independent voice and tone switches with correct checked states', () => {
  const html = panel.checks(draft());
  for (const key of ['push', 'sound', 'popup', 'speech']) assert.match(html, new RegExp('name="' + key + '"'));
  assert.match(html, /name="speech" checked/);
  assert.doesNotMatch(html, /name="sound" checked/);
  assert.match(html, /auch ohne Alarmton/);
});
test('phone selection does not require sensors before output choices are available', () => {
  assert.doesNotThrow(() => verify(1, draft({sound: true})));
});
test('voice-only can proceed without ringer or volume sensors', () => {
  assert.doesNotThrow(() => verify(2, draft()));
});
test('alarm tone still requires original-mode and volume sensors', () => {
  assert.throws(() => verify(2, draft({sound: true})), /Companion-Sensoren/);
  assert.doesNotThrow(() => verify(2, draft({sound: true, ringer_sensor: 'sensor.ringer', volume_sensor: 'sensor.volume'})));
});
test('iPhone offers no unsupported speech switch', () => {
  assert.doesNotMatch(panel.checks(draft({platform: 'ios'})), /name="speech"/);
});
test('browser offers only its alarm window switch', () => {
  const html = panel.checks(draft({platform: 'browser'}));
  assert.match(html, /name="popup"/);
  for (const key of ['push', 'sound', 'speech']) assert.doesNotMatch(html, new RegExp('name="' + key + '"'));
});
test('all outputs may be turned off explicitly', () => {
  const value = draft({push: false, sound: false, speech: false, popup: false});
  assert.doesNotThrow(() => verify(2, value));
  assert.doesNotMatch(panel.checks(value), /checked/);
});

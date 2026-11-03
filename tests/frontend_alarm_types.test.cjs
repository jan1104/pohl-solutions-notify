// Run the real frontend in a DOM-free VM; these are not browser/device tests.
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
const plain = value => JSON.parse(JSON.stringify(value));
const custom = {id: 'CUSTOM_123456789ABC', name: 'Wasser <Keller>', mode: 'alarm', priority: 5,
  push: false, sound: true, speech: false, popup: true, tone_seconds: 5, speech_seconds: 8,
  speech_template: 'Achtung. {name}. Standort {site}. {areas}.', channel: 'Wasser <Keller>', builtin: false};
function panel(extra = {}) {
  const p = Object.create(Panel.prototype);
  p.data = {users: {}, devices: {}, sources: {}, incidents: {}, available_users: [{id: 'user', name: 'Ada'}],
    alarm_types: {[custom.id]: {...custom}}, ...extra};
  p._hass = {states: {}, user: {is_admin: true}};
  return p;
}
function mount(p) {
  const nodes = new Map();
  const node = () => ({addEventListener() {}, focus() {}, querySelectorAll: () => []});
  const root = {innerHTML: '', focus() {}, querySelector: key => {if (!nodes.has(key)) nodes.set(key, node());return nodes.get(key);}, querySelectorAll: () => []};
  p.shadowRoot = {querySelector: () => root};
  p.refreshTestStep = () => {};
  p.autoSensors = () => {};
  return {root, nodes};
}
test('legacy snapshots keep built-in choices and custom profiles determine mode and priority', () => {
  const p = panel();
  assert.equal(p.typeLabel(custom.id), custom.name);
  assert.equal(p.isAlarm(custom.id), true);
  assert.equal(p.isAlarm('INFO'), false);
  p.data.incidents = Object.fromEntries(['FIRE', custom.id, 'INTRUSION'].map(type => [type, {type, status: 'open', started_at: '2026-11-03'}]));
  assert.deepEqual(plain(p.active().map(i => i.type)), [custom.id, 'INTRUSION', 'FIRE']);
  delete p.data.alarm_types;
  assert.deepEqual(plain(p.typeChoices().map(t => t.id)), ['INFO', 'WARNING', 'FIRE', 'INTRUSION']);
});
test('user wizard displays escaped custom and renamed built-in labels', () => {
  const p = panel();
  p.data.alarm_types.FIRE = {...p.typeChoices().find(t => t.id === 'FIRE'), name: 'Brand & Rauch'};
  const {root} = mount(p);
  p.wizard = {kind: 'user', step: 1, draft: {id: 'user', types: [custom.id], enabled: true}};
  p.renderWizard();
  assert.match(root.innerHTML, /Wasser &lt;Keller&gt;/);
  assert.match(root.innerHTML, /Brand &amp; Rauch/);
  assert.match(root.innerHTML, /data-alarm-type="CUSTOM_123456789ABC" type="checkbox" checked/);
  assert.doesNotMatch(root.innerHTML, /<Keller>/);
});
test('recipient checkbox capture stores only known IDs in types, without checkbox payload fields', () => {
  const p = panel();
  const checks = [{name: 'recipient_type', type: 'checkbox', checked: true, dataset: {alarmType: custom.id}},
    {name: 'recipient_type', type: 'checkbox', checked: false, dataset: {alarmType: 'FIRE'}},
    {name: 'recipient_type', type: 'checkbox', checked: true, dataset: {alarmType: 'UNKNOWN'}}];
  const enabled = {name: 'enabled', type: 'checkbox', checked: true};
  const form = {querySelectorAll: selector => selector === '[name="recipient_type"]' ? checks : [...checks, enabled]};
  p.shadowRoot = {querySelector: () => form};
  p.wizard = {kind: 'user', step: 1, draft: {id: 'user', types: []}};
  p.captureWizard();
  assert.deepEqual(plain(p.wizard.draft), {id: 'user', types: [custom.id], enabled: true});
});
test('source assignment offers one existing-type dropdown and automatic grouping', () => {
  const p = panel();
  p.data.alarm_types.FIRE = {...p.typeChoices().find(t => t.id === 'FIRE'), name: 'Brand & Rauch'};
  const {root} = mount(p);
  p.wizard = {kind: 'source', step: 1, draft: {type: custom.id, alarm_key: 'Alte Gruppe', detection: 'Alte Beschreibung', name: 'Sensor', enabled: true}};
  p.renderWizard();
  assert.match(root.innerHTML, /Art der Meldung<select name="type">/);
  assert.match(root.innerHTML, /value="CUSTOM_123456789ABC" selected/);
  assert.match(root.innerHTML, /Wasser &lt;Keller&gt;/);
  assert.match(root.innerHTML, /Brand &amp; Rauch/);
  assert.match(root.innerHTML, /automatisch zu einem gemeinsamen Alarm zusammengefasst/);
  assert.doesNotMatch(root.innerHTML, /name="detection"|alarm_key|Gemeinsames Alarmereignis|Neues Ereignis/);
  assert.doesNotMatch(root.innerHTML, /Benachrichtigungstext/);
  delete p.wizard.draft.alarm_key;
  assert.doesNotThrow(() => p.validateWizard());
  p.wizard.draft.type = 'UNKNOWN';
  assert.throws(() => p.validateWizard(), /vorhandene Art der Meldung/);
});

test('information source keeps its message settings without an event group', () => {
  const p = panel();
  const {root} = mount(p);
  p.wizard = {kind: 'source', step: 1, draft: {type: 'INFO', name: 'Tor', message: 'Tor offen', enabled: true}};
  p.renderWizard();
  assert.match(root.innerHTML, /Art der Meldung<select name="type">/);
  assert.match(root.innerHTML, /Benachrichtigungstext/);
  assert.match(root.innerHTML, /name="silent"/);
  assert.doesNotMatch(root.innerHTML, /name="detection"|alarm_key|Gemeinsames Alarmereignis/);
  assert.doesNotThrow(() => p.validateWizard());
});

test('saving an edited source sends no stale manual event group', async () => {
  const p = panel();
  const {root} = mount(p);
  const draft = {id: 'source', name: 'Sensor', entity_id: 'binary_sensor.source', type: custom.id,
    alarm_key: 'Legacy', _new_group: true, detection: 'Legacy detail', enabled: true};
  p.wizard = {kind: 'source', step: 2, editing: true, draft};
  p.captureWizard = () => {};
  p.renderAdmin = () => {};
  p.closeWizard = () => {};
  const calls = [];
  p.manage = async (action, data) => calls.push({action, data: plain(data)});
  p.renderWizard();
  assert.match(root.innerHTML, /Art der Meldung/);
  assert.match(root.innerHTML, /Automatisch mit allen Meldern derselben Alarmart/);
  assert.doesNotMatch(root.innerHTML, /Legacy/);
  await root.querySelector('#wizard-form').onsubmit({preventDefault() {}});
  assert.equal(calls.length, 1);
  assert.equal(calls[0].action, 'source_upsert');
  assert.equal(calls[0].data.type, custom.id);
  assert.equal(calls[0].data.detection, 'Legacy detail');
  assert.equal(Object.hasOwn(calls[0].data, 'alarm_key'), false);
  assert.equal(Object.hasOwn(calls[0].data, '_new_group'), false);
  assert.equal(draft.alarm_key, 'Legacy');
});

test('configuration export includes registry schema 2 and custom history retains current name', () => {
  const data = panel().data;
  data.journal = [{id: 'row', at: '2026-11-03T12:00:00Z', type: custom.id, action: 'alarm_raised'}];
  context.exportData = data;
  const backup = plain(vm.runInContext('configurationBackup(exportData)', context));
  assert.equal(backup.schema_version, 2);
  assert.deepEqual(backup.alarm_types[custom.id], custom);
  assert.equal(backup.alarm_types.FIRE.tone_seconds, null);
  assert.match(vm.runInContext('journalCSV(exportData)', context), /Wasser <Keller>/);
});
test('custom profile capture preserves stable ID/channel and accepts independent switches', () => {
  const p = panel();
  p.alarmTypeDraft = {...custom};
  const values = {name: {value: '  Wasseralarm  '}, priority: {type: 'number', value: '3'},
    tone_seconds: {type: 'number', value: '4.5'}, speech_seconds: {type: 'number', value: '8'},
    speech_template: {value: '{name} in {areas}'},
    push: {type: 'checkbox', checked: false}, sound: {type: 'checkbox', checked: false},
    speech: {type: 'checkbox', checked: true}, popup: {type: 'checkbox', checked: false}};
  const result = p.captureAlarmType({querySelector: selector => values[selector.match(/"(.*?)"/)[1]]});
  assert.equal(result.name, 'Wasseralarm');
  assert.equal(result.channel, custom.channel);
  assert.equal(result.id, custom.id);
  assert.equal(result.tone_seconds, 4.5);
  assert.equal(result.sound, false);
  assert.equal(result.speech, true);
  assert.doesNotThrow(() => p.validateAlarmType(result));
});
test('custom validation rejects invalid priorities, durations and unsafe speech placeholders', () => {
  const p = panel();
  for (const invalid of [{priority: 101}, {priority: 1.5}, {tone_seconds: 16}, {speech_seconds: 0},
    {speech_seconds: NaN}, {name: ''}, {speech_template: '{name.foo}'},
    {speech_template: '{name!r}'}, {speech_template: '{site:20}'}, {speech_template: 'x'.repeat(241)}]) {
    assert.throws(() => p.validateAlarmType({...custom, ...invalid}), JSON.stringify(invalid));
  }
});
test('built-in edits preserve fixed priorities and device durations', () => {
  const p = panel();
  const builtin = p.typeChoices().find(t => t.id === 'INTRUSION');
  p.alarmTypeDraft = builtin;
  const result = p.captureAlarmType({querySelector: selector => selector.includes('name') ? {value: 'Schutz'} : {type: 'number', value: '1'}});
  assert.equal(result.priority, 10);
  assert.equal(result.tone_seconds, null);
  assert.equal(result.speech_seconds, null);
  const html = p.alarmTypeFields(builtin);
  assert.match(html, /name="priority"[^>]*disabled/);
  assert.doesNotMatch(html, /name="tone_seconds"|name="speech_seconds"/);
});
test('registry list escapes names, exposes recipients, and locks changes during active alarms', () => {
  const p = panel({users: {user: {name: 'Ada', enabled: true, types: [custom.id]}},
    incidents: {incident: {type: 'FIRE', status: 'open', started_at: '2026-11-03'}}});
  const {root} = mount(p);
  p.renderAlarmTypeAdmin();
  assert.match(root.innerHTML, /Empfänger: Ada/);
  assert.match(root.innerHTML, /Wasser &lt;Keller&gt;/);
  assert.match(root.innerHTML, /data-go="edit-type" data-id="CUSTOM_123456789ABC" disabled/);
  assert.match(root.innerHTML, /data-go="remove-type" data-id="CUSTOM_123456789ABC" disabled/);
  assert.doesNotMatch(root.innerHTML, /data-go="remove-type" data-id="FIRE"/);
});
test('new-profile dialog submits creation without an ID and restores default speech for an empty field', async () => {
  const p = panel();
  const {root, nodes} = mount(p);
  let request;
  p.manage = async (action, data) => {request = {action, data};return {alarm_type_id: 'CUSTOM_AAAAAAAAAAAA'};};
  p.showToast = () => {};
  p.openAlarmType();
  const fields = {name: {value: 'Technik'}, speech_template: {value: '  '}, sound: {type: 'checkbox', checked: false}};
  const form = {querySelector: selector => fields[selector.match(/"(.*?)"/)[1]]};
  await nodes.get('#type-form').onsubmit({preventDefault() {}, target: form});
  assert.equal(request.action, 'alarm_type_upsert');
  assert.equal(Object.hasOwn(request.data, 'id'), false);
  assert.equal(request.data.name, 'Technik');
  assert.equal(request.data.sound, false);
  assert.equal(request.data.speech_template, custom.speech_template);
  assert.equal(root.innerHTML, '');
});
test('an alarm becoming active after opening the dialog prevents its submission', async () => {
  const p = panel();
  const {nodes} = mount(p);
  p.openAlarmType(custom.id);
  p.data.incidents.newAlarm = {status: 'claimed', type: 'FIRE', started_at: '2026-11-03'};
  p.manage = () => {assert.fail('A locked registry must not be submitted');};
  await nodes.get('#type-form').onsubmit({preventDefault() {}, target: {}});
  assert.match(nodes.get('#type-error').textContent, /aktiver Alarme/);
  assert.equal(nodes.get('#type-save').disabled, false);
});
test('device testing offers custom types while keeping both baseline tests required', () => {
  const p = panel({devices: {phone: {id: 'phone', test_session: 'session'}}, incidents: {
    first: {type: custom.id, status: 'ended', test_device: 'phone', test_session: 'session'},
    second: {type: 'FIRE', status: 'ended', test_device: 'phone', test_session: 'session'}}});
  const {root} = mount(p);
  p.wizard = {kind: 'device', step: 4, draft: {id: 'phone', name: 'Phone', platform: 'android'}};
  p.renderWizard();
  assert.match(root.innerHTML, /data-test-type="CUSTOM_123456789ABC"/);
  assert.match(root.innerHTML, /Wasser &lt;Keller&gt; testen/);
  const check = {}, button = {}, status = {};
  p.shadowRoot = {querySelectorAll: () => [], querySelector: key => ({'#tested-check': check, '#confirm-device': button, '#test-progress': status}[key])};
  p.updateTestConfirmation();
  assert.equal(check.disabled, true);
  assert.equal(button.disabled, true);
  assert.match(status.textContent, /Einbruchalarm: noch prüfen/);
  p.data.incidents.third = {type: 'INTRUSION', status: 'ended', test_device: 'phone', test_session: 'session'};
  p.updateTestConfirmation();
  assert.equal(check.disabled, false);
});
test('Android sensor requirements follow assigned profile outputs and the device tone switch', () => {
  const p = panel({users: {user: {id: 'user', types: [custom.id]}}});
  p.data.alarm_types[custom.id].sound = false;
  p.wizard = {kind: 'device', step: 2, draft: {platform: 'android', user_id: 'user', sound: true, popup: false}};
  assert.doesNotThrow(() => p.validateWizard());
  p.data.users.user.types.push('INFO');
  assert.doesNotThrow(() => p.validateWizard());
  p.data.users.user.types.push('FIRE');
  assert.throws(() => p.validateWizard(), /Companion-Sensoren/);
  p.data.users.user.types = [custom.id];
  p.data.alarm_types[custom.id].sound = true;
  assert.throws(() => p.validateWizard(), /Companion-Sensoren/);
  p.wizard.draft.sound = false;
  assert.doesNotThrow(() => p.validateWizard());
});


test('information and warning retain every output switch when renamed or disabled', () => {
  const p = panel();
  for (const id of ['INFO', 'WARNING']) {
    const info = {...p.typeChoices().find(t => t.id === id), name: 'Eigene Meldung', push: false, sound: false, speech: false, popup: false};
    const html = p.alarmTypeFields(info);
    for (const key of ['push', 'sound', 'speech', 'popup']) assert.match(html, new RegExp('name="'+key+'"'));
    assert.match(html, /ohne „Ich komme“/);
    assert.match(html, /Benachrichtigungstext des Melders vorgelesen/);
    assert.match(html, /Das Garagentor ist noch offen/);
    assert.doesNotMatch(html, /name="priority"/);
    p.alarmTypeDraft = info;
    const values = {speech: {type: 'checkbox', checked: true}, speech_template: {value: 'Bitte das Tor schließen.'}};
    const result = p.captureAlarmType({querySelector: selector => values[selector.match(/"(.*?)"/)[1]]});
    assert.equal(result.speech, true);
    assert.equal(result.push, false);
    assert.equal(result.mode, 'message');
    assert.equal(result.speech_template, 'Bitte das Tor schließen.');
  }
});

test('standard speech is hidden behind plain instructions and an escaped concrete preview', () => {
  const p = panel({site_id: 'Werkstatt <Ost>'});
  const html = p.alarmTypeFields(custom);
  assert.match(html, /<textarea[^>]*><\/textarea>/);
  assert.match(html, /Standard-Sprachtext – wenn das Feld leer bleibt/);
  const customHtml = p.alarmTypeFields({...custom, speech_template: 'Bitte zum Eingang.'});
  assert.match(customHtml, /id="standard-speech-preview">Achtung\. Wasser &lt;Keller&gt;/);
  assert.match(customHtml, /id="speech-preview"[^>]*>Bitte zum Eingang\./);
  assert.match(html, /Alarmname einfügen/);
  assert.match(html, /Standort einfügen/);
  assert.match(html, /Betroffene Bereiche einfügen/);
  assert.match(html, /Achtung. Wasser &lt;Keller&gt;. Standort Werkstatt &lt;Ost&gt;. Erdgeschoss, Küche./);
  assert.doesNotMatch(html, /<Keller>|<Ost>/);
  assert.equal(p.speechPreview({...custom, speech_template: 'Bitte am Eingang melden.'}), 'Bitte am Eingang melden.');
  assert.equal(p.speechPreview({...custom, speech_template: '{name} bei {site}: {areas}'}), 'Wasser <Keller> bei Werkstatt <Ost>: Erdgeschoss, Küche');
});

test('speech preview updates with typing and labelled buttons insert at the cursor safely', () => {
  const p = panel({site_id: 'Haus'});
  const {root, nodes} = mount(p);
  const speech = {value: '', selectionStart: 0, selectionEnd: 0, focus() {}, setSelectionRange(start, end) {this.selectionStart = start;this.selectionEnd = end;}};
  const name = {value: 'Hausalarm'};
  const insert = {dataset: {speechInsert: 'name'}};
  root.querySelectorAll = selector => selector === '[data-speech-insert]' ? [insert] : [];
  root.querySelector('#type-form').querySelector = selector => selector === '[name="speech_template"]' ? speech : name;
  p.openAlarmType(custom.id);
  speech.value = 'Bitte prüfen.';
  speech.oninput();
  assert.equal(nodes.get('#speech-preview').textContent, 'Bitte prüfen.');
  assert.equal(nodes.get('#standard-speech-preview').textContent, 'Achtung. Hausalarm. Standort Haus. Erdgeschoss, Küche.');
  speech.value = 'Meldung: Ende';speech.selectionStart = 9;speech.selectionEnd = 13;
  insert.onclick();
  assert.equal(speech.value, 'Meldung: {name}');
  assert.equal(nodes.get('#speech-preview').textContent, 'Meldung: Hausalarm');
  name.value = '<img src=x>';
  name.oninput();
  assert.equal(nodes.get('#speech-preview').textContent, 'Meldung: <img src=x>');
  assert.equal(nodes.get('#standard-speech-preview').textContent, 'Achtung. <img src=x>. Standort Haus. Erdgeschoss, Küche.');
  speech.value = 'x'.repeat(240);speech.selectionStart = 240;speech.selectionEnd = 240;
  insert.onclick();
  assert.equal(speech.value.length, 240);
  assert.match(nodes.get('#type-error').textContent, /höchstens 240/);
});

test('message notification tone does not require alarm volume sensors', () => {
  const p = panel({users: {user: {id: 'user', types: ['INFO']}}});
  p.data.alarm_types.INFO = {...p.typeChoices().find(t => t.id === 'INFO'), sound: true};
  p.wizard = {kind: 'device', step: 2, draft: {platform: 'android', user_id: 'user', sound: true, popup: false}};
  assert.doesNotThrow(() => p.validateWizard());
});

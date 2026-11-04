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
test('built-in edits preserve fixed priorities and retain legacy timing on blank fields', () => {
  const p = panel();
  const builtin = p.typeChoices().find(t => t.id === 'INTRUSION');
  p.alarmTypeDraft = builtin;
  const fields = {name: {value: 'Schutz'}, tone_seconds: {type: 'number', value: ''}, speech_seconds: {type: 'number', value: ''}, priority: {type: 'number', value: '1', disabled: true}};
  const result = p.captureAlarmType({querySelector: selector => fields[selector.match(/"(.*?)"/)[1]]});
  assert.equal(result.priority, 10);
  assert.equal(result.tone_seconds, null);
  assert.equal(result.speech_seconds, null);
  assert.doesNotThrow(() => p.validateAlarmType(result));
  const html = p.alarmTypeFields(builtin);
  assert.match(html, /name="priority"[^>]*disabled/);
  assert.match(html, /name="tone_seconds"[^>]*value=""/);
  assert.match(html, /name="speech_seconds"[^>]*value=""/);
  assert.match(html, /Leer lassen: bisherige Gerätezeiten verwenden/);
});

test('built-in alarm times are editable per type and use the same bounded validation', () => {
  const p = panel();
  const builtin = p.typeChoices().find(t => t.id === 'FIRE');
  p.alarmTypeDraft = builtin;
  const fields = {tone_seconds: {type: 'number', value: '7'}, speech_seconds: {type: 'number', value: '4.5'}};
  const result = p.captureAlarmType({querySelector: selector => fields[selector.match(/"(.*?)"/)[1]]});
  assert.equal(result.tone_seconds, 7);
  assert.equal(result.speech_seconds, 4.5);
  assert.equal(result.priority, 20);
  assert.doesNotThrow(() => p.validateAlarmType(result));
  for (const change of [{tone_seconds: 0}, {tone_seconds: 16}, {tone_seconds: NaN}, {speech_seconds: 13}, {speech_seconds: false}]) {
    assert.throws(() => p.validateAlarmType({...result, ...change}));
  }
  assert.doesNotMatch(p.alarmTypeFields(p.typeChoices().find(t => t.id === 'INFO')), /name="tone_seconds"|name="speech_seconds"/);
});

test('legacy timing disclosure shows assigned devices without hiding different values', () => {
  const p = panel({users: {u: {id: 'u', types: ['FIRE']}}, devices: {
    one: {id: 'one', name: 'Phone <One>', user_id: 'u', fire_seconds: 3, speech_seconds: 6},
    two: {id: 'two', name: 'Phone Two', user_id: 'u', fire_seconds: 9, speech_seconds: 11},
    other: {id: 'other', name: 'Not assigned', user_id: 'x', fire_seconds: 12}
  }});
  const html = p.alarmTimingFields(p.typeChoices().find(t => t.id === 'FIRE'));
  assert.match(html, /Bisherige Zeiten/);
  assert.match(html, /Phone &lt;One&gt;.*Tonphase: 3 Sekunden.*Sprache: 6 Sekunden/);
  assert.match(html, /Phone Two.*Tonphase: 9 Sekunden.*Sprache: 11 Sekunden/);
  assert.doesNotMatch(html, /Not assigned|Phone <One>/);
});

test('device wizard delegates timing to alarm types while retaining its saved legacy values', () => {
  const p = panel();
  const {root} = mount(p);
  p.wizard = {kind: 'device', step: 2, editing: true, draft: {id: 'phone', platform: 'android', user_id: 'u',
    popup: false, push: true, sound: true, speech: true, browsers: [], fire_seconds: 3, intrusion_seconds: 9, speech_seconds: 11}};
  p.renderWizard();
  assert.doesNotMatch(root.innerHTML, /name="fire_seconds"|name="intrusion_seconds"|name="speech_seconds"/);
  assert.match(root.innerHTML, /Ton- und Sprachzeiten legst du unter Alarmarten fest/);
  p.captureWizard();
  assert.deepEqual(plain([p.wizard.draft.fire_seconds, p.wizard.draft.intrusion_seconds, p.wizard.draft.speech_seconds]), [3, 9, 11]);
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
  assert.match(html, /Standard-Sprachtext/);
  assert.match(html, /id="custom-speech-preview" hidden/);
  assert.match(html, /<details class="alarm-type-help"><summary>Weitere Hinweise<\/summary>/);
  const customHtml = p.alarmTypeFields({...custom, speech_template: 'Bitte zum Eingang.'});
  assert.match(customHtml, /id="standard-speech-preview">Achtung\. Wasser &lt;Keller&gt;/);
  assert.match(customHtml, /id="speech-preview"[^>]*>Bitte zum Eingang\./);
  assert.match(html, /Alarmname einfügen/);
  assert.match(html, /Standort einfügen/);
  assert.match(html, /Bereiche einfügen/);
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
  assert.equal(nodes.get('#custom-speech-preview').hidden, false);
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


test('completed history entries start collapsed with date status type and every source in summary', () => {
  const p = panel();
  const i = {id: 'event<1>', type: custom.id, status: 'false_alarm', started_at: '2026-11-03T12:00:00Z',
    ended_at: '2026-11-03T12:01:00Z', site_id: 'Haus', title: 'Hausalarm',
    sources: {one: {id: 'one', name: 'Tür <Ost>', area: 'EG', triggered_at: '2026-11-03T12:00:00Z'},
      two: {id: 'two', name: 'Fenster', area: 'OG', triggered_at: '2026-11-03T12:00:01Z'}}, responses: {}, audit: [], delivery: []};
  p.responseRows = () => '<p>Rückmeldungen im Detail</p>';
  const html = p.historyIncidentHTML(i);
  assert.match(html, /^<details class="history-entry" data-disclosure-key="history-incident:event&lt;1&gt;">/);
  assert.doesNotMatch(html.slice(0, html.indexOf('>')), /\bopen\b/);
  const summary = html.match(/<summary>(.*?)<\/summary>/s)[1];
  assert.match(summary, /history-time/);
  assert.match(summary, /Fehlalarm bestätigt/);
  assert.match(summary, /Wasser &lt;Keller&gt;/);
  assert.match(summary, /Melder: Tür &lt;Ost&gt;, Fenster/);
  assert.doesNotMatch(summary, /Rückmeldungen im Detail|Verlauf und Transport|WER KOMMT/);
  assert.match(html.slice(html.indexOf('</summary>')), /Rückmeldungen im Detail/);
  assert.match(html, /Verlauf und Transport/);
  assert.doesNotMatch(html, /data-action=/);
  const active = p.incidentHTML({...i, status: 'open'}, true);
  assert.match(active, /^<section/);
  assert.match(active, /data-action="coming"/);
});

test('history disclosure identity remains stable when summary text changes', () => {
  const p = panel();
  p.disclosures = new Map();
  const entry = {dataset: {disclosureKey: 'history-incident:stable'}, open: true};
  p.rememberDetails({querySelectorAll: () => [entry]});
  const refreshed = {dataset: {disclosureKey: 'history-incident:stable'}, open: false};
  p.restoreDetails({querySelectorAll: () => [refreshed]});
  assert.equal(refreshed.open, true);
  const other = {dataset: {disclosureKey: 'history-incident:other'}, open: false};
  p.restoreDetails({querySelectorAll: () => [other]});
  assert.equal(other.open, false);
});

test('information history is collapsed and distinguishes triggered from received', () => {
  const p = panel();
  const html = p.historyMessageHTML({id: 'msg', type: 'INFO', at: '2026-11-03T12:00:00Z',
    source_name: 'Tor', area: 'Hof', text: '<script>Text</script>'});
  assert.match(html, /^<details class="history-entry" data-disclosure-key="history-message:msg">/);
  const summary = html.match(/<summary>(.*?)<\/summary>/s)[1];
  assert.match(summary, /Gemeldet/);
  assert.match(summary, /<strong>Info<\/strong>/);
  assert.match(summary, /Melder: Tor/);
  assert.doesNotMatch(summary, /Hof|Text|script/);
  assert.match(html, /&lt;script&gt;Text&lt;\/script&gt;/);
  assert.match(html, /keine Bestätigung von Empfang/);
});


function deliveryPanel(extra = {}) {
  return panel({site_id: 'Werkstatt', users: {u: {id: 'u', name: 'Ada <Team>', enabled: true, types: [custom.id]}},
    devices: {phone: {id: 'phone', user_id: 'u', name: 'Handy', enabled: true, tested: true,
      platform: 'android', notify_action: 'notify.mobile_app_phone', push: true, sound: true, speech: true, popup: true,
      browsers: [{id: 'browser'}]}}, ...extra});
}

test('source list opens the output probe with its selected fire info or warning source', async () => {
  const p = deliveryPanel();
  const sources = Object.fromEntries(['FIRE', 'INFO', 'WARNING'].map(type => [type, {
    id: type, type, name: type + ' Melder', area: 'Küche', entity_id: 'binary_sensor.' + type.toLowerCase(),
    enabled: true, message: type + ' Testtext'}]));
  p.data.sources = sources;
  p.data.users.u.types = ['FIRE', 'INFO', 'WARNING'];
  const {root} = mount(p);
  p.rememberDetails = p.restoreDetails = p.bindMenus = () => {};
  p.manage = async () => {throw Error('Opening a dialog must not send a test');};
  for (const type of ['FIRE', 'INFO', 'WARNING']) {
    p.renderSourceAdmin();
    assert.match(root.innerHTML, new RegExp('data-go="test-source" data-id="'+type+'"'));
    await root.onclick({target: {closest: () => ({dataset: {go: 'test-source', id: type}})}});
    assert.equal(p.outputTestDialog.kind, type);
    assert.equal(p.outputTestDialog.sourceId, type);
    assert.match(root.innerHTML, new RegExp('value="'+type+'" selected'));
    assert.doesNotMatch(root.innerHTML, /\(Beispiel ohne Melder\)/);
  }
});

test('source shortcut sends its real source identity and does not toggle the sensor', async () => {
  const p = deliveryPanel();
  p.data.sources = {door: {id: 'door', type: custom.id, name: 'Tür', area: 'Eingang', enabled: true}};
  mount(p);
  p.openOutputTest(custom.id, 'door');
  const calls = [];
  p.manage = async (action, data) => {calls.push({action, data: plain(data)});return {test_id: 'ours'};};
  await p.requestOutputTest(p.outputTestDialog, 'sound');
  assert.deepEqual(calls, [{action: 'output_test', data: {id: 'phone', alarm_type: custom.id, output: 'sound', source_id: 'door'}}]);
});

test('source test shortcut rejects deactivated missing or mismatched sources', () => {
  const p = deliveryPanel();
  p.showError = () => {};
  mount(p);
  p.data.sources = {off: {id: 'off', type: custom.id, enabled: false}, wrong: {id: 'wrong', type: 'INFO', enabled: true}};
  for (const id of ['off', 'wrong', 'missing']) {
    p.openOutputTest(custom.id, id);
    assert.equal(p.outputTestDialog, undefined);
  }
});

test('delivery preview intersects profile and device switches and reports readiness honestly', () => {
  const p = deliveryPanel();
  const source = {type: custom.id, name: 'Tür <Ost>', area: 'Eingang', enabled: true};
  let rows = plain(p.deliveryPlan(source));
  assert.deepEqual(rows[0].outputs, ['Ton', 'Fenster']);
  assert.equal(rows[0].reason, '');
  p.data.devices.phone.sound = false;
  p.data.devices.phone.tested = false;
  rows = plain(p.deliveryPlan(source));
  assert.deepEqual(rows[0].outputs, ['Fenster']);
  assert.equal(rows[0].reason, 'Geräteprüfung offen');
  const html = p.renderDeliveryPreview(source);
  assert.match(html, /Wer bekommt was/);
  assert.match(html, /Ada &lt;Team&gt;/);
  assert.match(html, /Tür &lt;Ost&gt;/);
  assert.match(html, /derzeit keine reguläre Ausgabe/);
  assert.match(html, /keine Zustell- oder Erreichbarkeitsbestätigung/);
  p.data.devices.phone.restore_pending = true;
  assert.match(p.renderDeliveryPreview(source), /Wiederherstellung oder Einrichtung läuft/);
  assert.match(p.renderDeliveryPreview({type: custom.id}), /Bereiche werden beim Auslösen ergänzt/);
  assert.match(html, /Achtung. Wasser &lt;Keller&gt;. Standort Werkstatt. Eingang./);
});

test('delivery preview explains disabled and missing recipients and unsupported speech', () => {
  const p = deliveryPanel();
  const source = {type: custom.id, enabled: true};
  p.data.devices.phone.platform = 'ios';
  p.data.alarm_types[custom.id].speech = true;
  assert.deepEqual(plain(p.deliveryPlan(source)[0].outputs), ['Ton', 'Fenster']);
  p.data.users.u.enabled = false;
  assert.equal(p.deliveryPlan(source)[0].reason, 'Benutzer deaktiviert');
  p.data.users.u.enabled = true;
  p.data.devices = {};
  assert.equal(p.deliveryPlan(source)[0].reason, 'Kein Gerät zugeordnet');
  p.data.users.u.types = [];
  assert.match(p.renderDeliveryPreview(source), /Keine Benutzer/);
});

test('message preview uses the actual source text and silent mode removes audio', () => {
  const p = deliveryPanel();
  p.data.alarm_types.INFO = {...p.typeChoices().find(t => t.id === 'INFO'), push: true, sound: true, speech: true, popup: true};
  p.data.users.u.types = ['INFO'];
  const source = {type: 'INFO', name: 'Tor', area: 'Hof', message: 'Bitte das Garagentor schließen.', silent: true, enabled: true};
  assert.deepEqual(plain(p.deliveryPlan(source)[0].outputs), ['Push-Nachricht', 'Fenster']);
  assert.equal(p.sourceSpeechPreview(source), source.message);
  assert.match(p.renderDeliveryPreview(source), /Stumm senden: Ton und Sprache entfallen/);
  p.data.alarm_types.INFO.speech_template = '{name}: {areas} bei {site}';
  assert.equal(p.sourceSpeechPreview(source), 'Info: Hof bei Werkstatt');
});

test('single-output dialog permits unconfirmed devices but limits buttons to enabled outputs', () => {
  const p = deliveryPanel();
  p.data.devices.phone.tested = false;
  const {root} = mount(p);
  p.openOutputTest(custom.id);
  assert.match(root.innerHTML, /Ausgaben testen/);
  assert.match(root.innerHTML, /Geräteprüfung offen/);
  assert.match(root.innerHTML, /keine vollständige Gerätefreigabe/);
  assert.match(root.innerHTML, /normalen Benachrichtigungston ohne erzwungene Lautstärke/);
  assert.match(root.innerHTML, /data-output-test="push" disabled/);
  assert.match(root.innerHTML, /data-output-test="sound" >Ton testen/);
  assert.match(root.innerHTML, /data-output-test="speech" disabled/);
  assert.match(root.innerHTML, /data-output-test="popup" >Fenster testen/);
  p.data.incidents = {active: {type: 'FIRE', status: 'open', started_at: '2026-11-03'}};
  p.renderOutputTest();
  assert.match(root.innerHTML, /data-output-test="sound" disabled/);
});

test('single-output requests use selected device type and source without changing test confirmation', async () => {
  const p = deliveryPanel();
  p.data.sources = {door: {id: 'door', type: custom.id, name: 'Tür', area: 'EG', enabled: true}};
  mount(p);
  p.openOutputTest(custom.id);
  p.outputTestDialog.sourceId = 'door';
  const calls = [];
  p.manage = async (action, data) => {calls.push({action, data: plain(data)});return {test_id: 'token', state: 'requested'};};
  await p.requestOutputTest(p.outputTestDialog, 'sound');
  assert.deepEqual(calls, [{action: 'output_test', data: {id: 'phone', alarm_type: custom.id, output: 'sound', source_id: 'door'}}]);
  assert.equal(p.data.devices.phone.tested, true);
  assert.match(p.outputTestDialog.status, /keinen Empfang/);
  assert.equal(p.outputTestDialog.session.test_id, 'token');
  await p.stopOutputTest(p.outputTestDialog);
  assert.deepEqual(calls[1], {action: 'output_test_stop', data: {id: 'phone', test_id: 'token'}});
});

test('closing while a test request completes cleans only its returned session', async () => {
  const p = deliveryPanel();
  mount(p);p.openOutputTest(custom.id);
  const dialog = p.outputTestDialog;
  let complete;
  const pending = new Promise(resolve => {complete = resolve;});
  const calls = [];
  p.manage = async (action, data) => {calls.push({action, data: plain(data)});if (action === 'output_test')return pending;return {ok: true};};
  const run = p.requestOutputTest(dialog, 'sound');
  await Promise.resolve();
  await p.closeOutputTest(dialog);
  complete({test_id: 'ours'});
  await run;
  assert.equal(p.outputTestDialog, null);
  assert.deepEqual(calls[1], {action: 'output_test_stop', data: {id: 'phone', test_id: 'ours'}});
});

test('single-output requests reject inactive or silent sources before transport', async () => {
  const p = deliveryPanel();
  p.data.alarm_types.INFO = {...p.typeChoices().find(t => t.id === 'INFO'), sound: true, speech: true};
  p.data.users.u.types = ['INFO'];
  p.data.sources = {door: {id: 'door', type: 'INFO', name: 'Tor', silent: true, enabled: true}};
  mount(p);p.openOutputTest('INFO');p.outputTestDialog.sourceId = 'door';
  p.manage = async () => {throw new Error('must not send');};
  await p.requestOutputTest(p.outputTestDialog, 'speech');
  assert.match(p.outputTestDialog.status, /erlaubt die gewählte Testausgabe nicht/);
  p.data.sources.door.silent = false;p.data.sources.door.enabled = false;
  await p.requestOutputTest(p.outputTestDialog, 'push');
  assert.match(p.outputTestDialog.status, /erlaubt die gewählte Testausgabe nicht/);
});


test('test preview matches backend example text and prefixes selected-source text as a test', () => {
  const p = deliveryPanel();
  assert.equal(p.testSpeechPreview(custom.id), 'Test. Achtung. Wasser <Keller>. Standort Werkstatt. Beispielbereich.');
  assert.equal(p.testSpeechPreview('INFO'), 'Test. Dies ist eine Beispielmeldung.');
  assert.equal(p.testSpeechPreview('INFO', {type: 'INFO', name: 'Tor', area: 'Hof', message: 'Tor offen'}), 'Test. Tor offen');
});

test('recovered sessions can be stopped deliberately but closing never stops another tabs test', async () => {
  const p = deliveryPanel({output_test_sessions: {phone: {test_id: 'existing', alarm_type: custom.id, output: 'sound', state: 'requested'}}});
  const {root} = mount(p);p.openOutputTest(custom.id);
  assert.equal(p.outputTestDialog.session.owned, false);
  assert.match(root.innerHTML, /data-output-test="sound" disabled/);
  const calls = [];
  p.manage = async (action, data) => {calls.push({action, data: plain(data)});return {ok: true};};
  const dialog = p.outputTestDialog;
  await p.closeOutputTest(dialog);
  assert.equal(calls.length, 0);
  p.openOutputTest(custom.id);
  await p.stopOutputTest(p.outputTestDialog);
  assert.deepEqual(calls, [{action: 'output_test_stop', data: {id: 'phone', test_id: 'existing'}}]);
});

test('failed transport recovers a pending cleanup token from the refreshed admin snapshot', async () => {
  const p = deliveryPanel();
  mount(p);p.openOutputTest(custom.id);
  p._hass.callWS = async () => {};
  p.load = async () => {p.data.output_test_sessions = {phone: {test_id: 'cleanup', state: 'cleanup_pending'}};};
  p.manage = async () => {throw new Error('Transport fehlgeschlagen');};
  await p.requestOutputTest(p.outputTestDialog, 'sound');
  assert.equal(p.outputTestDialog.session.test_id, 'cleanup');
  assert.match(p.outputTestDialog.status, /Transport fehlgeschlagen/);
});

test('global recovery state blocks new test requests and stopping accepted test audio', async () => {
  const p = deliveryPanel();
  const {root} = mount(p);p.openOutputTest(custom.id);
  p.data.output_tests_blocked = 'Wiederherstellung läuft';
  p.outputTestDialog.session = {test_id: 'ours', device_id: 'phone', owned: true};
  p.renderOutputTest();
  assert.match(root.innerHTML, /Wiederherstellung läuft/);
  assert.match(root.innerHTML, /id="output-test-stop" disabled/);
  p.manage = async () => {throw new Error('must not send');};
  await assert.rejects(p.stopOutputTest(p.outputTestDialog), /Wiederherstellung läuft/);
});

test('source assignment refreshes only its delivery summary after a field change', () => {
  const p = deliveryPanel();
  const {root} = mount(p);
  p.wizard = {kind: 'source', step: 1, draft: {type: custom.id, name: 'Tür', area: 'Alt', enabled: true}};
  p.captureWizard = () => {p.wizard.draft.area = 'Neu';};
  p.renderWizard();
  const before = root.innerHTML;
  root.querySelector('#wizard-form').onchange({target: {name: 'area'}});
  assert.equal(root.innerHTML, before);
  assert.match(root.querySelector('#source-delivery-preview').innerHTML, /Neu/);
});


test('incident timeline uses names and German events while technical identifiers stay folded away', () => {
  const p = panel({users: {user: {id: 'user', name: 'Jan Pohl'}}, devices: {phone: {id: 'phone', name: 'Jan S22'}}});
  const i = {id: 'event-id', sources: {rawsource: {id: 'rawsource', name: 'Testmelder <Tür>'}},
    audit: [{at: '2026-11-04T18:29:22Z', action: 'source_added', source_id: 'rawsource'},
      {at: '2026-11-04T18:29:33Z', action: 'sound_stopped_by_response', user_id: 'user'},
      {at: '2026-11-04T18:29:40Z', action: 'false_alarm', user_id: 'user'}],
    delivery: [{at: '2026-11-04T18:29:22Z', device_id: 'phone', state: 'requested', detail: 'notify.mobile_app_sm_s908b_jan'}]};
  const html = p.incidentTimeline(i);
  const human = html.split('<details class="timeline-technical"')[0];
  assert.match(human, /Melder hinzugefügt/);
  assert.match(human, /Testmelder &lt;Tür&gt;/);
  assert.match(human, /Alarmierung gestoppt/);
  assert.match(human, /Fehlalarm bestätigt/);
  assert.match(human, /Jan Pohl/);
  assert.match(human, /Jan S22/);
  assert.doesNotMatch(human, /source_added|sound_stopped_by_response|rawsource|notify\.mobile_app/);
  assert.match(html, /data-disclosure-key="incident-log:event-id"/);
  assert.match(html, /data-disclosure-key="incident-tech:event-id"/);
  assert.match(html, /<summary>Technische Details<\/summary>/);
  assert.match(html, /source_added/);
  assert.match(html, /notify\.mobile_app_sm_s908b_jan/);
  assert.doesNotMatch(html, /<Tür>/);
});

test('transport timeline groups only nearby identical requests and retains meaningful warnings', () => {
  const p = panel({devices: {phone: {name: 'Handy'}}});
  const request = at => ({at, device_id: 'phone', state: 'requested', detail: 'notify.mobile_app_phone'});
  const i = {id: 'event', sources: {}, audit: [], delivery: [request('2026-11-04T18:29:22Z'), request('2026-11-04T18:29:23Z'),
    {at: '2026-11-04T18:29:33Z', device_id: 'phone', state: 'receipt_timeout', detail: 'No receipt rawdetail'},
    request('2026-11-04T18:29:34Z'), request('2026-11-04T18:29:40Z'),
    {at: '2026-11-04T18:29:41Z', device_id: 'phone', state: 'notification_received', detail: 'received'}]};
  const html = p.incidentTimeline(i).split('<details class="timeline-technical"')[0];
  assert.match(html, /2 Anfragen zusammengefasst/);
  assert.equal((html.match(/Ausgabe angefordert/g) || []).length, 3);
  assert.match(html, /timeline-row warning/);
  assert.match(html, /Empfangsbestätigung fehlt/);
  assert.match(html, /Empfang vom Handy bestätigt/);
  assert.match(html, /nicht die Ton- oder Sprachwiedergabe/);
  assert.doesNotMatch(html, /receipt_timeout|No receipt rawdetail/);
});

test('timeline handles missing names and unknown actions without exposing raw identifiers', () => {
  const p = panel();
  const rows = Array.from({length: 31}, (_, n) => ({at: '2026-11-04T18:29:22Z', device_id: 'hidden-device', state: 'new_state', detail: '<script>unsafe</script>'}));
  const html = p.incidentTimeline({id: 'x', sources: {}, audit: [{at: '2026-11-04T18:29:22Z', action: 'raw_new_action', source_id: 'hidden-source'}], delivery: rows});
  const human = html.split('<details class="timeline-technical"')[0];
  assert.match(human, /Melder nicht mehr zugeordnet/);
  assert.match(human, /Gerät nicht mehr zugeordnet/);
  assert.match(human, /Weiterer Ereigniseintrag/);
  assert.match(human, /letzten 30 von 31 Transporteinträgen/);
  assert.doesNotMatch(human, /hidden-device|hidden-source|raw_new_action|new_state|unsafe/);
  assert.match(html, /&lt;script&gt;unsafe&lt;\/script&gt;/);
  assert.doesNotMatch(html, /<script>/);
});

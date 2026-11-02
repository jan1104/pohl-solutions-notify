"""Validate configuration exports before replacing any live settings."""
from copy import deepcopy
from math import isfinite
from .model import AlarmModel
from .const import TYPES

def prepare_import(current, document, accounts, states, notify_actions):
    if not isinstance(document, dict) or document.get('format') != 'alarm_system_configuration' or document.get('schema_version') != 1:
        raise ValueError('Keine unterstützte Alarm-Einrichtungssicherung (Schema 1)')
    if AlarmModel(current).active() or current.get('leases'):
        raise ValueError('Vor dem Import aktive Alarme beenden und die Handy-Wiederherstellung abschließen')
    if document.get('site_id') != current['site_id']:
        raise ValueError('Die Sicherung gehört zu einem anderen Standort')
    mode = document.get('retention_mode', 'unlimited')
    if mode not in ('unlimited', '30d', '3m', '5m', '12m', '4y'):
        raise ValueError('Ungültige Aufbewahrungsdauer')
    for key in ('users', 'devices', 'sources'):
        if not isinstance(document.get(key), dict) or len(document[key]) > 1000:
            raise ValueError('Ungültige Liste: ' + key)
    staged = AlarmModel(current)
    staged.data.update(users={}, devices={}, sources={}, signal_values={}, retention_mode=mode)
    for uid, record in document['users'].items():
        if not isinstance(record, dict) or record.get('id') != uid or uid not in accounts:
            raise ValueError('HA-Konto nicht vorhanden oder ungültige Konto-ID: ' + str(uid))
        types = record.get('types', [])
        if not isinstance(types, list) or any(t not in TYPES for t in types):
            raise ValueError('Ungültige Alarmarten für ein Konto')
        staged.data['users'][uid] = {'id': uid, 'name': accounts[uid], 'types': list(dict.fromkeys(types)), 'enabled': bool(record.get('enabled', True))}
    phones, browsers = set(), set()
    for did, record in document['devices'].items():
        if not isinstance(record, dict) or record.get('id') != did or record.get('user_id') not in staged.data['users']:
            raise ValueError('Ungültige Geräte-/Benutzerzuordnung')
        device = deepcopy(record)
        if device.get('platform') not in ('android', 'ios', 'browser'):
            raise ValueError('Ungültige Geräteplattform')
        action = device.get('notify_action', '')
        if device['platform'] != 'browser' and action not in notify_actions:
            raise ValueError('Companion-Notify-Dienst fehlt: ' + str(action))
        if action and action in phones: raise ValueError('Handy ist mehrfach zugeordnet')
        if action: phones.add(action)
        if not isinstance(device.get('browsers', []), list): raise ValueError('Ungültige Browserliste')
        for b in device.get('browsers', []):
            if not isinstance(b, dict) or not isinstance(b.get('id'), str) or not b['id'] or b['id'] in browsers:
                raise ValueError('Ungültige oder doppelte Browser-ID')
            browsers.add(b['id'])
        for field, default, maximum in (('fire_seconds', 5, 15), ('intrusion_seconds', 5, 15), ('speech_seconds', 8, 12)):
            value = float(device.get(field, default))
            if not isfinite(value) or not 1 <= value <= maximum: raise ValueError('Ungültige Ton-/Sprachdauer')
            device[field] = value
        device.update(tested=False, category_setup={})
        device.pop('tested_at', None)
        for key in ('setup_pending', 'setup_categories', 'setup_error', 'setup_running',
                    'setup_restore_pending', 'restore_pending', 'setup_retry_at',
                    'test_session', '_sensor_phone', '_audio_baseline'):
            device.pop(key, None)
        staged.data['devices'][did] = device
    for sid, record in document['sources'].items():
        if not isinstance(record, dict) or record.get('id') != sid or record.get('entity_id') not in states:
            raise ValueError('Binary-Sensor fehlt oder Melder-ID ungültig: ' + str(sid))
        staged.register_source(record, states[record['entity_id']])
    # No imported state, history, recovery leases or credentials can enter here.
    return staged.snapshot()


def completed_device_tests(data, device):
    """Tests count only for the current verification session and after completion."""
    session = device.get("test_session")
    return {i["type"] for i in data.get("incidents", {}).values()
            if session and i.get("test_device") == device["id"]
            and i.get("test_session") == session and i.get("status") in ("ended", "false_alarm")}


def user_view(data, user_id):
    """Keep only authorized messages and the current account's settings."""
    for field in ('available_users', 'notify_actions', 'phone_connections', 'browser_connections'):
        data.pop(field, None)
    account = data['users'].get(user_id, {})
    enabled = bool(account and account.get('enabled', True))
    allowed = account.get('types', []) if enabled else []
    hidden_tests = {k for k, i in data['incidents'].items() if i.get('test_device') and data['devices'].get(i['test_device'], {}).get('user_id') != user_id}
    data['incidents'] = {k: i for k, i in data['incidents'].items() if i['type'] in allowed and
                         (not i.get('test_device') or data['devices'].get(i['test_device'], {}).get('user_id') == user_id)}
    data['sources'] = {k: s for k, s in data['sources'].items() if s['type'] in allowed}
    data['signal_values'] = {k: v for k, v in data.get('signal_values', {}).items() if k in data['sources']}
    data['journal'] = [e for e in data['journal'] if e['type'] in allowed and e.get('incident_id') not in hidden_tests]
    data['devices'] = {k: d for k, d in data['devices'].items() if enabled and d['user_id'] == user_id}
    data['users'] = {k: ({'id': u['id'], 'name': u['name'], 'types': list(u.get('types', [])), 'enabled': u.get('enabled', True)}
                        if k == user_id else {'id': u['id'], 'name': u['name']})
                     for k, u in data['users'].items() if enabled or k == user_id}
    return data

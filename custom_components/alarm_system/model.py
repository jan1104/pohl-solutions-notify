"""Persistent, platform-independent incident state. No HA imports."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from calendar import monthrange
from uuid import uuid4


def stamp():
    return datetime.now(timezone.utc).isoformat()


class AlarmModel:
    def __init__(self, saved=None, site_id="LW20"):
        self.data = deepcopy(saved) if saved else {
            "site_id": site_id, "retention_days": 0, "users": {}, "devices": {},
            "incidents": {}, "suppressed": {}, "leases": {}, "sources": {}, "signal_values": {},
        }
        for key in ("users", "devices", "incidents", "suppressed", "leases", "sources", "signal_values"):
            self.data.setdefault(key, {})
        self.data.setdefault("retention_days", 0)
        self.data.setdefault("retention_mode", "unlimited")
        self.data.setdefault("journal", [])

    def log(self, action, *, kind=None, incident=None, source=None, user_id=None,
            user_name=None, device=None, browser_id=None, text="", details=None):
        if not source and incident:
            selected = [s for s in incident.get("sources", {}).values() if s.get("active")]
            if not selected:
                selected = list(incident.get("sources", {}).values())
            source = {field: " | ".join(dict.fromkeys(str(s.get(field, "")) for s in selected if s.get(field)))
                      for field in ("id", "name", "area", "detection", "entity_id")}
        source = source or {}
        device = device or {}
        entry = {"id": uuid4().hex, "at": stamp(), "action": action,
            "type": kind or (incident or {}).get("type", ""),
            "site_id": self.data["site_id"], "incident_id": (incident or {}).get("id", ""),
            "user_id": user_id or "", "user_name": user_name or self.data["users"].get(user_id, {}).get("name") or (user_id if user_id else "System"),
            "device_id": device.get("id", ""), "device_name": device.get("name", ""),
            "browser_id": browser_id or "", "source_id": source.get("id", ""),
            "source_name": source.get("name", source.get("source_name", "")),
            "entity_id": source.get("entity_id", ""), "area": source.get("area", ""),
            "detection": source.get("detection", ""), "text": text,
            "details": deepcopy(details or {})}
        self.data["journal"].append(entry)
        if incident:
            matched = {"alarm_raised": "source_added", "end_source": "source_ended"}.get(action, action)
            if incident.get("audit") and incident["audit"][-1]["action"] == matched:
                incident["audit"][-1].setdefault("journal_id", entry["id"])
            state = {"notification_requested": "requested", "popup_requested": "popup_requested", "popup_status_requested": "popup_status_requested", "popup_error": "popup_error", "transport_error": "error"}.get(action)
            if state and incident.get("delivery") and incident["delivery"][-1]["state"] == state:
                incident["delivery"][-1].setdefault("journal_id", entry["id"])
        return entry

    def snapshot(self):
        return deepcopy(self.data)

    def active(self):
        return [i for i in self.data["incidents"].values() if i["status"] in ("open", "claimed")]

    def recipients(self, kind):
        return [d for d in self.data["devices"].values()
                if d.get("enabled") and d.get("tested")
                and (u := self.data["users"].get(d["user_id"]))
                and u.get("enabled", True) and kind in u.get("types", [])]

    def recipient_transport(self, incident, user_id, recipients):
        ids = {d['id'] for d in recipients if d['user_id'] == user_id}
        entries = incident.get('delivery', [])
        requested = {e['device_id'] for e in entries if e.get('state') in ('requested', 'popup_requested') and e.get('device_id') in ids}
        errors = {e['device_id'] for e in entries if e.get('state') in ('error', 'popup_error') and e.get('device_id') in ids}
        return {'total': len(ids), 'requested': len(requested), 'errors': len(errors)}

    def audience(self, kind):
        return [u for u in self.data["users"].values()
                if u.get("enabled", True) and kind in u.get("types", [])
                and any(d["user_id"] == u["id"] and d.get("tested") and d.get("enabled")
                        for d in self.data["devices"].values())]

    def authorized(self, user_id, incident):
        u = self.data["users"].get(user_id)
        return bool(u and u.get("enabled", True) and incident["type"] in u.get("types", []))

    def register_source(self, payload, current_state=None):
        source_id = payload.get("id") or uuid4().hex
        old = self.data["sources"].get(source_id, {})
        entity_id = str(payload.get("entity_id", ""))
        name = str(payload.get("name", "")).strip()
        kind = payload.get("type", "FIRE")
        if not entity_id.startswith("binary_sensor.") or not name or kind not in ("INFO", "WARNING", "FIRE", "INTRUSION"):
            raise ValueError("Meldername, Binary-Sensor und gültige Alarmart erforderlich")
        if any(x["entity_id"] == entity_id and x["id"] != source_id for x in self.data["sources"].values()):
            raise ValueError("Dieser Binary-Sensor ist bereits zugeordnet")
        url = str(payload.get("url", "")).strip()
        if url and (not url.startswith("/") or url.startswith("//")):
            raise ValueError("HA-Seite als internen Pfad angeben, zum Beispiel /lovelace/energie")
        key = str(payload.get("alarm_key", "")).strip() or {"FIRE": "Feueralarm Gebäude", "INTRUSION": "Einbruchalarm Gebäude"}.get(kind, name)
        changed = any(old.get(k) != value for k, value in (("entity_id", entity_id), ("type", kind), ("alarm_key", key)))
        if old and changed and any(source_id in i["sources"] and i["sources"][source_id]["active"] for i in self.active()):
            raise ValueError("Vor dem Ändern der Signalzuordnung die aktive Melderzeile beenden")
        if kind in ("FIRE", "INTRUSION") and (any(x["alarm_key"] == key and x["type"] != kind and x["type"] in ("FIRE", "INTRUSION") and x["id"] != source_id for x in self.data["sources"].values()) or any(i["alarm_key"] == key and i["type"] != kind for i in self.active())):
            raise ValueError("Eine Ereignisgruppe darf nur eine Alarmart enthalten")
        source = {"id": source_id, "name": name, "entity_id": entity_id, "type": kind,
                  "alarm_key": key, "area": str(payload.get("area", "")),
                  "detection": str(payload.get("detection", "")), "camera": str(payload.get("camera", "")),
                  "message": str(payload.get("message", "")), "url": url, "enabled": bool(payload.get("enabled", True)),
                  "silent": bool(payload.get("silent", False)), "graph_entity": str(payload.get("graph_entity", "")),
                  "graph_minutes": max(1, min(1440, int(payload.get("graph_minutes", 15))))}
        self.data["sources"][source_id] = source
        if not old or old.get("entity_id") != entity_id:
            # Saving a binding never generates an alarm implicitly.
            self.data["signal_values"][source_id] = current_state if current_state in ("on", "off") else None
        return source

    def remove_source(self, source_id):
        if any(source_id in i["sources"] and i["sources"][source_id]["active"] for i in self.active()):
            raise ValueError("Zuerst die aktive Melderzeile beenden; alternativ den Eintrag deaktivieren")
        self.data["sources"].pop(source_id, None)
        self.data["signal_values"].pop(source_id, None)

    def signal_update(self, entity_id, state):
        """Translate a final input signal into metadata, never evaluate detection logic."""
        source = next((s for s in self.data["sources"].values() if s["entity_id"] == entity_id), None)
        if not source or state not in ("on", "off"):
            return None
        previous = self.data["signal_values"].get(source["id"])
        self.data["signal_values"][source["id"]] = state
        if state == "off":
            self.normal(source["alarm_key"], source["id"])
            return None
        if previous == "on" or not source["enabled"]:
            return None
        return {"type": source["type"], "alarm_key": source["alarm_key"], "source_id": source["id"],
                "source_name": source["name"], "entity_id": entity_id, "title": source["alarm_key"],
                "message": source["message"] or f'{source["name"]} · {source["area"]}',
                "area": source["area"], "detection": source["detection"], "camera": source["camera"],
                "url": source.get("url", ""), "silent": source["silent"], "graph_entity": source["graph_entity"], "graph_minutes": source["graph_minutes"]}

    def raise_alarm(self, payload):
        kind = payload["type"]
        if kind not in ("FIRE", "INTRUSION"):
            raise ValueError("Only FIRE/INTRUSION create incidents")
        key, source_id = payload["alarm_key"], payload["source_id"]
        suppression = f"{key}|{source_id}"
        if suppression in self.data["suppressed"]:
            return None, "suppressed"
        incident = next((i for i in self.active() if i["alarm_key"] == key), None)
        if incident and incident["type"] != kind:
            raise ValueError("alarm_key already belongs to another alarm type")
        created = incident is None
        if created:
            incident = {
                "id": uuid4().hex, "alarm_key": key, "type": kind,
                "title": payload.get("title") or kind, "site_id": self.data["site_id"],
                "started_at": stamp(), "ended_at": None, "status": "open",
                "sources": {}, "responses": {}, "audit": [], "delivery": [],
                "next_due": 0,
            }
            self.data["incidents"][incident["id"]] = incident
        sources = incident["sources"]
        if source_id in sources and sources[source_id]["active"]:
            sources[source_id]["signal_active"] = True
            return incident, "duplicate"
        sources[source_id] = {
            "id": source_id, "name": payload.get("source_name", source_id),
            "area": payload.get("area", ""), "detection": payload.get("detection", ""),
            "camera": payload.get("camera", ""), "entity_id": payload.get("entity_id", ""),
            "triggered_at": stamp(), "active": True, "signal_active": True,
            "ended_at": None, "ended_by": None,
        }
        # A new source in an already claimed incident does not reopen its sound cycle.
        self.audit(incident, "source_added", None, source_id)
        return incident, "new" if created else "source_added"

    def audit(self, incident, action, actor, source=None):
        incident["audit"].append({"at": stamp(), "action": action, "user_id": actor, "source_id": source, "name": self.data["users"].get(actor, {}).get("name") or actor or "System"})

    def view(self, incident_id, user_id, user_name=None):
        incident = self.data['incidents'][incident_id]
        if incident not in self.active():
            return False
        views = incident.setdefault('views', {})
        if user_id in views:
            return False
        views[user_id] = {'at': stamp(), 'name': user_name or self.data['users'].get(user_id, {}).get('name') or 'Name nicht verfügbar'}
        self.audit(incident, 'viewed', user_id)
        return True

    def come(self, incident_id, user_id, user_name=None):
        incident = self.data["incidents"][incident_id]
        if incident not in self.active():
            raise ValueError("Incident already ended")
        name = user_name or self.data["users"].get(user_id, {}).get("name")
        # A response only claims the selected incident, including device tests.
        targets = [incident]
        for current in targets:
            if current["status"] == "open":
                current["status"] = "claimed"
                current["silenced_by"] = user_id
                current["silenced_by_name"] = name or "Name nicht verfügbar"
                current["silenced_at"] = stamp()
                self.audit(current, "sound_stopped_by_response", user_id)
        incident["responses"][user_id] = {"answer": "coming", "at": stamp(), "name": name or "Name nicht verfügbar"}
        self.audit(incident, "coming", user_id)
        return incident

    def end_source(self, incident_id, source_id, user_id):
        incident = self.data["incidents"][incident_id]
        source = incident["sources"][source_id]
        if not source["active"]:
            return incident
        source.update(active=False, ended_at=stamp(), ended_by=user_id)
        if source["signal_active"]:
            self.data["suppressed"][f'{incident["alarm_key"]}|{source_id}'] = source.get("entity_id", "")
        self.audit(incident, "source_ended", user_id, source_id)
        if not any(s["active"] for s in incident["sources"].values()):
            incident.update(status="ended", ended_at=stamp())
        return incident

    def false_alarm(self, incident_id, user_id):
        incident = self.data["incidents"][incident_id]
        if incident not in self.active():
            raise ValueError("Incident already ended")
        for source_id in list(incident["sources"]):
            self.end_source(incident_id, source_id, user_id)
        incident.update(status="false_alarm", ended_at=stamp(), ended_by=user_id)
        self.audit(incident, "false_alarm", user_id)
        return incident

    def normal(self, alarm_key, source_id):
        self.data["suppressed"].pop(f"{alarm_key}|{source_id}", None)
        for i in self.data["incidents"].values():
            if i["alarm_key"] == alarm_key and source_id in i["sources"]:
                i["sources"][source_id]["signal_active"] = False
                # No automatic incident/source closure on a normal signal.

    def purge(self, now=None):
        mode = self.data.get("retention_mode", "unlimited")
        if mode == "unlimited":
            return
        now = now or datetime.now(timezone.utc)
        if mode == "30d":
            cutoff = now - timedelta(days=30)
        else:
            months = {"3m": 3, "5m": 5, "12m": 12, "4y": 48}[mode]
            year, month0 = divmod(now.year * 12 + now.month - 1 - months, 12)
            month = month0 + 1
            cutoff = now.replace(year=year, month=month, day=min(now.day, monthrange(year, month)[1]))
        self.data["incidents"] = {
            k: i for k, i in self.data["incidents"].items()
            if not i.get("ended_at") or datetime.fromisoformat(i["ended_at"]) > cutoff
        }
        active_ids = {i["id"] for i in self.active()}
        self.data["journal"] = [e for e in self.data["journal"]
            if e.get("incident_id") in active_ids or datetime.fromisoformat(e["at"]) > cutoff]


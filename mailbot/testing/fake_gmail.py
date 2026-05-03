"""
Minimal Gmail API surface used by mailbot.gmail_ops, backed by in-memory state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from email.utils import parseaddr
from typing import Any, Callable


class _Req:
    def __init__(self, fn: Callable[[], dict[str, Any]]):
        self._fn = fn

    def execute(self) -> dict[str, Any]:
        return self._fn()


@dataclass
class _Msg:
    mid: str
    internal_date: int
    from_header: str
    subject: str
    snippet: str
    label_ids: list[str] = field(default_factory=lambda: ["INBOX"])


def _from_email(from_header: str) -> str:
    _, addr = parseaddr(from_header)
    return (addr or "").strip().lower()


def _match_query(m: _Msg, q: str) -> bool:
    if not q:
        return True
    for p in q.split():
        if p == "in:inbox":
            if "INBOX" not in m.label_ids:
                return False
        elif p.startswith("from:"):
            spec = p[5:].lower()
            fe = _from_email(m.from_header)
            if spec.startswith("*@"):
                dom = spec[2:]
                if not fe.endswith("@" + dom):
                    return False
            else:
                if fe != spec:
                    return False
    return True


class _MessagesPart:
    def __init__(self, root: "FakeGmailService"):
        self._root = root

    def list(self, userId: str = "me", q: str | None = None, maxResults: int = 100, pageToken: str | None = None) -> _Req:
        def run() -> dict[str, Any]:
            qn = (q or "").strip()
            mids = [m.mid for m in self._root._messages.values() if _match_query(m, qn)]
            mids.sort(key=lambda mid: self._root._messages[mid].internal_date, reverse=True)
            slice_ids = mids[: maxResults or 100]
            return {"messages": [{"id": mid} for mid in slice_ids], "nextPageToken": None}

        return _Req(run)

    def get(
        self,
        userId: str = "me",
        id: str | None = None,
        format: str | None = None,
        metadataHeaders: list[str] | None = None,
    ) -> _Req:
        mid = id or ""

        def run() -> dict[str, Any]:
            m = self._root._messages[mid]
            headers = [
                {"name": "From", "value": m.from_header},
                {"name": "Subject", "value": m.subject},
                {"name": "Date", "value": "Mon, 1 Jan 2024 00:00:00 +0000"},
            ]
            return {
                "id": m.mid,
                "threadId": f"th-{m.mid}",
                "internalDate": str(m.internal_date),
                "snippet": m.snippet,
                "labelIds": list(m.label_ids),
                "payload": {"headers": headers},
            }

        return _Req(run)

    def batchModify(self, userId: str = "me", body: dict[str, Any] | None = None) -> _Req:
        def run() -> dict[str, Any]:
            self._root.batch_modify_calls.append(dict(body or {}))
            ids = (body or {}).get("ids") or []
            add = (body or {}).get("addLabelIds") or []
            remove = (body or {}).get("removeLabelIds") or []
            for mid in ids:
                m = self._root._messages.get(mid)
                if not m:
                    continue
                for lid in add:
                    if lid not in m.label_ids:
                        m.label_ids.append(lid)
                for lid in remove:
                    if lid in m.label_ids:
                        m.label_ids.remove(lid)
            return {}

        return _Req(run)


class _LabelsPart:
    def __init__(self, root: "FakeGmailService"):
        self._root = root

    def list(self, userId: str = "me") -> _Req:
        def run() -> dict[str, Any]:
            labs = []
            for lid, name in self._root._labels.items():
                ltype = "user" if str(lid).startswith("Label_") else "system"
                labs.append({"id": lid, "name": name, "type": ltype})
            return {"labels": labs}

        return _Req(run)

    def create(self, userId: str = "me", body: dict[str, Any] | None = None) -> _Req:
        def run() -> dict[str, Any]:
            name = (body or {}).get("name") or "label"
            lid = f"Label_{self._root._next_label}"
            self._root._next_label += 1
            self._root._labels[lid] = name
            return {"id": lid, "name": name}

        return _Req(run)


class FakeGmailService:
    """Implements the googleapiclient-style call chain used by gmail_ops."""

    def __init__(self, account_id: str, profile_email: str, messages: list[_Msg]):
        self.account_id = account_id
        self.profile_email = profile_email
        self._messages: dict[str, _Msg] = {m.mid: m for m in messages}
        self._labels: dict[str, str] = {"INBOX": "INBOX", "UNREAD": "UNREAD"}
        self._next_label = 1
        self.batch_modify_calls: list[dict[str, Any]] = []
        self._messages_part = _MessagesPart(self)
        self._labels_part = _LabelsPart(self)

    def users(self) -> FakeGmailService:
        return self

    def messages(self) -> _MessagesPart:
        return self._messages_part

    def labels(self) -> _LabelsPart:
        return self._labels_part

    def getProfile(self, userId: str = "me") -> _Req:
        return _Req(lambda: {"emailAddress": self.profile_email})


_FAKE_REGISTRY: dict[str, FakeGmailService] = {}


def _seed(account_id: str) -> FakeGmailService:
    if account_id == "personal":
        msgs = [
            _Msg("p-new", 4_000_000, "Shop <shop@store.example>", "Sale today", "Snippet sale"),
            _Msg("p-mid", 3_000_000, "Shop <shop@store.example>", "Newsletter", "Snippet news"),
            _Msg("p-old", 2_000_000, "Shop <shop@store.example>", "Welcome", "Snippet welcome"),
            _Msg("p-boss", 3_500_000, "Boss <boss@corp.example>", "Please read", "Important"),
        ]
        return FakeGmailService("personal", "personal@example.com", msgs)
    if account_id == "work":
        msgs = [
            _Msg("w-1", 2_800_000, "Alerts <alerts@corp.example>", "Build failed", "CI failure"),
        ]
        return FakeGmailService("work", "work@example.com", msgs)
    return FakeGmailService(account_id, f"{account_id}@example.com", [])


def get_fake_gmail(account_id: str) -> FakeGmailService:
    if account_id not in _FAKE_REGISTRY:
        _FAKE_REGISTRY[account_id] = _seed(account_id)
    return _FAKE_REGISTRY[account_id]


def reset_fake_registry() -> None:
    _FAKE_REGISTRY.clear()

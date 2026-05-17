from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dev_workbench.models import (
    AdoConfig,
    AdoPostUpdateResult,
    AdoTicket,
    AdoTicketDetail,
    AdoTicketDraft,
    AdoTicketList,
    TicketNote,
)
from dev_workbench.storage import connect
from dev_workbench.work import WorkbenchService

DEFAULT_QUERY = """
SELECT [System.Id]
FROM WorkItems
WHERE [System.AssignedTo] = @Me
  AND [System.State] <> 'Closed'
  AND [System.TeamProject] = @project
ORDER BY [System.ChangedDate] DESC
""".strip()

CONFIG_ENV = {
    "organization_url": "WORKBENCH_ADO_ORGANIZATION_URL",
    "project": "WORKBENCH_ADO_PROJECT",
    "default_query": "WORKBENCH_ADO_DEFAULT_QUERY",
    "auth_mode": "WORKBENCH_ADO_AUTH_MODE",
    "personal_access_token_env_var": "WORKBENCH_ADO_PAT_ENV_VAR",
}


class AdoConfigurationError(ValueError):
    pass


class AdoPermissionError(ValueError):
    pass


class AzureDevOpsClient:
    def __init__(self, config: AdoConfig):
        self.config = config

    def list_tickets(self) -> list[AdoTicket]:
        self._require_ready()
        query = self.config.default_query or DEFAULT_QUERY
        payload = self._request_json(
            "POST",
            f"{self._project_base()}/_apis/wit/wiql?api-version=7.1",
            {"query": query},
        )
        ids = [item["id"] for item in payload.get("workItems", [])[:50]]
        return self._get_work_items(ids, include_description=False)

    def get_ticket(self, ticket_id: int) -> AdoTicket:
        self._require_ready()
        tickets = self._get_work_items([ticket_id], include_description=True)
        if not tickets:
            raise AdoConfigurationError(f"Azure DevOps ticket not found: {ticket_id}")
        return tickets[0]

    def post_comment(self, ticket_id: int, body: str) -> None:
        self._require_ready()
        self._request_json(
            "POST",
            f"{self._project_base()}/_apis/wit/workItems/{ticket_id}/comments?api-version=7.1-preview.4",
            {"text": body},
        )

    def _get_work_items(self, ids: list[int], *, include_description: bool) -> list[AdoTicket]:
        if not ids:
            return []
        fields = [
            "System.Id",
            "System.Title",
            "System.State",
            "System.AssignedTo",
            "System.WorkItemType",
        ]
        if include_description:
            fields.append("System.Description")
        url = (
            f"{self._org_base()}/_apis/wit/workitems"
            f"?ids={','.join(str(item) for item in ids)}"
            f"&fields={quote(','.join(fields))}"
            "&api-version=7.1"
        )
        payload = self._request_json("GET", url)
        return [_ticket_from_work_item(item) for item in payload.get("value", [])]

    def _request_json(self, method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._basic_token()}",
        }
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise AdoConfigurationError(f"Azure DevOps request failed: HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise AdoConfigurationError(f"Azure DevOps request failed: {exc.reason}") from exc
        return json.loads(response_body) if response_body else {}

    def _require_ready(self) -> None:
        if not self.config.configured or not self.config.token_available:
            raise AdoConfigurationError(self.config.setup_guidance or "Azure DevOps is not configured.")

    def _basic_token(self) -> str:
        env_var = self.config.personal_access_token_env_var
        token = os.environ.get(env_var or "") if env_var else None
        if not token:
            raise AdoConfigurationError(self.config.setup_guidance or "Azure DevOps token is unavailable.")
        return base64.b64encode(f":{token}".encode("utf-8")).decode("ascii")

    def _org_base(self) -> str:
        return (self.config.organization_url or "").rstrip("/")

    def _project_base(self) -> str:
        return f"{self._org_base()}/{quote(self.config.project or '')}"


@dataclass
class AzureDevOpsService:
    db_path: Path | None = None
    client: AzureDevOpsClient | None = None

    def get_config(self) -> AdoConfig:
        values = _read_config(self.db_path)
        merged = {key: os.environ.get(env_name) or values.get(key) for key, env_name in CONFIG_ENV.items()}
        auth_mode = merged.get("auth_mode") or "pat_env"
        pat_env_var = merged.get("personal_access_token_env_var") or "AZURE_DEVOPS_EXT_PAT"
        config = AdoConfig(
            organization_url=merged.get("organization_url"),
            project=merged.get("project"),
            default_query=merged.get("default_query") or DEFAULT_QUERY,
            auth_mode=auth_mode,
            personal_access_token_env_var=pat_env_var if auth_mode == "pat_env" else None,
        )
        config.configured = bool(config.organization_url and config.project and config.auth_mode)
        config.token_available = bool(
            config.configured
            and config.auth_mode == "pat_env"
            and config.personal_access_token_env_var
            and os.environ.get(config.personal_access_token_env_var)
        )
        if not config.configured:
            config.setup_guidance = (
                "Set WORKBENCH_ADO_ORGANIZATION_URL and WORKBENCH_ADO_PROJECT. "
                "For PAT auth, set WORKBENCH_ADO_PAT_ENV_VAR to the env var name that contains the token."
            )
        elif config.auth_mode != "pat_env":
            config.setup_guidance = "Only auth_mode=pat_env is currently implemented for Azure DevOps REST calls."
        elif not config.token_available:
            config.setup_guidance = (
                f"Set {config.personal_access_token_env_var} in the local shell. "
                "The token value is read from the environment and is never stored in SQLite."
            )
        return config

    def list_tickets(self) -> AdoTicketList:
        config = self.get_config()
        if not config.configured or not config.token_available:
            return AdoTicketList(tickets=[], config=config)
        return AdoTicketList(tickets=self._client(config).list_tickets(), config=config)

    def get_ticket_detail(self, ticket_id: int) -> AdoTicketDetail:
        config = self.get_config()
        if not config.configured or not config.token_available:
            ticket = AdoTicket(id=ticket_id, title=f"Azure DevOps #{ticket_id}")
        else:
            ticket = self._client(config).get_ticket(ticket_id)
        return AdoTicketDetail(
            ticket=ticket,
            notes=self.list_notes(str(ticket_id)),
            latest_draft=self.latest_draft(str(ticket_id)),
            config=config,
        )

    def add_note(self, ticket_id: int, text: str) -> TicketNote:
        return WorkbenchService(self.db_path).add_ticket_note(str(ticket_id), text)

    def list_notes(self, ticket_ref: str) -> list[TicketNote]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM ticket_notes WHERE ticket_ref = ? ORDER BY id ASC",
                (ticket_ref,),
            ).fetchall()
        return [_note_from_row(row) for row in rows]

    def create_draft_update(self, ticket_id: int, note: str | None = None) -> AdoTicketDraft:
        if note and note.strip():
            self.add_note(ticket_id, note)
        detail = self.get_ticket_detail(ticket_id)
        body = _draft_body(detail.ticket, detail.notes)
        now = _now()
        with connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO ticket_update_drafts (ticket_ref, body, posted, created_at) VALUES (?, ?, 0, ?)",
                (str(ticket_id), body, now),
            )
            row = conn.execute("SELECT * FROM ticket_update_drafts WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _draft_from_row(row)

    def latest_draft(self, ticket_ref: str) -> AdoTicketDraft | None:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM ticket_update_drafts WHERE ticket_ref = ? ORDER BY id DESC LIMIT 1",
                (ticket_ref,),
            ).fetchone()
        return _draft_from_row(row) if row else None

    def post_update(self, ticket_id: int, *, from_draft: bool, yes: bool) -> AdoPostUpdateResult:
        if not from_draft:
            raise AdoPermissionError("post-update requires --from-draft.")
        if not yes:
            raise AdoPermissionError("post-update requires explicit --yes confirmation.")
        draft = self.latest_draft(str(ticket_id))
        if draft is None:
            raise AdoPermissionError(f"no local draft exists for ticket {ticket_id}")
        config = self.get_config()
        if not config.configured or not config.token_available:
            raise AdoConfigurationError(config.setup_guidance or "Azure DevOps is not configured.")
        self._client(config).post_comment(ticket_id, draft.body)
        posted_at = _now()
        with connect(self.db_path) as conn:
            conn.execute(
                "UPDATE ticket_update_drafts SET posted = 1, posted_at = ? WHERE id = ?",
                (posted_at, draft.id),
            )
        return AdoPostUpdateResult(
            ticket_ref=str(ticket_id),
            draft_id=draft.id,
            posted=True,
            message="posted approved draft update to Azure DevOps",
        )

    def _client(self, config: AdoConfig) -> AzureDevOpsClient:
        return self.client or AzureDevOpsClient(config)


def _read_config(db_path: Path | None) -> dict[str, str]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT key, value FROM ado_config").fetchall()
    return {row["key"]: row["value"] for row in rows}


def _ticket_from_work_item(item: dict[str, Any]) -> AdoTicket:
    fields = item.get("fields", {})
    assigned_to = fields.get("System.AssignedTo")
    if isinstance(assigned_to, dict):
        assigned_to = assigned_to.get("displayName")
    return AdoTicket(
        id=int(item.get("id")),
        title=fields.get("System.Title", ""),
        state=fields.get("System.State"),
        assigned_to=assigned_to,
        work_item_type=fields.get("System.WorkItemType"),
        url=item.get("url"),
        description=fields.get("System.Description"),
    )


def _draft_body(ticket: AdoTicket, notes: list[TicketNote]) -> str:
    note_lines = [note.text for note in notes] or ["No local notes captured yet."]
    return "\n".join(
        [
            f"Update for #{ticket.id}: {ticket.title}",
            "",
            "Progress:",
            *[f"- {line}" for line in note_lines],
            "",
            "Next steps:",
            "- Continue from the current local notes.",
        ]
    )


def _note_from_row(row) -> TicketNote:
    return TicketNote(id=row["id"], ticket_ref=row["ticket_ref"], text=row["text"], created_at=row["created_at"])


def _draft_from_row(row) -> AdoTicketDraft:
    return AdoTicketDraft(
        id=row["id"],
        ticket_ref=row["ticket_ref"],
        body=row["body"],
        posted=bool(row["posted"]),
        created_at=row["created_at"],
        posted_at=row["posted_at"],
    )


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()

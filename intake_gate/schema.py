"""The nine-stage intake schema.

Every field a deal must answer before operations will accept it. Stage order,
field names, and option lists mirror the interactive gate on the portfolio
page. Nothing here knows about clients, platforms, or vendors; the managed
lists are placeholders a real deployment would fill from its own systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

FieldKind = Literal["text", "date", "number", "select", "choice"]


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: FieldKind
    required: bool = False
    options: tuple[str, ...] = ()

    def accepts(self, value: object) -> bool:
        """Return True when value is a usable answer for this field."""
        if value is None:
            return False
        if self.kind == "choice":
            return value in self.options
        if self.kind == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0
        if self.kind in ("text", "date", "select"):
            return isinstance(value, str) and value.strip() != ""
        return False


@dataclass(frozen=True)
class Stage:
    number: str
    key: str
    name: str
    purpose: str
    fields: tuple[Field, ...] = field(default_factory=tuple)

    def field_map(self) -> dict[str, Field]:
        return {f.key: f for f in self.fields}


def _choice(key: str, label: str, *options: str, required: bool = False) -> Field:
    return Field(key, label, "choice", required, tuple(options))


STAGES: tuple[Stage, ...] = (
    Stage(
        "01", "opportunity", "Opportunity",
        "The basics. The fields most often left blank.",
        (
            Field("opportunity_name", "Opportunity name", "text", required=True),
            _choice("vertical", "Vertical", "QSR", "F&B", "Retail", "Ad / Media", "Other", required=True),
            _choice("engagement_type", "Engagement type", "New business", "Retained client", required=True),
            _choice("response_type", "Response type", "RFP", "Quote", "POC / pilot", required=True),
            Field("due_date", "Due date", "date"),
            Field("sales_owner", "Sales owner", "text", required=True),
        ),
    ),
    Stage(
        "02", "solution", "Solution & Hardware",
        "The tech. It flags a kickoff the moment the solution is new.",
        (
            Field("platform", "Platform", "select"),
            Field("player", "Go-forward player", "select"),
            _choice("storage", "Storage", "None", "32GB", "64GB", "TBD"),
            _choice("multi_output", "Multi-output", "Single", "Dual", "More than 2"),
            Field("endpoint_count", "Endpoint count", "number"),
            _choice("new_vendor", "New vendor or solution?", "Yes", "No"),
            _choice("new_hardware", "Hardware not used before?", "Yes", "No"),
        ),
    ),
    Stage(
        "03", "install", "Install & Field",
        "Who installs, and what has to be staged before they arrive.",
        (
            _choice("install_responsibility", "Install responsibility", "Field tech", "Client self-install", "Third-party"),
            _choice("imaging", "Imaging needed?", "Yes", "No"),
            _choice("staging", "Staging & kitting?", "Yes", "No"),
        ),
    ),
    Stage(
        "04", "content_ops", "Content Ops Scope",
        "What operations owns. Origination drives the whole effort model.",
        (
            _choice("origination", "Content origination", "Client supplies", "Agency supplies", "Originated from concept", required=True),
            _choice("ops_deliverable", "Deliverables", "Menu boards", "Daypart", "LTO / promo", "Pricing", "POS-driven", "Ad trafficking"),
            _choice("localization", "Localization", "Single", "Bilingual", "Three or more"),
            _choice("deployment_scope", "Deployment scope", "Single site", "Multi-site", "Network-wide"),
            _choice("cms_training", "Client CMS training?", "Yes", "No"),
        ),
    ),
    Stage(
        "05", "creative", "Creative Scope",
        "Creative is a separate lane. Split out so scope does not blur with operations.",
        (
            _choice("creative_engaged", "Creative engaged?", "Yes", "No"),
            _choice("creative_deliverable", "Deliverables", "Design from concept", "Template", "Brand adaptation", "Motion", "Resizing"),
        ),
    ),
    Stage(
        "06", "migration", "Migration",
        "Any conversion flags a kickoff and starts a conversion clock.",
        (
            _choice("migration_type", "Migration type", "None", "Platform to platform", "Other"),
            Field("conversion_deadline", "Conversion deadline", "date"),
        ),
    ),
    Stage(
        "07", "sla", "SLA",
        "Custom commitments need a capacity review before anyone signs.",
        (
            _choice("sla", "SLA", "Standard tiers", "Custom"),
            _choice("after_hours", "After-hours coverage?", "Yes", "No"),
        ),
    ),
    Stage(
        "08", "readiness", "Readiness Gate",
        "Operations does not proceed until these exist. Missing items block the work.",
        (
            _choice("opportunity_logged", "Opportunity logged", "Yes", "No"),
            _choice("sow_exists", "SOW or quote exists", "Yes", "No"),
            _choice("owner_assigned", "Internal owner assigned", "Yes", "No"),
            _choice("kickoff_scheduled", "Kickoff scheduled", "Yes", "No"),
        ),
    ),
    Stage(
        "09", "notes", "Notes",
        "Complexity flags and open questions, so nothing lives only in one person's head.",
        (
            Field("notes", "Notes and open items", "text"),
        ),
    ),
)

STAGE_BY_KEY: dict[str, Stage] = {s.key: s for s in STAGES}
ALL_FIELDS: dict[str, Field] = {f.key: f for s in STAGES for f in s.fields}

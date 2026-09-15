"""Table-driven tests for the gate.

Expectations live here, not in the package, so a rule change has to be made
on purpose in both places.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from intake_gate import STAGES, build_name, estimate, evaluate, evaluate_flags, is_valid_name, render
from intake_gate.cli import main
from intake_gate.rules import RULES

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text())


# ---------- schema ----------

def test_nine_stages_in_order():
    assert [s.number for s in STAGES] == [f"{i:02d}" for i in range(1, 10)]


def test_field_keys_are_unique():
    keys = [f.key for s in STAGES for f in s.fields]
    assert len(keys) == len(set(keys))


def test_required_fields_are_exactly_the_stage_one_basics_and_origination():
    required = {f.key for s in STAGES for f in s.fields if f.required}
    assert required == {
        "opportunity_name", "vertical", "engagement_type",
        "response_type", "sales_owner", "origination",
    }


# ---------- clean path ----------

def test_clean_deal_is_cleared():
    d = evaluate(load("clean_deal.json"))
    assert d.cleared
    assert d.verdict == "Cleared to kickoff"
    assert d.stages_ready == 9
    assert d.flags == ()
    assert d.readiness_blockers == ()


def test_clean_deal_exit_code_zero(capsys):
    assert main([str(EXAMPLES / "clean_deal.json")]) == 0
    assert "Cleared to kickoff" in capsys.readouterr().out


# ---------- blocking ----------

@pytest.mark.parametrize("key", ["opportunity_logged", "sow_exists", "owner_assigned", "kickoff_scheduled"])
def test_any_missing_readiness_item_blocks(key):
    intake = load("clean_deal.json")
    intake[key] = "No"
    d = evaluate(intake)
    assert not d.cleared
    assert d.readiness_blockers == (key,)


@pytest.mark.parametrize("key", ["opportunity_name", "vertical", "engagement_type", "response_type", "sales_owner", "origination"])
def test_missing_required_field_blocks(key):
    intake = load("clean_deal.json")
    del intake[key]
    d = evaluate(intake)
    assert not d.cleared
    assert key in d.missing_required


def test_custom_sla_blocks_signoff_even_when_readiness_is_complete():
    intake = load("clean_deal.json")
    intake["sla"] = "Custom"
    d = evaluate(intake)
    assert not d.cleared
    assert [f.code for f in d.signoff_blockers] == ["CAPACITY-REVIEW"]


def test_more_than_two_outputs_blocks_signoff():
    intake = load("clean_deal.json")
    intake["multi_output"] = "More than 2"
    d = evaluate(intake)
    assert not d.cleared
    assert [f.code for f in d.signoff_blockers] == ["ENG-REVIEW"]


def test_custom_sla_example_exit_code_one():
    assert main([str(EXAMPLES / "custom_sla.json")]) == 1


# ---------- flags, one rule each ----------

FLAG_CASES = [
    ({"multi_output": "More than 2"}, "ENG-REVIEW"),
    ({"new_vendor": "Yes"}, "KICKOFF-NEW-SOLUTION"),
    ({"new_hardware": "Yes"}, "KICKOFF-NEW-SOLUTION"),
    ({"origination": "Originated from concept"}, "CREATIVE-LANE"),
    ({"creative_engaged": "Yes"}, "CREATIVE-LANE"),
    ({"migration_type": "Platform to platform"}, "MIGRATION-CLOCK"),
    ({"migration_type": "Other"}, "MIGRATION-CLOCK"),
    ({"sla": "Custom"}, "CAPACITY-REVIEW"),
    ({"after_hours": "Yes"}, "AFTER-HOURS"),
    ({"imaging": "Yes"}, "FIELD-STAGING"),
    ({"staging": "Yes"}, "FIELD-STAGING"),
    ({"localization": "Bilingual"}, "LOCALIZATION"),
    ({"localization": "Three or more"}, "LOCALIZATION"),
]


@pytest.mark.parametrize("intake,code", FLAG_CASES)
def test_each_flag_fires_alone(intake, code):
    assert [f.code for f in evaluate_flags(intake)] == [code]


def test_no_flags_on_empty_intake():
    assert evaluate_flags({}) == []


def test_every_rule_is_covered_by_a_case():
    covered = {code for _, code in FLAG_CASES}
    assert covered == {r.flag.code for r in RULES}


def test_only_engineering_and_capacity_block_signoff():
    blocking = {r.flag.code for r in RULES if r.flag.blocks_signoff}
    assert blocking == {"ENG-REVIEW", "CAPACITY-REVIEW"}


def test_migration_starts_a_clock():
    clocks = {r.flag.code for r in RULES if r.flag.starts_clock}
    assert clocks == {"MIGRATION-CLOCK"}


# ---------- validation ----------

def test_unknown_field_is_reported_and_blocks():
    intake = load("clean_deal.json")
    intake["price"] = 100000
    d = evaluate(intake)
    assert d.unknown_fields == ("price",)
    assert not d.cleared


def test_invalid_choice_is_reported_and_blocks():
    intake = load("clean_deal.json")
    intake["vertical"] = "Aerospace"
    d = evaluate(intake)
    assert "vertical" in d.invalid_fields
    assert "vertical" in d.missing_required
    assert not d.cleared


@pytest.mark.parametrize("bad", [-1, "12", True, None])
def test_bad_endpoint_count_does_not_count_as_answered(bad):
    intake = load("clean_deal.json")
    intake["endpoint_count"] = bad
    d = evaluate(intake)
    solution = next(s for s in d.stages if s.key == "solution")
    assert not solution.complete


# ---------- effort ----------

@pytest.mark.parametrize("count,points", [(0, 1), (10, 1), (11, 3), (100, 3), (101, 6), (1000, 6), (1001, 10), (10000, 10), (10001, 15)])
def test_endpoint_bands_at_boundaries(count, points):
    e = estimate({"endpoint_count": count})
    assert e.points == points


def test_localization_multiplies_the_base():
    base = estimate({"endpoint_count": 240, "deployment_scope": "Multi-site"}).points
    bilingual = estimate({"endpoint_count": 240, "deployment_scope": "Multi-site", "localization": "Bilingual"}).points
    assert bilingual == round(base * 1.5)


def test_bands_are_monotonic():
    light = estimate({"endpoint_count": 5}).band
    program = estimate(load("custom_sla.json")).band
    assert light == "Light"
    assert program == "Program"


def test_brief_never_mentions_dollars():
    intake = load("custom_sla.json")
    text = render(intake, evaluate(intake))
    assert "$" not in text
    assert "Effort only" in text


# ---------- naming ----------

def test_naming_builder_matches_portfolio_example():
    assert build_name("ATL01", 2, "promo", date(2026, 7, 29)) == "ATL01-S02-PROMO-20260729"


def test_naming_strips_punctuation_and_pads_screen():
    assert build_name("atl-01", 7, "MENU", date(2026, 1, 1)) == "ATL01-S07-MENU-20260101"


@pytest.mark.parametrize("kwargs", [
    dict(location="", screen=1, content_type="promo"),
    dict(location="ATL", screen=0, content_type="promo"),
    dict(location="ATL", screen=1, content_type="banner"),
])
def test_naming_rejects_bad_input(kwargs):
    with pytest.raises(ValueError):
        build_name(live_date=date(2026, 1, 1), **kwargs)


def test_is_valid_name():
    assert is_valid_name("ATL01-S02-PROMO-20260729")
    assert not is_valid_name("atl01-s02-promo-2026")


# ---------- json output ----------

def test_json_output_round_trips(capsys):
    assert main([str(EXAMPLES / "custom_sla.json"), "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["cleared"] is False
    assert "CAPACITY-REVIEW" in data["signoff_blockers"]
    assert data["effort"]["band"] == "Program"

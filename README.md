# Intake and Readiness Gate

A nine-stage intake gate for operations work. A deal does not reach the delivery team until every stage clears, and the form flags the risks on its own so the person filling it in does not have to know the rules.

Built by Kristen Estes, a Director of Content Operations with 20 years in creative and content ops and a PMP, as a public proof-of-work for senior AI Product and AI Operations roles. [LinkedIn](https://www.linkedin.com/in/kris10estes)

**For AI enablement teams:** the gate flags risk on its own, so a new teammate follows the rules on day one without memorizing them first.

This is the logic behind the interactive gate on my systems portfolio, pulled out into code so it can be read, tested, and reused. Client, platform, and vendor detail is withheld; the managed lists are placeholders.

## What it does

Give it an intake as JSON. It returns one decision:

**Stage status:** which of the nine stages are complete and which required fields are missing.

**Smart flags:** eight rules fire on their own from the answers. Two of them block sign-off (an engineering review for more than two outputs, a capacity review for a custom SLA). The rest route work: a kickoff for any new vendor or hardware, a creative lane whenever content is originated from concept, a conversion clock for any migration, staging before a field install, and a localization multiplier.

**Readiness gate:** four items operations will not proceed without. Opportunity logged, SOW or quote exists, internal owner assigned, kickoff scheduled.

**Effort estimate:** a band and a point score from endpoint count, deployment scope, origination, deliverable type, migration, and localization. Effort only, never dollars. Cost sits with operations, price sits with sales, and the two never share a field.

**Requirements brief:** the whole decision as Markdown, ready to paste into a tracker or wiki at kickoff.

The naming-convention builder from the same portfolio page is included as a utility: one clean filename every time, `LOCATION-Sxx-TYPE-YYYYMMDD`.

## Try it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m intake_gate examples/clean_deal.json          # cleared, exit 0
python -m intake_gate examples/custom_sla.json          # blocked, exit 1
python -m intake_gate examples/custom_sla.json --format json
python -m intake_gate --name atl-01 --screen 2 --type promo --date 2026-07-29

python -m pytest                                        # 60 tests
```

The exit code is the gate. Zero means cleared to kickoff. One means something is open, and the brief says what.

## How the rules are written

Each rule is one line of intent next to one line of condition, in `intake_gate/rules.py`:

```python
Rule(
    Flag("CAPACITY-REVIEW", "Capacity review",
         "A custom SLA blocks sign-off until capacity is reviewed.",
         blocks_signoff=True),
    lambda i: _is(i, "sla", "Custom"),
),
```

Rules only add work. Nothing in the gate removes a review someone else added. The tests confirm every rule fires alone, that only the two intended rules block sign-off, and that a rule cannot be added without a test case covering it.

## Layout

```
intake_gate/
  schema.py    the nine stages and their fields
  rules.py     smart flags and the readiness gate
  effort.py    level-of-effort bands
  gate.py      one decision from one intake
  brief.py     the Markdown requirements brief
  naming.py    the filename builder
  cli.py       command line entry point
examples/      a clean deal and a blocked one
tests/         60 table-driven cases
```

## What it is not

The effort weights are illustrative so the model is legible and testable. A real deployment calibrates them against its own delivery history. The managed lists (platform, player) are free text here because the real ones are internal.

## Built with

Claude Code and Claude in Cowork. The stages, rules, and thresholds are my decisions, lifted from a gate I designed and ran in production, and every line got read before it landed here. Directing the tool is the job.

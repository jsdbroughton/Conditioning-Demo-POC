# Conditioning Demo POC — before/after, and what it might mean for the product

Written for an internal Speckle audience who hasn't worked on this code — no
engineering background assumed. Real numbers throughout are measured against
live client models (see `docs/NOTES.md`'s 2026-08-14 and 2026-09-07 entries — the
2026-09-07 entries span two builds, the pre-parquet-port function and the
version described here; a mid-2026-09-07 port and a property-path bug in the
early build of it are why a couple of numbers below carry a caveat),
not estimated. The client itself is referred to here as "ACME Studios," per
this repo's own anonymization rule (see `README.md`) — internally the real
name is known, but this file lives in a repo that's meant to stay shareable,
so it keeps the same discipline everything else in it does.

## What this is

A Speckle Automate function built for one construction client. Their
architects model walls in Revit using their own naming habits; the
contractor needs every wall tagged with *their own* cost-classification
codes (a Uniformat-derived system, borrowed from their own estimating
spreadsheet) to run takeoffs and cost estimates. Today that tagging is done
by hand, wall by wall, across models with tens of thousands of elements.
This function reads a triggered model version, works out a classification
for every wall that doesn't already have one, and writes the result back —
never touching the original model.

## The problem, as it actually looks in a model (before)

Three things are true of a typical model before this function ever touches
it:

**Classification is a mix of three states, indistinguishable at a glance.**
Some walls already carry the contractor's own valid code. Some carry an
older, incompatible coding convention. Most carry nothing at all. Nothing in
the model tells you which is which without opening walls one at a time.

**The data needed to sub-type a wall exists, but it's scattered and
inconsistent.** A wall's Fire Rating and Type Mark sit under Revit's "Type
Parameters," its height under a completely different "Instance Parameters"
group — and coverage varies enormously by who modeled what. Checked
directly against three real source files on one project: Fire Rating was
populated on 92.8% of one file's walls, 48.1% of another's, and 22.9% of the
third's — same project, three very different completion states, and no
signal anywhere flagging that gap. Height is worse in a different way: it's
genuinely per-wall, not per-type — one official wall tag spanned 38 distinct
heights from 1 to 23 feet on a single model, purely from floor-to-floor
variation, so it can't even be treated as a fact about "that kind of wall."

**Nothing about a wall's name tells you whether to trust it.** A wall
carrying a fully descriptive type name and a wall whose Revit type is
literally named `Empty` look, in the raw model, equally authoritative.

## What the function adds (after)

The function reads the triggered version, classifies every wall, and
publishes the result as **two new sibling model versions** — a walls-only
one and a full republish of the whole building (see "How to see this
yourself" below) — the source model is never modified. In the full
republish, every element that isn't a wall also gets a code where the
evidence supports one — doors, floors, stairs, fixtures, ducts — using the
same "several independent clues must agree" approach as walls, and every
one of those is stamped as a proposal for the estimator to correct, because
the rule table behind them hasn't been reviewed by the client yet. Every
wall carries one added property containing, depending on the wall:

- Its classification code, and whether that code was **already there** or
  **worked out** — and if worked out, a one-to-three confidence tier plus a
  plain-English sentence naming exactly what evidence it came from (never
  "predicted by a model" — this is rule matching, not a trained system, and
  says so).
- For each attribute the wall actually has — fire rating, wall tag, height,
  acoustic rating, stud size — the value, and for fire rating and wall tag
  specifically, whether it came from a real Revit parameter or was read off
  the type name (the two don't always agree, so the source is recorded, not
  assumed).
- Where the client's own classification has nothing finer than "interior
  partition" for a wall, a similarity-based grouping into the finer
  sub-types their own estimators actually think in — at three
  granularities (a coarse resemblance read, a cost-relevant read split on
  fire/acoustic rating, and a fully-split read that also separates on
  height band), each with a plain-English description of what that group's
  members share, and an honest "varies between X, Y, Z" wherever they
  don't all agree, rather than a silent guess.

Alongside that: color-coded flags directly in the 3D viewer (so a reviewer
never has to open a properties panel to see which walls need a second look),
and a short markdown report attached to the run — cut, once someone actually
tried to read it, from 10.2 MB / 62,000 rows to 21.6 KB / 200 rows.

## Two worked examples worth walking through live

**The six-tag wall type.** In one production run, a single group of 100
wall elements — functionally identical partitions by every measure the
similarity engine uses — turned out to carry six different official wall
tags across the architects' own drawings (`K1`, `K2`, `K3`, `L2`, `L3`,
`L6`). Before this function, seeing that would mean opening up to 100
individual wall property panels and comparing them by hand. After, it's one
line: *"100 elements — Type Mark varies (K1, K2, K3, L2, L3, L6), Fire
Rating NFR, …"* — the fact surfaces itself instead of requiring someone to
go looking for it.

**The honesty test.** In another real run, 91% of a 5,955-element model
landed in the *highest*-confidence tier — including one wall whose entire
Revit type name was `Empty`. That's not a bug: Revit's own category
assignment for that element really is a strong, reliable signal, tier and
all. But it's exactly why the function also stamps a completely separate
flag — "did the building tell us this, or did we work it out" — on every
wall regardless of tier. High confidence and "already checked by a human"
are two different claims, and this is the clearest real example of why they
can't be collapsed into one number. Worth showing side by side: the tier,
and the fact that this wall's own name gave the tool nothing to go on at
all.

**The wrong-code regression, caught live on a demo call.** A fresh internal
port of this function to Speckle's newer data format shipped with a subtle
bug: every Revit parameter read used a slightly wrong lookup path, one
level short of what the real export actually uses. The result looked
plausible rather than obviously broken — nearly every wall in a fitout
model landed on an *exterior*-wall code, when a fitout is almost entirely
interior partitions. It read as a believable classification right up until
someone who knew the building looked at the numbers and said that's not
right. Confirmed and fixed the same day by pulling the exact property
paths off the live model rather than guessing, and re-run to confirm
interior walls now land on the interior code family as expected. The
lesson worth keeping in front of anyone extending this: a classification
tool that fails by producing a wrong-but-plausible answer, instead of an
obviously missing one, needs a person who knows the domain checking its
output after every change that looks routine — its own quiet confidence is
not evidence it's right.

**The costing test.** An early version of wall-type grouping described its
own "varies" honestly — a hundred-element group might report "Fire Ratings:
NFR, SMOKE" rather than picking one and hiding the rest. Truthful, but not
what the estimators asked for on the call: two walls with different fire
ratings cost differently, so a group spanning both fire ratings still can't
be priced as one line. Fixed by splitting fire rating and acoustic (STC)
rating out *before* similarity clustering runs, so those two attributes
can no longer vary inside that group — by construction, not by coincidence.

**The "is height really just a bigger number" test.** Height looked at
first like a pure quantity question — a taller wall has more square
footage, and the takeoff already prices that without touching
classification. Pushed on directly: no, height can be a genuine cost
*category*, not just a bigger quantity — taller interior stud walls
commonly need a heavier stud gauge or added bracing past a real
threshold, the same shape of problem fire rating and acoustic rating
already were. No client call was available to confirm exactly where that
threshold sits for this contractor, so it was picked deliberately rather
than left out: short under 4', standard up to roughly 20', tall above
that, flagged everywhere as an assumption to correct once the real
numbers are known, not a measured fact.

Once fire rating, acoustics *and* height all mattered, a single flat split
would have made every group finer whether or not a given family actually
needed it. So grouping became three views instead of one: a coarse read
(does this look like the same wall at all), a cost read (does it also
agree on fire rating and acoustics), and a full read (does it also agree
on height). A family that's already uniform on the finer questions shows
up once, at the coarse level — nothing manufactures a difference that
isn't there, and a reader can pick whichever question they're actually
asking.

## How to see this yourself, in the Speckle app

1. Open the client's project and pick any one of the three source models.
2. Open a few walls' Properties panels in the viewer. Look for Assembly
   Code (may be missing, may be an old format), Fire Rating and Type Mark
   under Parameters → Type Parameters → Identity Data, and Unconnected
   Height under Parameters → Instance Parameters → Constraints — several
   clicks deep, one wall at a time, nothing summarized.
3. Open the automation run's "View Results" link, or navigate directly to
   the sibling `Conditioned/All/<model name>` version (the full building, conditioned
   walls patched in) or `Conditioned/Walls/<model name>` (conditioned walls only) — the
   source model stays loaded alongside either, so the viewer's color-coded
   flags still resolve.
4. Open the same wall's Properties panel in the new version. Everything
   from the section above now sits under one property — one place to look,
   rather than several parameter groups.
5. Open the run's attached markdown report for the aggregate picture:
   coverage percentages, a tier breakdown, and the wall-type groups — the
   one-page version of what would otherwise take opening every wall to see.

## Why this might matter beyond this one client

Strip away the specific client's code list and Uniformat vocabulary, and
what's left is a reusable pattern, not a wall-specific tool:

- Match every element against whatever *is* already correctly classified in
  the same model; fall back to rules over the element's own category and
  parameters when nothing matches; tag every result with a confidence tier
  and a plain statement of exactly what it was derived from.
- Prefer the element's own real parameters over guessing from its name, and
  record which one actually supplied each value.
- Where no formal classification exists at all, describe what similar
  elements have in common instead of inventing a category — and say plainly
  when they don't agree, rather than picking one value and hiding the rest.
- Never touch the source data. Publish a new version, a viewer overlay, and
  a report a person can read end to end before trusting any of it.
- No training, no external AI service, nothing leaves the customer's
  Speckle workspace — this is rule-matching against the model's own data,
  which matters a lot if a feature like this is going to touch every
  customer's BIM data.

None of that mechanism is specific to walls, to Uniformat, or to this one
client's spreadsheet. The same approach — match against a reference
taxonomy, tier the confidence, cluster and describe the leftovers, report
before trusting — would apply just as well to a different classification
system (MasterFormat, OmniClass, a firm's own equipment-tagging convention)
against a different element category (doors, MEP equipment, structural
framing). This client's Uniformat code set is the first taxonomy plugged
into that engine, not the limit of what it can do.

**What's genuinely still proof-of-concept**, i.e. what a real product
feature would need on top of this:

- One hardcoded reference dataset per deployment, wired in by hand — not
  something a customer uploads or configures themselves.
- Every result auto-applies today regardless of tier. There's no review
  queue where a person accepts or rejects a Tier 2/3 result before it
  becomes final — tiers are a label on the output, not a gate.
- Nothing a reviewer corrects today feeds back into the next run — no
  memory across runs, no improvement loop.
- Shipped as a Python Automate function, deployed one model at a time via a
  manual CLI tool — not a configurable, self-serve pipeline stage inside
  the app.

## Further reading

- `README.md` — "What it does" and "Output" sections have the full,
  current property schema this document is summarizing.
- `docs/NOTES.md` — the dated development log; search for `2026-08-14` and
  `2026-09-07` for the entries this document draws its numbers from.

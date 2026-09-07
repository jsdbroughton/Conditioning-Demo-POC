# Saved-views prompt for Speckle AI chat

Paste the block below into Speckle AI chat on a `Conditioned/All/<model>`
version. It walks the story in `docs/BEFORE-AFTER-DEMO.md` as a set of saved
views. The property group name is whatever the automation's *Conditioned Code
Property Name* input was set to — on the current Turner deployment that is
`Turner Conditioned UF Code`; substitute if yours differs.

---

You are working on the model version currently open. Every object carries a
property group called **`Turner Conditioned UF Code`** written by a Speckle
Automate function that assigns Uniformat Level 4 cost codes. Its keys are:

- `Status` — `existing` | `predicted` | `component` | `not conditioned`
- `Level 4 Code` (e.g. `C1010.10`) and `Level 4 Code Description`
- `Tier` — `Tier 0` (already correct) … `Tier 3` (needs a human look)
- `Requires Verification` — true wherever the function derived the code
- `Method` — `similarity` | `heuristic_category` | `heuristic_function` |
  `heuristic_host_function` | `heuristic_name` | `legacy_code`
- `Original Code` — the legacy code that was replaced, if any
- Walls only: `Observed Fire Rating`, `Observed Acoustic STC`,
  `Observed Height Band`, `Observed Wall Tag`, `Observed Stud Size`
- Walls only, three nested granularities of an inferred wall-type grouping:
  `Inferred Type Group (Coarse)` → `Inferred Type Group (Fire/Acoustic)` →
  `Inferred Type Group (Fine Grained)`, each with a matching
  `Inferred Group Label (…)` and, on the fine-grained one, an
  `Inferred Group Description`
- Components only: `Parent Level 4 Code`

Please do two things.

**1. Rebuild the classification hierarchy in the Models panel.**
Group the scene tree so a reviewer can browse it the way the estimator
thinks: first by `Level 4 Code` (show the `Level 4 Code Description`
alongside the code). For WALL codes only — A2010.x, B2010.x, B2020.30,
C1010.x — continue within each code by `Inferred Type Group (Coarse)`, then
`Inferred Type Group (Fire/Acoustic)`, then
`Inferred Type Group (Fine Grained)`; the grouping keys exist only on walls,
so for every other code stop at the Level 4 Code rather than showing empty
`(none)` levels. Objects with `Status` =
`component` or `not conditioned` go in their own branches at the top level,
labelled as such, so they are visible but never mixed into a coded branch.
Where a finer tier's key equals its parent's key, do not create an empty
sub-branch — that means the finer split found nothing to separate.

**2. Create these saved views, in this order, each colourised by the named
property and with a one-line description a non-engineer can read.** Hide
`Status = component` and `Status = not conditioned` in every view unless the
view says otherwise.

1. **Before — as modelled.** No conditioning colours; colour by Revit
   `category`. Description: what the estimator receives today.
2. **Level 4 codes.** Colour by `Level 4 Code`. Legend ordered by code.
   Description: every element the function could honestly place, in the
   client's own cost vocabulary.
3. **Authored vs. derived.** Colour by `Requires Verification` (false =
   authored by the model, true = worked out by the function). Description:
   the "did the building tell us, or did we work it out" question.
4. **Confidence tiers.** Colour by `Tier`, ordered Tier 0 → Tier 3, with
   Tier 3 in a warning colour. Description: where a reviewer should look
   first.
5. **Needs a closer look.** Isolate `Tier = Tier 3` only, colour by
   `Level 4 Code`. Description: the review queue.
6. **Legacy codes remapped.** Isolate objects where `Original Code` is
   present, colour by `Level 4 Code`. Description: elements that carried an
   old-format code and were translated, original preserved.
7. **How each code was reached.** Colour by `Method`. Description: matched
   to an already-coded neighbour, read from Revit's category, from
   `Function`, from the host wall's `Function`, or from a name keyword.
8. **Interior partitions — coarse families.** Isolate `Level 4 Code =
   C1010.10`, colour by `Inferred Type Group (Coarse)`. Description: which
   architect wall types basically resemble each other.
9. **Interior partitions — fire and acoustic split.** Same isolation,
   colour by `Inferred Type Group (Fire/Acoustic)`. Description: the same
   families, now separated wherever fire rating or STC differs, because
   those cost differently.
10. **Interior partitions — fully split.** Same isolation, colour by
    `Inferred Type Group (Fine Grained)`. Description: further separated by
    height band (short / standard / tall) — an opinionated threshold awaiting
    the estimator's confirmation.
11. **Fire rating as observed.** Walls only, colour by
    `Observed Fire Rating`; leave walls with no value grey and keep them
    visible. Description: coverage is uneven between source files — grey is
    the gap, not a rating.
12. **Height bands.** Walls only, colour by `Observed Height Band`.
    Description: where the tall/short thresholds fall on this building.
13. **What was not classified.** Show only `Status = not conditioned`,
    colour by Revit `category`. Description: honest blanks — rooms and other
    non-physical elements, and physical elements with no usable evidence.
14. **Components.** Show only `Status = component`, colour by
    `Parent Level 4 Code`. Description: parts priced with their parent
    (railing supports, nested door families) — deliberately not counted.

After creating them, list each view's name with the object count it shows,
and tell me which views came out empty on this model so I can drop them.

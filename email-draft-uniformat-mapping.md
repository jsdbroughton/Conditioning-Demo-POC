# Draft reply — thread: "Additional Uniformat Code Mapping"

**Reply all** to Kevin's 16:33 message (To: Kevin, Jessica)
**Subject:** RE: Additional Uniformat Code Mapping

---

Kevin, Jessica,

Kevin — before you build that mapping from scratch, we may already have most
of it. The conditioning runs have been doing exactly this mapping against
your own models, so rather than starting from a blank page, here is what
they have inferred so far:

| Model tag | Turner code | Elements | Note |
|-----------|-------------|----------|------|
| `C1010145` | `C1010.10` | 100 | Interior fixed partitions |
| `B2010160` | `B2010.10` | 73 | Exterior wall veneer |
| `B2020200` | `B2020.30` | 24 | Curtain systems — read as exterior window wall |
| `B2010` | `B2010.10` | 2 | Bare section code, no sub-code present |
| `B2010160` | `B2010.40` | 1 | **Needs your call** — see below |

Four of those five are straightforward. The last one is the interesting one:
the same model tag `B2010160` resolved two different ways, because one of
those elements is a curtain system rather than a wall. That is a genuine
question about your taxonomy rather than a bug, and it is exactly the sort
of thing worth pinning down in the document you are writing.

Please treat this as a starting point to correct rather than an answer. It
is derived from what is in the models, not from anything Turner has told us,
and it only covers the codes those models actually contain.

## What has changed since this morning

The conditioned models have been refreshed. Alongside the Level 4 code, each
wall element now also carries:

- **Observed Type Attributes** — fire rating, acoustic rating and stud size,
  e.g. `SMOKE · STC-35 · 6" Stud`. Also available separately as **Observed
  Fire Rating**, **Observed Acoustic STC** and **Observed Stud Size**.
- **Observed Type Group** — a grouping of element types that closely
  resemble one another, for the models where the naming is less structured.

Jessica — these sit inside the same `Conditioned UF Code` property set as
the code itself, so they should come through into Power BI alongside
everything you already have, without changing how you pull the data.

That gives you the breakdown Kevin was after on the call. On the interiors
model, for example, the interior partitions now split as:

- NFR — 19,844 elements
- SMOKE — 6,320
- 1HR — 769

and further by acoustic rating and stud size within those.

## Two things to be aware of

**"Observed" means we derived it, not that Turner agreed it.** Everything
above is read out of the architect's own element type names. It is not a
Turner classification and should not be treated as one. Where the group
labels carry a letter (A, B, C), that letter is ours — assigned by size, and
it will change if the model changes.

**The attributes depend entirely on how the architect named things.** On the
interiors model, 97% of elements are named in a way that gives up rating,
STC and stud size cleanly. On the curtain wall model it is 0% — those types
are named `CW_Unitized_Spandrel`, `20d panel` and similar, which assert none
of it. Where there is nothing to read, the properties are simply absent
rather than guessed. The report attached to each run leads with that
coverage figure so you can see which situation you are looking at before
building anything on top of it.

The grouping also cannot reliably separate a smoke partition from a
non-rated one on name similarity alone — we tested that specifically, and it
is why the attributes above are extracted separately rather than inferred
from the groups.

That is still the gap the key code table closes, so Kevin, your document
remains the thing that turns this from "what the model appears to say" into
"what Turner says it is."

Happy to walk through any of it on Thursday.

Best,
Jonathon

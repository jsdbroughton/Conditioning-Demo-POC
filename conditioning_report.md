# Conditioning Demo POC — Uniformat Prediction Report

## Summary

| Metric | Count |
|--------|-------|
| Total walls analysed | 580 |

**Validation**

| Metric | Count |
|--------|-------|
| Has Turner Level 4 code (e.g. B2010.10) | 0 |
| Has code but NOT Turner Level 4 format (needs review) | 175 |
| No code at all (uncoded) | 405 |

**Conditioning**

| Metric | Count |
|--------|-------|
| Predicted via similarity match | 0 |
| Predicted via heuristic / default | 405 |
| Confidence threshold | 0.65 |

---

## Non-Level4 Codes (needs manual crosswalk review — NOT auto-changed)

These walls already have an Assembly Code, but not in Turner's Level 4 dot-notation format (e.g. legacy ASTM Uniformat II codes like `B2010160`). Conditioning does **not** overwrite these — a prior version of this function did, discarding the specific sub-code in favour of a generic default, which is the exact regression caught live on the 2026-07-17 Turner call. They're flagged via `Turner Level 4 Code Review Needed` for a human to map, and their type/family/function are used as similarity references for genuinely uncoded walls below.

| Type Name | Type Mark | Function | Width (mm) | Original Code |
|-----------|-----------|----------|------------|---------------|
| Exterior - 8" Conc. Curb |  | Exterior | 203 | `B2010` ×1 |
| Exterior - 60" Concrete |  | Exterior | 1524 | `B2010` ×1 |
| _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl | CMV-1 | Exterior | 489 | `B2010160` ×5 |
| _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 | CMV-2 | Exterior | 521 | `B2010160` ×1 |
| _HFH -CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl NO BRICK RETURN | CMV | Exterior | 514 | `B2010160` ×2 |
| _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | CMV | Exterior | 514 | `B2010160` ×8 |
| _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell | CMV-CMU | Exterior | 479 | `B2010160` ×2 |
| _HFH -CMV - Brick Masonry Veneer-CMU backup | CMV-SCMU | Exterior | 479 | `B2010160` ×4 |
| _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl WO Sweeps | CMV | Exterior | 514 | `B2010160` ×4 |
| _HFH -CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl NO BRICK RETURN VMU | CMV | Exterior | 498 | `B2010160` ×3 |
| _HFH - BMV - Brick Masonry Veneer. 2nd fl channel VMU | BMV | Exterior | 473 | `B2010160` ×1 |
| _HFH - BMV - Brick Masonry Veneer VMU | BMV | Exterior | 473 | `B2010160` ×1 |
| _HFH - BMV - Brick Masonry Veneer. 1'-7 1/4" - 1 3/8" air no wrap | BMV | Exterior | 489 | `B2010160` ×1 |
| _HFH - BMV - Brick Masonry Veneer. 2nd fl East | BMV | Exterior | 489 | `B2010160` ×1 |
| _HFH - BMV - Brick Masonry Veneer. 1'-7 1/4" - 1 3/8" air | BMV | Exterior | 489 | `B2010160` ×1 |
| _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Top soldier | BMV | Exterior | 514 | `B2010160` ×6 |
| _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Bottom soldier | BMV | Exterior | 514 | `B2010160` ×1 |
| _HFH - BMV - BRIDGE TOP | BMV | Exterior | 514 | `B2010160` ×1 |
| _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG | BMV | Exterior | 514 | `B2010160` ×5 |
| _HFH - BMV - Brick Masonry Veneer. Generic 1 3/8" AG | BMV | Exterior | 489 | `B2010160` ×5 |
| _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | BMV | Exterior | 514 | `B2010160` ×7 |
| _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" CRV TOP | BMV | Exterior | 514 | `B2010160` ×1 |
| _HFH - BMV - Brick Masonry Veneer. 2nd fl | BMV | Exterior | 489 | `B2010160` ×3 |
| _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | BMV | Exterior | 489 | `B2010160` ×10 |
| Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | K3 | Interior | 108 | `C1010145` ×81 |
| Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | L4 | Interior | 117 | `C1010145` ×18 |
| Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud | L6 | Interior | 168 | `C1010145` ×1 |

---

## Predictions (walls with NO existing code)

| # | Type Name | Level | Width (mm) | Predicted Code | Confidence | Method | Matched From |
|---|-----------|-------|------------|----------------|------------|--------|--------------|
| 1 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 2 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 3 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 4 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 5 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 6 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 7 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 8 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 9 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 10 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 11 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 12 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 13 | Exterior - 4" SCMU_6" STUD 2HR | LEVEL 01 | 464 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 14 | Exterior - 4" SCMU_6" STUD 2HR | LEVEL 01 | 464 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 15 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 16 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 17 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 18 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 19 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 20 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 21 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 22 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 23 | HFH - Cast Stone Sill 8" | LEVEL 01 | 394 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 24 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 25 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 26 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 27 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 28 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 29 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 30 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 31 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 32 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 33 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 34 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 35 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 36 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 37 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 38 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 39 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 40 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 41 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 42 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 43 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 44 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 45 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 46 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 47 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 48 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 49 | HFH - Cast Stone Sill 9" | LEVEL 01 | 394 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 50 | HFH - Cast Stone Sill 9" | LEVEL 01 | 394 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 |
| 51 | Exterior - 4" CMU_6" STUD | LEVEL 01 | 432 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 52 | Exterior - 4" CMU_6" STUD | LEVEL 01 | 432 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 53 | _HFH - Roof WALL - NO BACKUP | LEVEL 01 | 111 | `B2010.10` | 75% | heuristic_function | _HFH -CMV - Brick Masonry Veneer-CMU backup |
| 54 | _HFH - Roof WALL - PARAPET | LEVEL 01 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 55 | _HFH - Roof WALL - PARAPET | LEVEL 01 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 56 | _HFH - Roof WALL - PARAPET | LEVEL 01 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 57 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | 75% | heuristic_function | Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud |
| 58 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | 75% | heuristic_function | Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud |
| 59 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | 75% | heuristic_function | Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud |
| 60 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | 75% | heuristic_function | Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud |
| 61 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | 75% | heuristic_function | Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud |
| 62 | *Schematic Design - 9" Interior | LEVEL 01 | 229 | `C1010.10` | 75% | heuristic_function | Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud |
| 63 | Exterior - 4" SCMU_8" CMU 2HR | LEVEL 01 | 444 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell |
| 64 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 65 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 66 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 67 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 68 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 69 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 70 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 71 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 72 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 73 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 74 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 75 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 76 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 77 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 78 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 79 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 80 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 81 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 82 | 084400_Curtain Wall - CW2A ED | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 83 | 084400_Curtain Wall - CW2A ED | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 84 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 85 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 86 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 87 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 88 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 89 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 90 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 91 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 92 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 93 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 94 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 95 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 96 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 97 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 98 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 99 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 100 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 101 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 102 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 103 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 104 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 105 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 106 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 107 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 108 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 109 | 084400_Curtain Wall - CW2A | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 110 | HFH - CW-2A_084400_Curtain Wall - 10 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 111 | HFH - CW-2A_084400_Curtain Wall - 10 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 112 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG |
| 113 | HFH -081100_FR_HM_90min. | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 114 | HFH -081100_FR_HM_90min. | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 115 | HFH -081100_FR_HM_90min. | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 116 | HFH - CW-2A_084400_Curtain Wall - 7 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 117 | HFH - CW-2A_084400_Curtain Wall - 7 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 118 | 084400_Curtain Wall - BRICK- VERTICAL 2' Mockup | LEVEL 01 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG |
| 119 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 120 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 121 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 122 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 123 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 124 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 125 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 126 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 127 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 128 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 129 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 130 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 131 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 132 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 133 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 134 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 135 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 136 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 137 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 138 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 139 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 140 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 141 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 142 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 143 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 144 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 145 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 146 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 147 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 148 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 20 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 149 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 150 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 151 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 152 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 153 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 154 | _HFH - Roof WALL_polyiso | LEVEL 05 ROOF | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 155 | _HFH - Roof WALL_polyiso | LEVEL 05 ROOF | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 156 | _HFH - Roof WALL_polyiso | LEVEL 05 ROOF | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 157 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 158 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 159 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 160 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 161 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET | LEVEL 05 ROOF | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 162 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET | LEVEL 05 ROOF | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 163 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET | LEVEL 05 ROOF | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 164 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 ROOF | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 165 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 166 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 167 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 168 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 169 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 ROOF | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 170 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 ROOF | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 171 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 172 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 173 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 174 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 175 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 176 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 177 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 178 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 179 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 180 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 181 | _HFH - Roof WALL-stair | LEVEL 05 ROOF | 365 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 182 | 084400_Curtain Wall - CW1 - Curve | LEVEL 05 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 183 | 084400_Curtain Wall - CW1A - Curve | LEVEL 05 ROOF | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 184 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 185 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 186 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 187 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 188 | _HFH - Roof WALL - 6" Stud | LEVEL 03 | 264 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 189 | _HFH - Roof WALL - NO BACKUP | LEVEL 03 | 111 | `B2010.10` | 75% | heuristic_function | _HFH -CMV - Brick Masonry Veneer-CMU backup |
| 190 | _HFH - Roof WALL - 6" Stud + Sheathing | LEVEL 03 | 279 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 191 | Exterior - Sheathing+8"Stud | LEVEL 03 | 235 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 192 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 193 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 194 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 195 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 196 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 197 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 198 | 084400_Curtain Wall - CW2C - Curve fixed number grid | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 199 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 200 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 201 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 202 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 203 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 204 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 205 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 206 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 207 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 208 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 209 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 210 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 211 | 084400_Curtain Wall - CW2B - Fin | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 212 | 084400_Curtain Wall - CW1B- tower | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 213 | 084400_Curtain Wall - CW1B- tower | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 214 | 084400_Curtain Wall - CW1B- tower | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 215 | 084400_Curtain Wall - CW1B - Curve | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 216 | 084400_Curtain Wall - CW1B - Curve | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 217 | 084400_Curtain Wall - CW1B - Curve | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 218 | 084400_Curtain Wall - CW1C (Old CW3B) | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 219 | 084400_Curtain Wall - CW1C | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 220 | 084400_Curtain Wall - CW1C - Perf Panel | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 221 | 084400_Curtain Wall - CW1C - Perf Panel | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 222 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 223 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 224 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 225 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 226 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 227 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 228 | 084400_Curtain Wall - CW1A - Curve | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 229 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer VMU |
| 230 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer VMU |
| 231 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer VMU |
| 232 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer VMU |
| 233 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer VMU |
| 234 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer VMU |
| 235 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer VMU |
| 236 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 04 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 237 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 04 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 238 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 04 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 239 | Foundation - 8" Concrete w/ Insulation | LEVEL 04 | 254 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 240 | _HFH - Roof WALL_polyiso | LEVEL 04 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 241 | _HFH - Roof WALL_polyiso | LEVEL 04 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 242 | _HFH - Roof WALL_polyiso | LEVEL 04 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 243 | 084400_Curtain Wall - CW1 - Curve | LEVEL 04 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 244 | 084400_Curtain Wall - CW1A - TYP | LEVEL 04 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 245 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 04 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 246 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 04 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 247 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 04 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 248 | 084100_Storefront - 4 1/2" - Defined - None | LEVEL 04 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl |
| 249 | 084400_Curtain Wall - CW2 - Fin | LEVEL 04 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 250 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 251 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 252 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 253 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 254 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 255 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 256 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 257 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 258 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 259 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 260 | Exterior - Insulated Metal Panel dble sided on 8" Metal Stud | LEVEL 05 | 394 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 261 | Exterior - Insulated Metal Panel dble sided on 8" Metal Stud | LEVEL 05 | 394 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 262 | Exterior - Insulated Metal Panel dble sided on 8" Metal Stud | LEVEL 05 | 394 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 263 | Exterior - Insulated Metal Panel on 6" Metal Stud | LEVEL 05 | 279 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 264 | Exterior - Insulated Metal Panel on 6" Metal Stud | LEVEL 05 | 279 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 265 | Exterior - Insulated Metal Panel on 6" Metal Stud | LEVEL 05 | 279 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 266 | Exterior - Insulated Metal Panel on 6" Metal Stud -2hr | LEVEL 05 | 311 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 267 | Exterior - Insulated Metal Panel on 6" Metal Stud -2hr | LEVEL 05 | 311 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 268 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 269 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 270 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 271 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 272 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 05 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 273 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 05 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 274 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 275 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 276 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 277 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 278 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 279 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 280 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 281 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 282 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 283 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 284 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 285 | Exterior - Insulated Parapet Wall (East&South) | LEVEL 05 | 143 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 286 | Exterior - Insulated Parapet Wall (East&South) | LEVEL 05 | 143 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 287 | Exterior - Insulated Parapet Wall (East&South) | LEVEL 05 | 143 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 288 | _HFH - Roof WALL - 6" Stud | LEVEL 05 | 264 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 289 | 084400_Curtain Wall - CW1 - Curve | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 290 | 084400_Curtain Wall - CW1 - Curve | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 291 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 292 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 293 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 294 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 295 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 296 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 297 | 084400_Curtain Wall - CW1A - Curve | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 298 | 084400_Curtain Wall - CW1A - Curve | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 299 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 300 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 301 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 302 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 303 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 304 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 305 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 306 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 307 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 308 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 309 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 310 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP |
| 311 | 084400_Curtain Wall - ALR 4' | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 312 | 084400_Curtain Wall - ALR 4' | LEVEL 05 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 313 | 084400_Curtain Wall - CW2B - Above ED | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 314 | 084400_Curtain Wall - CW2B - Above ED | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 315 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 316 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 317 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 318 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 319 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 320 | 084400_Curtain Wall - CW2B - Curve | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 321 | 084400_Curtain Wall - CW1A - TYP | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 322 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 323 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 324 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 325 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 326 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 327 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 328 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 329 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 330 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 331 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 332 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 333 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 334 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 335 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 336 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 337 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 338 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 339 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 340 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 341 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 342 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 343 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 344 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 345 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 346 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 347 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 348 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 349 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 350 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 351 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 352 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 353 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 354 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 355 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 356 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 357 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 358 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 359 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 360 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 361 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 362 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 363 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 364 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 365 | 084400_Curtain Wall - CW2B - Curve ED | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 366 | 084400_Curtain Wall - CW1C - Perf Panel | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 367 | 084400_Curtain Wall - CW1C | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 368 | 084400_Curtain Wall - CW1C | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 369 | 084400_Curtain Wall - CW1B- tower | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 370 | 084400_Curtain Wall - CW1B- tower | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 371 | 084400_Curtain Wall - ALR - CW1E | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 372 | 084400_Curtain Wall - ALR - CW1E | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 373 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 02 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG |
| 374 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 375 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 376 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 377 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 378 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 379 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 380 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 381 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 382 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | 75% | heuristic_function | Exterior - 8" Conc. Curb |
| 383 | Exterior - Insulated Metal Panel on 12" Metal Stud -2hr | LEVEL 19 | 464 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel VMU |
| 384 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 385 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 386 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 387 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 388 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 389 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 390 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 391 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 392 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 393 | 084400_Curtain Wall - ALR Curve - CWIE | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 394 | 084400_Curtain Wall - ALR Curve - CWIE | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 395 | 084400_Curtain Wall - ALR - Curve | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 396 | 084400_Curtain Wall - ALR - Curve | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 397 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 398 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 399 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 400 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 401 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 402 | _HFH - Roof WALL_mineral wool insulation | LEVEL 06 | 365 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - BRIDGE TOP |
| 403 | 084400_Curtain Wall - CW1A - TYP | LEVEL 06 | 0 | `B2010.10` | 75% | heuristic_function | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl |
| 404 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 21 HELIPAD | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG |
| 405 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 21 HELIPAD | 0 | `B2010.10` | 75% | heuristic_function | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG |

---

## Elements Not Conditioned (already Turner Level 4)

These walls already carry a Turner Level 4 code and were passed through unchanged.

| Type Name | Type Mark | Function | Width (mm) | Code | Count |
|-----------|-----------|----------|------------|------|-------|
| — | — | — | — | _none_ | 0 |

---

## Final Code Distribution (all elements)

Turner Level 4 codes (existing + predicted) vs. legacy codes still awaiting manual crosswalk review — kept separate so a passing run can't be misread as "fully conditioned".

| Code | Description | Count | Status |
|------|-------------|-------|--------|
| `B2010.10` | Exterior Wall Veneer | 399 | Level 4 |
| `C1010.10` | Interior Fixed Partitions | 6 | Level 4 |
| `B2010` | _legacy / non-Turner format_ | 2 | Needs review |
| `B2010160` | _legacy / non-Turner format_ | 73 | Needs review |
| `C1010145` | _legacy / non-Turner format_ | 100 | Needs review |

---
_Generated by Conditioning Demo POC · Speckle Automate_
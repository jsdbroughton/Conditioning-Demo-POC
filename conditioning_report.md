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
| Predicted via heuristic / default | 580 |
| Confidence threshold | 0.65 |

---

## Non-Level4 Codes (upgraded by conditioning)

These walls had existing codes in a non-Turner-Level4 format. A predicted Level 4 code has been applied; the original code is preserved in the `Original Assembly Code (upgraded)` property for review.

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

## Predictions

| # | Type Name | Level | Width (mm) | Predicted Code | Confidence | Method | Matched From |
|---|-----------|-------|------------|----------------|------------|--------|--------------|
| 1 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | — | heuristic_function | — |
| 2 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | — | heuristic_function | — |
| 3 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | — | heuristic_function | — |
| 4 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | — | heuristic_function | — |
| 5 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | — | heuristic_function | — |
| 6 | Exterior - 4" SCMU_6" STUD NonRated R10ci | LEVEL 01 | 356 | `B2010.10` | — | heuristic_function | — |
| 7 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl | LEVEL 01 | 489 | `B2010.10` | — | heuristic_function | — |
| 8 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl | LEVEL 01 | 489 | `B2010.10` | — | heuristic_function | — |
| 9 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl | LEVEL 01 | 489 | `B2010.10` | — | heuristic_function | — |
| 10 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl | LEVEL 01 | 489 | `B2010.10` | — | heuristic_function | — |
| 11 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl | LEVEL 01 | 489 | `B2010.10` | — | heuristic_function | — |
| 12 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -1 3/8" gl  CMV2 | LEVEL 01 | 521 | `B2010.10` | — | heuristic_function | — |
| 13 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | — | heuristic_function | — |
| 14 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | — | heuristic_function | — |
| 15 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | — | heuristic_function | — |
| 16 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | — | heuristic_function | — |
| 17 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | — | heuristic_function | — |
| 18 | Exterior - 4" SCMU_6" STUD 2HR R10ci | LEVEL 01 | 387 | `B2010.10` | — | heuristic_function | — |
| 19 | Exterior - 4" SCMU_6" STUD 2HR | LEVEL 01 | 464 | `B2010.10` | — | heuristic_function | — |
| 20 | Exterior - 4" SCMU_6" STUD 2HR | LEVEL 01 | 464 | `B2010.10` | — | heuristic_function | — |
| 21 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 22 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 23 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 24 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 25 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 26 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 27 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 28 | _HFH - GFRC | LEVEL 01 | 200 | `B2010.10` | — | heuristic_function | — |
| 29 | _HFH -CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl NO BRICK RETURN | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 30 | _HFH -CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl NO BRICK RETURN | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 31 | HFH - Cast Stone Sill 8" | LEVEL 01 | 394 | `B2010.10` | — | heuristic_function | — |
| 32 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 33 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 34 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 35 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 36 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 37 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 38 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 39 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 40 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 41 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 42 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 43 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 44 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 45 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 46 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 47 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 48 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 49 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 50 | HFH - Cast Stone Sill | LEVEL 01 | 368 | `B2010.10` | — | heuristic_function | — |
| 51 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | — | heuristic_function | — |
| 52 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | — | heuristic_function | — |
| 53 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | — | heuristic_function | — |
| 54 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | — | heuristic_function | — |
| 55 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | — | heuristic_function | — |
| 56 | HFH - Tubesteel - Vestibule INT | LEVEL 01 | 279 | `B2010.10` | — | heuristic_function | — |
| 57 | HFH - Cast Stone Sill 9" | LEVEL 01 | 394 | `B2010.10` | — | heuristic_function | — |
| 58 | HFH - Cast Stone Sill 9" | LEVEL 01 | 394 | `B2010.10` | — | heuristic_function | — |
| 59 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 60 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 61 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 62 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 63 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 64 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 65 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 66 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 67 | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell | LEVEL 01 | 479 | `B2010.10` | — | heuristic_function | — |
| 68 | _HFH - CMV - Brick Masonry Veneer-CMU backup - Cell | LEVEL 01 | 479 | `B2010.10` | — | heuristic_function | — |
| 69 | _HFH -CMV - Brick Masonry Veneer-CMU backup | LEVEL 01 | 479 | `B2010.10` | — | heuristic_function | — |
| 70 | _HFH -CMV - Brick Masonry Veneer-CMU backup | LEVEL 01 | 479 | `B2010.10` | — | heuristic_function | — |
| 71 | _HFH -CMV - Brick Masonry Veneer-CMU backup | LEVEL 01 | 479 | `B2010.10` | — | heuristic_function | — |
| 72 | _HFH -CMV - Brick Masonry Veneer-CMU backup | LEVEL 01 | 479 | `B2010.10` | — | heuristic_function | — |
| 73 | Exterior - 4" CMU_6" STUD | LEVEL 01 | 432 | `B2010.10` | — | heuristic_function | — |
| 74 | Exterior - 4" CMU_6" STUD | LEVEL 01 | 432 | `B2010.10` | — | heuristic_function | — |
| 75 | _HFH - Roof WALL - NO BACKUP | LEVEL 01 | 111 | `B2010.10` | — | heuristic_function | — |
| 76 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl WO Sweeps | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 77 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl WO Sweeps | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 78 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl WO Sweeps | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 79 | _HFH - CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl WO Sweeps | LEVEL 01 | 514 | `B2010.10` | — | heuristic_function | — |
| 80 | _HFH - Roof WALL - PARAPET | LEVEL 01 | 111 | `B2010.10` | — | heuristic_function | — |
| 81 | _HFH - Roof WALL - PARAPET | LEVEL 01 | 111 | `B2010.10` | — | heuristic_function | — |
| 82 | _HFH - Roof WALL - PARAPET | LEVEL 01 | 111 | `B2010.10` | — | heuristic_function | — |
| 83 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | — | heuristic_function | — |
| 84 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | — | heuristic_function | — |
| 85 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | — | heuristic_function | — |
| 86 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | — | heuristic_function | — |
| 87 | BRAKE METAL SLIDER ENCLOSURE WALL | LEVEL 01 | 286 | `C1010.10` | — | heuristic_function | — |
| 88 | *Schematic Design - 9" Interior | LEVEL 01 | 229 | `C1010.10` | — | heuristic_function | — |
| 89 | Exterior - 4" SCMU_8" CMU 2HR | LEVEL 01 | 444 | `B2010.10` | — | heuristic_function | — |
| 90 | _HFH -CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl NO BRICK RETURN VMU | LEVEL 01 | 498 | `B2010.10` | — | heuristic_function | — |
| 91 | _HFH -CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl NO BRICK RETURN VMU | LEVEL 01 | 498 | `B2010.10` | — | heuristic_function | — |
| 92 | _HFH -CMV - Brick Masonry Veneer. 1'-7 1/4" -2 3/8" gl NO BRICK RETURN VMU | LEVEL 01 | 498 | `B2010.10` | — | heuristic_function | — |
| 93 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel VMU | LEVEL 01 | 473 | `B2010.10` | — | heuristic_function | — |
| 94 | _HFH - BMV - Brick Masonry Veneer VMU | LEVEL 01 | 473 | `B2010.10` | — | heuristic_function | — |
| 95 | Exterior - 8" Conc. Curb | LEVEL 01 | 203 | `B2010.10` | — | heuristic_function | — |
| 96 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 97 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 98 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 99 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 100 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 101 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 102 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 103 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 104 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 105 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 106 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 107 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 108 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 109 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 110 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 111 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 112 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 113 | 084400_Curtain Wall - CW1A - TYP | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 114 | 084400_Curtain Wall - CW2A ED | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 115 | 084400_Curtain Wall - CW2A ED | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 116 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 117 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 118 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 119 | 084400_Curtain Wall - CW1A - Curve | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 120 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 121 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 122 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 123 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 124 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 125 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 126 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 127 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 128 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 129 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 130 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 131 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 132 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 133 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 134 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 135 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 136 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 137 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 138 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 139 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 140 | HFH - CW-2D_084400_Curtain Wall - 7 1/2" - Defined - None 2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 141 | 084400_Curtain Wall - CW2A | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 142 | HFH - CW-2A_084400_Curtain Wall - 10 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 143 | HFH - CW-2A_084400_Curtain Wall - 10 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 144 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 145 | HFH -081100_FR_HM_90min. | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 146 | HFH -081100_FR_HM_90min. | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 147 | HFH -081100_FR_HM_90min. | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 148 | HFH - CW-2A_084400_Curtain Wall - 7 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 149 | HFH - CW-2A_084400_Curtain Wall - 7 1/2" - Defined - None | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 150 | 084400_Curtain Wall - BRICK- VERTICAL 2' Mockup | LEVEL 01 | 0 | `B2010.10` | — | heuristic_function | — |
| 151 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 152 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 153 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 154 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 155 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 156 | _HFH - IMP1- Mtl Panel Wall | LEVEL 20 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 157 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 158 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 159 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 160 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 161 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 162 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 163 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 164 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 165 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 166 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 167 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 168 | _HFH - Roof WALL - PARAPET | LEVEL 20 ROOF | 111 | `B2010.10` | — | heuristic_function | — |
| 169 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 170 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 171 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 172 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 173 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 174 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 175 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 176 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 177 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 178 | 084400_Curtain Wall - ALR - CW1D | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 179 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 180 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 20 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 181 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | — | heuristic_function | — |
| 182 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | — | heuristic_function | — |
| 183 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | — | heuristic_function | — |
| 184 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | — | heuristic_function | — |
| 185 | _HFH - Perf. Mtl Screen Wall - Mech Equipment | LEVEL 05 ROOF | 57 | `B2010.10` | — | heuristic_function | — |
| 186 | _HFH - Roof WALL_polyiso | LEVEL 05 ROOF | 314 | `B2010.10` | — | heuristic_function | — |
| 187 | _HFH - Roof WALL_polyiso | LEVEL 05 ROOF | 314 | `B2010.10` | — | heuristic_function | — |
| 188 | _HFH - Roof WALL_polyiso | LEVEL 05 ROOF | 314 | `B2010.10` | — | heuristic_function | — |
| 189 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | — | heuristic_function | — |
| 190 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | — | heuristic_function | — |
| 191 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | — | heuristic_function | — |
| 192 | _HFH - Roof WALL_mineral wool insulation | LEVEL 05 ROOF | 365 | `B2010.10` | — | heuristic_function | — |
| 193 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET | LEVEL 05 ROOF | 362 | `B2010.10` | — | heuristic_function | — |
| 194 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET | LEVEL 05 ROOF | 362 | `B2010.10` | — | heuristic_function | — |
| 195 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET | LEVEL 05 ROOF | 362 | `B2010.10` | — | heuristic_function | — |
| 196 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 ROOF | 346 | `B2010.10` | — | heuristic_function | — |
| 197 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | — | heuristic_function | — |
| 198 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | — | heuristic_function | — |
| 199 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | — | heuristic_function | — |
| 200 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud_PARAPET 2 | LEVEL 05 ROOF | 362 | `B2010.10` | — | heuristic_function | — |
| 201 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 ROOF | 346 | `B2010.10` | — | heuristic_function | — |
| 202 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 ROOF | 346 | `B2010.10` | — | heuristic_function | — |
| 203 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 204 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 205 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 206 | _HFH - IMP1- Mtl Panel Wall | LEVEL 05 ROOF | 311 | `B2010.10` | — | heuristic_function | — |
| 207 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | — | heuristic_function | — |
| 208 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | — | heuristic_function | — |
| 209 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | — | heuristic_function | — |
| 210 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | — | heuristic_function | — |
| 211 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | — | heuristic_function | — |
| 212 | _HFH - Roof WALL-Plenum Curb | LEVEL 05 ROOF | 330 | `B2010.10` | — | heuristic_function | — |
| 213 | _HFH - Roof WALL-stair | LEVEL 05 ROOF | 365 | `B2010.10` | — | heuristic_function | — |
| 214 | 084400_Curtain Wall - CW1 - Curve | LEVEL 05 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 215 | 084400_Curtain Wall - CW1A - Curve | LEVEL 05 ROOF | 0 | `B2010.10` | — | heuristic_function | — |
| 216 | _HFH - BMV - Brick Masonry Veneer. 1'-7 1/4" - 1 3/8" air no wrap | LEVEL 03 | 489 | `B2010.10` | — | heuristic_function | — |
| 217 | _HFH - BMV - Brick Masonry Veneer. 2nd fl East | LEVEL 03 | 489 | `B2010.10` | — | heuristic_function | — |
| 218 | _HFH - BMV - Brick Masonry Veneer. 1'-7 1/4" - 1 3/8" air | LEVEL 03 | 489 | `B2010.10` | — | heuristic_function | — |
| 219 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | — | heuristic_function | — |
| 220 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | — | heuristic_function | — |
| 221 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | — | heuristic_function | — |
| 222 | _HFH - Roof WALL_polyiso | LEVEL 03 | 314 | `B2010.10` | — | heuristic_function | — |
| 223 | _HFH - Roof WALL - 6" Stud | LEVEL 03 | 264 | `B2010.10` | — | heuristic_function | — |
| 224 | _HFH - Roof WALL - NO BACKUP | LEVEL 03 | 111 | `B2010.10` | — | heuristic_function | — |
| 225 | _HFH - Roof WALL - 6" Stud + Sheathing | LEVEL 03 | 279 | `B2010.10` | — | heuristic_function | — |
| 226 | Exterior - Sheathing+8"Stud | LEVEL 03 | 235 | `B2010.10` | — | heuristic_function | — |
| 227 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 228 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 229 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 230 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 231 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 232 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 233 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 234 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 235 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 236 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 237 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 238 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 239 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 240 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 241 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 242 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 243 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 244 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 245 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 246 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 247 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 248 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 249 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 250 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 251 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 252 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 253 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 254 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 255 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 256 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 257 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 258 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 259 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 260 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 261 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 262 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 263 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 264 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 265 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 266 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 267 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 268 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 269 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 270 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 271 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 03 | 108 | `C1010.10` | — | heuristic_function | — |
| 272 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | — | heuristic_function | — |
| 273 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | — | heuristic_function | — |
| 274 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | — | heuristic_function | — |
| 275 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | — | heuristic_function | — |
| 276 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | — | heuristic_function | — |
| 277 | _HFH - Roof WALL - PARAPET | LEVEL 03 | 111 | `B2010.10` | — | heuristic_function | — |
| 278 | 084400_Curtain Wall - CW2C - Curve fixed number grid | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 279 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 280 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 281 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 282 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 283 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 284 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 285 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 286 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 287 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 288 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 289 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 290 | 084400_Curtain Wall - CW2 - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 291 | 084400_Curtain Wall - CW2B - Fin | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 292 | 084400_Curtain Wall - CW1B- tower | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 293 | 084400_Curtain Wall - CW1B- tower | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 294 | 084400_Curtain Wall - CW1B- tower | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 295 | 084400_Curtain Wall - CW1B - Curve | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 296 | 084400_Curtain Wall - CW1B - Curve | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 297 | 084400_Curtain Wall - CW1B - Curve | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 298 | 084400_Curtain Wall - CW1C (Old CW3B) | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 299 | 084400_Curtain Wall - CW1C | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 300 | 084400_Curtain Wall - CW1C - Perf Panel | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 301 | 084400_Curtain Wall - CW1C - Perf Panel | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 302 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 303 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 304 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 305 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 306 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 307 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 308 | 084400_Curtain Wall - CW1A - Curve | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 309 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 310 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 311 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 312 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 313 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 314 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 315 | 084400_Curtain Wall - BRICK- VERTICAL 5' | LEVEL 03 | 0 | `B2010.10` | — | heuristic_function | — |
| 316 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Top soldier | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 317 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Top soldier | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 318 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Top soldier | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 319 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Top soldier | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 320 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Top soldier | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 321 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Top soldier | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 322 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" Bottom soldier | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 323 | _HFH - BMV - BRIDGE TOP | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 324 | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 325 | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 326 | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 327 | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 328 | _HFH - BMV - Brick Masonry Veneer. Generic 2 3/8" AG | LEVEL 04 | 514 | `B2010.10` | — | heuristic_function | — |
| 329 | _HFH - BMV - Brick Masonry Veneer. Generic 1 3/8" AG | LEVEL 04 | 489 | `B2010.10` | — | heuristic_function | — |
| 330 | _HFH - BMV - Brick Masonry Veneer. Generic 1 3/8" AG | LEVEL 04 | 489 | `B2010.10` | — | heuristic_function | — |
| 331 | _HFH - BMV - Brick Masonry Veneer. Generic 1 3/8" AG | LEVEL 04 | 489 | `B2010.10` | — | heuristic_function | — |
| 332 | _HFH - BMV - Brick Masonry Veneer. Generic 1 3/8" AG | LEVEL 04 | 489 | `B2010.10` | — | heuristic_function | — |
| 333 | _HFH - BMV - Brick Masonry Veneer. Generic 1 3/8" AG | LEVEL 04 | 489 | `B2010.10` | — | heuristic_function | — |
| 334 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 04 | 416 | `B2010.10` | — | heuristic_function | — |
| 335 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 04 | 416 | `B2010.10` | — | heuristic_function | — |
| 336 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 04 | 416 | `B2010.10` | — | heuristic_function | — |
| 337 | Foundation - 8" Concrete w/ Insulation | LEVEL 04 | 254 | `B2010.10` | — | heuristic_function | — |
| 338 | _HFH - Roof WALL_polyiso | LEVEL 04 | 314 | `B2010.10` | — | heuristic_function | — |
| 339 | _HFH - Roof WALL_polyiso | LEVEL 04 | 314 | `B2010.10` | — | heuristic_function | — |
| 340 | _HFH - Roof WALL_polyiso | LEVEL 04 | 314 | `B2010.10` | — | heuristic_function | — |
| 341 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 342 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 343 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 344 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 345 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 346 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 347 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 348 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 349 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 350 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 351 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 352 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 353 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 354 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 355 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 356 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 357 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 04 | 117 | `C1010.10` | — | heuristic_function | — |
| 358 | 084400_Curtain Wall - CW1 - Curve | LEVEL 04 | 0 | `B2010.10` | — | heuristic_function | — |
| 359 | 084400_Curtain Wall - CW1A - TYP | LEVEL 04 | 0 | `B2010.10` | — | heuristic_function | — |
| 360 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 04 | 0 | `B2010.10` | — | heuristic_function | — |
| 361 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 04 | 0 | `B2010.10` | — | heuristic_function | — |
| 362 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 04 | 0 | `B2010.10` | — | heuristic_function | — |
| 363 | 084100_Storefront - 4 1/2" - Defined - None | LEVEL 04 | 0 | `B2010.10` | — | heuristic_function | — |
| 364 | 084400_Curtain Wall - CW2 - Fin | LEVEL 04 | 0 | `B2010.10` | — | heuristic_function | — |
| 365 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 366 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 367 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 368 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 369 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 370 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 371 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 372 | _HFH - BMV - Brick Masonry Veneer. 1'-7 7/8" CRV TOP | LEVEL 05 | 514 | `B2010.10` | — | heuristic_function | — |
| 373 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 374 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 375 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 376 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 377 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 378 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 379 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 380 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 381 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 382 | Exterior - Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 383 | Exterior - Insulated Metal Panel dble sided on 8" Metal Stud | LEVEL 05 | 394 | `B2010.10` | — | heuristic_function | — |
| 384 | Exterior - Insulated Metal Panel dble sided on 8" Metal Stud | LEVEL 05 | 394 | `B2010.10` | — | heuristic_function | — |
| 385 | Exterior - Insulated Metal Panel dble sided on 8" Metal Stud | LEVEL 05 | 394 | `B2010.10` | — | heuristic_function | — |
| 386 | Exterior - Insulated Metal Panel on 6" Metal Stud | LEVEL 05 | 279 | `B2010.10` | — | heuristic_function | — |
| 387 | Exterior - Insulated Metal Panel on 6" Metal Stud | LEVEL 05 | 279 | `B2010.10` | — | heuristic_function | — |
| 388 | Exterior - Insulated Metal Panel on 6" Metal Stud | LEVEL 05 | 279 | `B2010.10` | — | heuristic_function | — |
| 389 | Exterior - Insulated Metal Panel on 6" Metal Stud -2hr | LEVEL 05 | 311 | `B2010.10` | — | heuristic_function | — |
| 390 | Exterior - Insulated Metal Panel on 6" Metal Stud -2hr | LEVEL 05 | 311 | `B2010.10` | — | heuristic_function | — |
| 391 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | — | heuristic_function | — |
| 392 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | — | heuristic_function | — |
| 393 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | — | heuristic_function | — |
| 394 | Exterior - Insulated Metal Panel on 8" Metal Stud -2hr | LEVEL 05 | 362 | `B2010.10` | — | heuristic_function | — |
| 395 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 05 | 416 | `B2010.10` | — | heuristic_function | — |
| 396 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 05 | 416 | `B2010.10` | — | heuristic_function | — |
| 397 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 398 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 399 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 400 | _HFH - Roof WALL_polyiso | LEVEL 05 | 314 | `B2010.10` | — | heuristic_function | — |
| 401 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 | 346 | `B2010.10` | — | heuristic_function | — |
| 402 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 | 346 | `B2010.10` | — | heuristic_function | — |
| 403 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud 2 | LEVEL 05 | 346 | `B2010.10` | — | heuristic_function | — |
| 404 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | — | heuristic_function | — |
| 405 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | — | heuristic_function | — |
| 406 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | — | heuristic_function | — |
| 407 | Exterior - Perforated Screen with Insulated Metal Panel on 8" Metal Stud | LEVEL 05 | 346 | `B2010.10` | — | heuristic_function | — |
| 408 | Exterior - Insulated Parapet Wall (East&South) | LEVEL 05 | 143 | `B2010.10` | — | heuristic_function | — |
| 409 | Exterior - Insulated Parapet Wall (East&South) | LEVEL 05 | 143 | `B2010.10` | — | heuristic_function | — |
| 410 | Exterior - Insulated Parapet Wall (East&South) | LEVEL 05 | 143 | `B2010.10` | — | heuristic_function | — |
| 411 | _HFH - Roof WALL - 6" Stud | LEVEL 05 | 264 | `B2010.10` | — | heuristic_function | — |
| 412 | Type L6 - Furring - Single Sided GWB - NFR - STC-NA - 6" Stud | LEVEL 05 | 168 | `C1010.10` | — | heuristic_function | — |
| 413 | 084400_Curtain Wall - CW1 - Curve | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 414 | 084400_Curtain Wall - CW1 - Curve | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 415 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 416 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 417 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 418 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 419 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 420 | 084400_Curtain Wall - CW1A - TYP | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 421 | 084400_Curtain Wall - CW1A - Curve | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 422 | 084400_Curtain Wall - CW1A - Curve | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 423 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 424 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 425 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 426 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 427 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 428 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 429 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 430 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 431 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 432 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 433 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 434 | 084400_Curtain Wall - ALR LVR-1 | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 435 | 084400_Curtain Wall - ALR 4' | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 436 | 084400_Curtain Wall - ALR 4' | LEVEL 05 | 0 | `B2010.10` | — | heuristic_function | — |
| 437 | _HFH - BMV - Brick Masonry Veneer. 2nd fl | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 438 | _HFH - BMV - Brick Masonry Veneer. 2nd fl | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 439 | _HFH - BMV - Brick Masonry Veneer. 2nd fl | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 440 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 441 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 442 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 443 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 444 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 445 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 446 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 447 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 448 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 449 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 450 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 451 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 452 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 453 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 454 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 455 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 456 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 457 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 458 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 459 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 460 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 461 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 462 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 463 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 464 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 465 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 466 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 467 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 468 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 469 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 470 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 471 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 472 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 473 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 474 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 475 | Type K3 - Furring - Single Sided GWB - NFR - STC-NA - 3-5/8" Stud - 6" AFC | LEVEL 02 | 108 | `C1010.10` | — | heuristic_function | — |
| 476 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 477 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 478 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 479 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 480 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 481 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 482 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 483 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 484 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 485 | _HFH - BMV - Brick Masonry Veneer. 2nd fl channel | LEVEL 02 | 489 | `B2010.10` | — | heuristic_function | — |
| 486 | Exterior - 60" Concrete | LEVEL 02 | 1524 | `B2010.10` | — | heuristic_function | — |
| 487 | 084400_Curtain Wall - CW2B - Above ED | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 488 | 084400_Curtain Wall - CW2B - Above ED | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 489 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 490 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 491 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 492 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 493 | 084400_Curtain Wall - CW2B | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 494 | 084400_Curtain Wall - CW2B - Curve | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 495 | 084400_Curtain Wall - CW1A - TYP | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 496 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 497 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 498 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 499 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 500 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 501 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 502 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 503 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 504 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 505 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 506 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 507 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 508 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 509 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 510 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 511 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 512 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 513 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 514 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 515 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 516 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 517 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 518 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 519 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 520 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 521 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 522 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 523 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 524 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 525 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 526 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 527 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 528 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 529 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 530 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 531 | HFH - CW2C_084400_Curtain Wall - 8 3/4" - Defined - FINS | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 532 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 533 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 534 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 535 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 536 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 537 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 538 | 084400_Curtain Wall - CW2 - Fin | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 539 | 084400_Curtain Wall - CW2B - Curve ED | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 540 | 084400_Curtain Wall - CW1C - Perf Panel | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 541 | 084400_Curtain Wall - CW1C | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 542 | 084400_Curtain Wall - CW1C | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 543 | 084400_Curtain Wall - CW1B- tower | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 544 | 084400_Curtain Wall - CW1B- tower | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 545 | 084400_Curtain Wall - ALR - CW1E | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 546 | 084400_Curtain Wall - ALR - CW1E | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 547 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 02 | 0 | `B2010.10` | — | heuristic_function | — |
| 548 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 549 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 550 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 551 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 552 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 553 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 554 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 555 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 556 | Exterior - Insulated Metal Panel on 12" Metal Stud | LEVEL 19 | 416 | `B2010.10` | — | heuristic_function | — |
| 557 | Exterior - Insulated Metal Panel on 12" Metal Stud -2hr | LEVEL 19 | 464 | `B2010.10` | — | heuristic_function | — |
| 558 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 559 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 560 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 561 | 084400_Curtain Wall - ALR Curve - CWID | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 562 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 563 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 564 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 565 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 566 | 084400_Curtain Wall - ALR - CW1D | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 567 | 084400_Curtain Wall - ALR Curve - CWIE | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 568 | 084400_Curtain Wall - ALR Curve - CWIE | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 569 | 084400_Curtain Wall - ALR - Curve | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 570 | 084400_Curtain Wall - ALR - Curve | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 571 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 572 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 573 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 574 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 575 | 084400_Curtain Wall - ALR - CW1E | LEVEL 19 | 0 | `B2010.10` | — | heuristic_function | — |
| 576 | _HFH - Roof WALL_mineral wool insulation | LEVEL 06 | 365 | `B2010.10` | — | heuristic_function | — |
| 577 | 084400_Curtain Wall - CW1A - TYP | LEVEL 06 | 0 | `B2010.10` | — | heuristic_function | — |
| 578 | Type L4 - Furring - Single Sided GWB - NFR - STC-NA - 4" Stud | LEVEL 21 HELIPAD | 117 | `C1010.10` | — | heuristic_function | — |
| 579 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 21 HELIPAD | 0 | `B2010.10` | — | heuristic_function | — |
| 580 | 084400_Curtain Wall - ALR LVR-2 | LEVEL 21 HELIPAD | 0 | `B2010.10` | — | heuristic_function | — |

---

## Elements Not Conditioned (already Turner Level 4)

These walls already carry a Turner Level 4 code and were passed through unchanged.

| Type Name | Type Mark | Function | Width (mm) | Code | Count |
|-----------|-----------|----------|------------|------|-------|
| — | — | — | — | _none_ | 0 |

---

## Final Code Distribution (all elements)

| Code | Description | Count |
|------|-------------|-------|
| `B2010.10` | Exterior Wall Veneer | 474 |
| `C1010.10` | Interior Fixed Partitions | 106 |

---
_Generated by Conditioning Demo POC · Speckle Automate_
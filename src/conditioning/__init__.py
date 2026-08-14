"""Business logic for the Conditioning Demo POC Speckle Automate function.

main.py at the repo root is the orchestrator — it wires these modules
together and is the only thing the Speckle Automate runtime invokes directly.
Everything in this package is plain, independently testable logic with no
dependency on `speckle_automate.AutomationContext` except `speckle_io`, which
is the one module that actually talks back to Speckle.

Module map:
  codes.py       Uniformat code reference data + code-format detection
                 (Level 4 dot-notation vs. legacy ASTM 3-digit suffix).
  walls.py       Extracting WallRecord data from raw Speckle DataObjects, and
                 classifying a wall list into coded/level4/uncoded buckets.
  predict.py     The prediction engine: fingerprint similarity + heuristic
                 fallback, producing Prediction objects for uncoded walls.
  report.py      Markdown conditioning report builder.
  speckle_io.py  Everything that writes back to Speckle: imprinting results
                 onto wall properties, viewer annotations, and creating the
                 'Conditioned' model version.
"""

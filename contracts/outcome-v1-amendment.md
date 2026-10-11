# Q03 outcome v1 field-type clarification — 2026-10-11

Additive clarification of outcome-v1.md, whose original text is preserved.
Official Match-V5 marks gameStartTimestamp and gameEndTimestamp as long.
The numeric timestamp gate therefore requires known nonnegative integers,
gameEndTimestamp >= gameStartTimestamp. A missing, boolean, fractional or
nonfinite value contributes no result observation. This verifies the modern
duration representation, never computes a duration by timestamp subtraction.
Even a delayed gameEndTimestamp leaves the reported gameDuration bin unchanged.

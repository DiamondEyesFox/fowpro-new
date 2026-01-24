# Shared Utilities (fowpro/shared/*)

## Will computation
- `fowpro/shared/will.py` provides:
  - `WillCost` and helpers to check/pay costs.
  - `can_pay_cost()` and `compute_payment()` used by v2 (and potentially v1).
- v1 has its own `WillPool`/`WillCost` in `models.py` as well, creating duplication.

## Observed risk
- Parallel cost logic in v1 and shared can diverge; v2 uses shared utilities, v1 uses `models.WillPool`.
- `fowpro/shared/__init__.py` notes TODOs for shared card database and asset management that are not implemented.

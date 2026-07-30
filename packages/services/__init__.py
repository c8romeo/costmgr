"""packages.services — orchestration layer.

AD-11: services may import packages.ports and packages.cost_engine.ports.
services may NOT import packages.cost_engine.core directly.
services may NOT import apps.api.

Future services:
  - month_input_adapter    (AD-13: only caller of engine input ports)
  - calc_orchestrator      (M3 dispatch, AD-19)
  - verification_runner    (V1→V4→V7→V8, AD-12)
  - reversal_handler       (Epic 11)
"""

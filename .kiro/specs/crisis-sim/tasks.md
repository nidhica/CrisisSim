# CrisisSim Implementation Tasks

## Phase 1 — Pure Simulation Engine

- [ ] 1. Create engine package structure and models
  - [x] 1.1 Create `backend/engine/__init__.py`
  - [x] 1.2 Implement `backend/engine/models.py` with all dataclasses
  - [x] 1.3 Create `backend/engine/tests/__init__.py`

- [-] 2. Implement risk_scorer.py
  - [ ] 2.1 Implement `calculate_risk_score()` with exact weights
  - [ ] 2.2 Implement `_risk_level()` with decimal-safe boundaries
  - [ ] 2.3 Implement `calculate_zone_results()`

- [-] 3. Implement response_time.py
  - [ ] 3.1 Implement `estimate_response_time()` with exact formula
  - [ ] 3.2 Handle zero demand_units safely

- [-] 4. Implement bottleneck_detector.py
  - [ ] 4.1 Resource shortage detection
  - [ ] 4.2 Shelter capacity detection
  - [ ] 4.3 Hospital capacity detection (effective_capacity = capacity + surge_capacity)
  - [ ] 4.4 Road access detection
  - [ ] 4.5 Sort by severity descending

- [-] 5. Implement intervention_engine.py
  - [ ] 5.1 Baseline strategy (state unchanged)
  - [ ] 5.2 Resource reallocation (zone params only, min floor enforced)
  - [ ] 5.3 Capacity expansion (shelters +20%, hospitals +15%)
  - [ ] 5.4 Combined strategy (reuse 5.2 + 5.3, no duplicate logic)
  - [ ] 5.5 Return `dict[str, SimulationState]`

- [-] 6. Implement evaluator.py
  - [ ] 6.1 Run same pipeline (zone_results + bottlenecks) on each modified state
  - [ ] 6.2 Calculate all required metrics per strategy

- [-] 7. Implement recommender.py
  - [ ] 7.1 Normalize metrics across four strategies
  - [ ] 7.2 Apply exact recommendation weights
  - [ ] 7.3 Deterministic tie-breaking by risk_reduction_pct

- [ ] 8. Implement run_full_simulation() orchestrator in engine/__init__.py

- [-] 9. Write engine tests
  - [ ] 9.1 test_risk_scorer.py (P-1, P-2, P-3, boundaries, edge cases)
  - [ ] 9.2 test_response_time.py (P-4, P-5, edge cases)
  - [ ] 9.3 test_bottleneck_detector.py (P-5, shelter/hospital edge cases)
  - [ ] 9.4 test_intervention_engine.py (resource constraints, state completeness)
  - [ ] 9.5 test_evaluator.py (P-8, before/after accuracy)
  - [ ] 9.6 test_recommender.py (P-6, P-7, tie-breaking)

- [x] 10. Create backend/requirements-dev.txt and verify all tests pass

## Phase 2 — Local Backend API

- [x] 11. Implement seed_data.py with hardcoded flood scenario
- [x] 12. Implement persistence/memory_store.py (local in-memory store)
- [x] 13. Implement handlers (thin wrappers)
- [x] 14. Implement bedrock/explainer.py with fallback
- [x] 15. Implement local_server.py (FastAPI)
- [x] 16. Add endpoint tests

## Phase 3 — Frontend

- [ ] 17. Scaffold Vite + React + TypeScript project
- [ ] 18. Define types/index.ts
- [ ] 19. Implement API service layer
- [ ] 20. Implement contexts (ScenarioContext, SimulationContext)
- [ ] 21. Build ScenarioSelectPage
- [ ] 22. Build DashboardPage + layout
- [ ] 23. Build SimMap with Leaflet
- [ ] 24. Build dashboard components
- [ ] 25. Build WhatIfPanel
- [ ] 26. Build results components
- [ ] 27. Wire everything together and verify full user flow

## Phase 4 — AWS Deployment

- [ ] 28. DynamoDB table setup and seed
- [ ] 29. Lambda handlers packaging
- [ ] 30. API Gateway configuration
- [ ] 31. Bedrock integration (live)
- [ ] 32. Amplify frontend deployment

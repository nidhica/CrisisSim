# CrisisSim Technical Design

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                     │
│                                                                      │
│  ┌──────────────┐    ┌─────────────────┐    ┌───────────────────┐   │
│  │ AWS Amplify  │    │  API Gateway    │    │  AWS Lambda       │   │
│  │  (Frontend)  │───▶│  (REST API)     │───▶│  (Handler Layer)  │   │
│  │  React/TS    │◀───│                 │◀───│                   │   │
│  └──────────────┘    └─────────────────┘    └────────┬──────────┘   │
│                                                       │              │
│                                              ┌────────▼──────────┐  │
│                                              │  Simulation Engine │  │
│                                              │  (Pure Python)     │  │
│                                              │  - risk_scorer     │  │
│                                              │  - response_time   │  │
│                                              │  - bottleneck      │  │
│                                              │  - interventions   │  │
│                                              │  - recommender     │  │
│                                              └────────┬──────────┘  │
│                                                       │              │
│                                 ┌─────────────────────▼──────────┐  │
│                                 │        DynamoDB                  │  │
│                                 │  (Scenarios + Simulation State) │  │
│                                 └─────────────────────────────────┘  │
│                                                                      │
│  AI Explanation Flow:                                                │
│  Lambda ──(structured result)──▶ Amazon Bedrock ──▶ Lambda ──▶ API  │
│                                                                      │
│  Observability:                                                      │
│  All Lambda functions ──▶ Amazon CloudWatch Logs                    │
└─────────────────────────────────────────────────────────────────────┘

Local Development (no AWS required):
  React (Vite) ──▶ FastAPI (local) ──▶ Simulation Engine (pure Python)
                                    ──▶ In-memory / JSON file store
```

### Data Flow — Simulation Run

```
1. User adjusts What-If parameters (local draft state in React)
2. User clicks "Run Simulation"
3. POST /simulate → API Gateway → Lambda handler
4. Handler loads scenario from DynamoDB
5. Handler calls simulation engine with merged parameters
6. Engine: risk_scorer → response_time → bottleneck → interventions → recommender
7. Result written back to DynamoDB (simulation_result item)
8. Response returned to frontend
9. Frontend updates dashboard, map, comparison view, before/after
```

### Data Flow — AI Explanation

```
1. User clicks "Explain Recommendation"
2. POST /explain → API Gateway → Lambda handler
3. Handler loads simulation result from DynamoDB
4. Handler builds structured prompt with full simulation data
5. Lambda calls Bedrock (Claude) with prompt
6. Bedrock returns plain-language explanation
7. Explanation returned to frontend and displayed
```

---

## 2. Frontend Architecture

### Technology
- React 18 + TypeScript
- Vite (build tool)
- Leaflet + React-Leaflet (map)
- OpenStreetMap tiles
- React Context for state management (no Redux needed for MVP scope)
- Axios for HTTP calls

### Pages

| Page | Route | Purpose |
|------|-------|---------|
| ScenarioSelect | `/` | Lists available scenarios |
| Dashboard | `/scenario/:id` | Main simulation view |

The app is effectively two pages. The dashboard is the primary surface and contains all simulation functionality.

### Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  Header: CrisisSim | Scenario name | Severity badge              │
├─────────────────────────┬────────────────────────────────────────┤
│  Left Panel (30%)       │  Map Panel (70%)                       │
│  ┌─────────────────┐    │  Leaflet/OSM interactive map           │
│  │ MetricsSummary  │    │  - color-coded zones                   │
│  │ - zones at risk │    │  - resource icons                      │
│  │ - population    │    │  - shelter / hospital markers          │
│  │ - avg resp time │    │  - click zone → ZoneDetailPanel        │
│  │ - bottleneck    │    │                                        │
│  └─────────────────┘    │                                        │
│  ┌─────────────────┐    │                                        │
│  │ RiskRankingList │    │                                        │
│  └─────────────────┘    │                                        │
├─────────────────────────┴────────────────────────────────────────┤
│  WhatIfPanel (collapsible)                                        │
│  - Parameter sliders + inputs                                     │
│  - [Run Simulation] button   [Reset] button                      │
├──────────────────────────────────────────────────────────────────┤
│  SimulationResults (shown after run)                             │
│  Tabs: [ Comparison ] [ Before vs After ] [ AI Explanation ]     │
└──────────────────────────────────────────────────────────────────┘
```

### Major Components

```
src/
  components/
    layout/
      Header.tsx
      Sidebar.tsx
    dashboard/
      MetricsSummary.tsx       # top-level KPI cards
      RiskRankingList.tsx      # sortable zone risk list
      BottleneckAlert.tsx      # primary bottleneck callout
    map/
      SimMap.tsx               # Leaflet map container
      ZoneLayer.tsx            # colored zone polygons
      ResourceMarkers.tsx      # ambulance / rescue team icons
      FacilityMarkers.tsx      # shelters and hospitals
      ZoneDetailPanel.tsx      # click-to-open zone info panel
    simulator/
      WhatIfPanel.tsx          # parameter controls
      ZoneParameterRow.tsx     # per-zone sliders
    results/
      ComparisonTable.tsx      # 4-strategy side-by-side
      BeforeAfterToggle.tsx    # before/after map + metrics
      AIExplanation.tsx        # Bedrock explanation display
    common/
      SeverityBadge.tsx
      LoadingSpinner.tsx
      ErrorBanner.tsx
```

### State Management

React Context is sufficient. Two contexts:

**ScenarioContext**
- `scenario`: loaded scenario data (zones, resources, facilities)
- `loadScenario(id)`: fetches from API

**SimulationContext**
- `draftParams`: local What-If parameter state (not yet run)
- `simulationResult`: last persisted simulation result
- `isRunning`: loading flag
- `runSimulation()`: POSTs draft params, updates result
- `resetParams()`: restores draftParams to scenario defaults
- `explanation`: Bedrock explanation string
- `fetchExplanation()`: calls /explain endpoint

### API Service Layer

```
src/services/
  api.ts          # Axios instance with base URL from env
  scenarios.ts    # getScenarios(), getScenario(id)
  simulation.ts   # runSimulation(id, params)
  explanation.ts  # getExplanation(simulationResultId)
```

Base URL read from `VITE_API_BASE_URL` environment variable.

### TypeScript Interfaces

```typescript
// Zone input parameters (What-If adjustable)
interface ZoneParams {
  zone_id: string;
  flood_severity: number;       // 0.0–1.0
  affected_population: number;  // 0–100000
  medical_urgency: number;      // 0.0–1.0
  road_accessibility: number;   // 0.0–1.0 (1 = fully accessible)
  rescue_teams: number;         // count
  ambulances: number;           // count
}

interface Zone extends ZoneParams {
  name: string;
  coordinates: [number, number][];  // polygon lat/lng
  centroid: [number, number];
}

interface Shelter {
  shelter_id: string;
  name: string;
  coordinates: [number, number];
  capacity: number;
  current_occupancy: number;
}

interface Hospital {
  hospital_id: string;
  name: string;
  coordinates: [number, number];
  capacity: number;
  surge_capacity: number;
  current_occupancy: number;
}

interface Scenario {
  scenario_id: string;
  name: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  zones: Zone[];
  shelters: Shelter[];
  hospitals: Hospital[];
}

interface ZoneResult {
  zone_id: string;
  risk_score: number;           // 0–100
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  response_time_minutes: number;
  risk_components: {
    affected_population_score: number;
    flood_severity_score: number;
    medical_urgency_score: number;
    road_accessibility_score: number;
    resource_shortage_score: number;
  };
}

interface Bottleneck {
  type: 'resource_shortage' | 'shelter_capacity' | 'hospital_capacity' | 'road_access';
  zone_id: string | null;
  description: string;
  severity_score: number;
}

interface InterventionResult {
  strategy: 'baseline' | 'resource_reallocation' | 'capacity_expansion' | 'combined';
  label: string;
  zone_results: ZoneResult[];
  avg_risk_score: number;
  avg_response_time_minutes: number;
  risk_reduction_pct: number;
  response_time_improvement_minutes: number;
  bottleneck_resolution_score: number;
  resource_cost: number;
  composite_score: number;
}

interface SimulationResult {
  result_id: string;
  scenario_id: string;
  run_at: string;
  params_used: ZoneParams[];
  baseline_zone_results: ZoneResult[];
  bottlenecks: Bottleneck[];
  interventions: InterventionResult[];
  recommended_strategy: string;
}
```

---

## 3. Backend Architecture

### Python Module Structure

```
backend/
  engine/                     # Pure simulation logic — no AWS, no HTTP
    __init__.py
    risk_scorer.py            # calculate_risk_score()
    response_time.py          # estimate_response_time()
    bottleneck_detector.py    # detect_bottlenecks()
    intervention_engine.py    # generate_intervention_params()
    evaluator.py              # evaluate_intervention()
    recommender.py            # rank_and_recommend()
    models.py                 # Python dataclasses matching TypeScript interfaces

  handlers/                   # Lambda entry points (thin wrappers)
    get_scenarios.py          # GET /scenarios
    get_scenario.py           # GET /scenarios/{id}
    run_simulation.py         # POST /simulate
    get_result.py             # GET /results/{id}
    get_explanation.py        # POST /explain

  persistence/
    dynamodb.py               # DynamoDB read/write helpers

  bedrock/
    explainer.py              # Bedrock prompt construction + invocation

  local_server.py             # FastAPI dev server (local only, not deployed)
  seed_data.py                # Loads default scenario into DynamoDB (or in-memory)
```

**Key principle:** `engine/` has zero AWS imports. It can be imported and tested locally with plain `pytest` — no mocking of AWS services needed.

### Lambda Handler Pattern

Each handler follows the same thin pattern:

```python
# handlers/run_simulation.py
import json
from engine.risk_scorer import calculate_risk_score
from engine.response_time import estimate_response_time
from engine.bottleneck_detector import detect_bottlenecks
from engine.intervention_engine import generate_intervention_params
from engine.evaluator import evaluate_intervention
from engine.recommender import rank_and_recommend
from persistence.dynamodb import load_scenario, save_simulation_result

def handler(event, context):
    try:
        body = json.loads(event['body'])
        scenario = load_scenario(body['scenario_id'])
        params = body['params']  # list of ZoneParams dicts
        # run engine
        result = run_full_simulation(scenario, params)
        save_simulation_result(result)
        return {'statusCode': 200, 'body': json.dumps(result)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
```

---

## 4. Simulation Engine Design

### SimulationState — Core Input Model

All simulation engine functions operate on a `SimulationState`, not a bare list of `ZoneParams`. This ensures capacity expansion strategies can modify shelters and hospitals alongside zone parameters.

```python
@dataclass
class SimulationState:
    zones: list[ZoneParams]        # per-zone adjustable parameters
    shelters: list[Shelter]        # current shelter state (capacity + occupancy)
    hospitals: list[Hospital]      # current hospital state (capacity + surge + occupancy)
```

The intervention engine generates one `SimulationState` per strategy. All four states are passed through the same simulation pipeline — no duplicated logic per strategy.

### Module Responsibilities and Data Flow

```
Input: SimulationState (zones + shelters + hospitals) + population_max
         │
         ▼
  risk_scorer.py
    calculate_zone_results(state, population_max)
      → List[ZoneResult]  (risk_score, risk_level, response_time, components per zone)
         │
         ▼
  bottleneck_detector.py
    detect_bottlenecks(zone_results, state.shelters, state.hospitals)
      → List[Bottleneck]
         │
         ▼
  intervention_engine.py
    generate_simulation_states(baseline_state, zone_results, bottlenecks)
      → Dict[strategy_name, SimulationState]
           "baseline"              → baseline_state unchanged
           "resource_reallocation" → modified zones only
           "capacity_expansion"    → modified shelters + hospitals only
           "combined"              → modified zones + shelters + hospitals
         │
         ▼
  evaluator.py (called once per strategy)
    evaluate_intervention(strategy, modified_state, baseline_zone_results, population_max)
      → InterventionResult
      (runs risk_scorer + bottleneck_detector on modified_state internally)
         │
         ▼
  recommender.py
    rank_and_recommend(interventions) → recommended_strategy, ranked_list
```

### risk_scorer.py

`calculate_zone_results` iterates all zones in a `SimulationState` and returns one `ZoneResult` per zone. Response time is calculated in the same pass (no separate module call needed from outside).

```python
WEIGHTS = {
    'affected_population': 0.25,
    'flood_severity':      0.25,
    'medical_urgency':     0.25,
    'road_accessibility':  0.15,  # inverted: high accessibility = low risk
    'resource_shortage':   0.10,  # inverted: high coverage = low shortage
}
# Weights must sum to exactly 1.0

def _risk_level(score: float) -> str:
    """Deterministic boundary mapping for decimal-safe classification."""
    if score <= 25:
        return "low"
    elif score <= 50:
        return "medium"
    elif score <= 75:
        return "high"
    else:
        return "critical"

def calculate_risk_score(zone: ZoneParams, population_max: int) -> tuple[float, dict]:
    """
    Returns (risk_score, components_dict).
    All inputs normalized to [0, 1].
    road_accessibility and resource_coverage inverted so higher raw = lower risk.
    resource_coverage = clamp((rescue_teams + ambulances) / demand_units, 0, 1)
    population normalized against scenario population_max.
    Score = weighted_sum * 100, clamped to [0, 100].
    """
    pop_norm = min(zone.affected_population / population_max, 1.0)
    flood_norm = zone.flood_severity
    medical_norm = zone.medical_urgency
    road_risk = 1.0 - zone.road_accessibility
    resource_coverage = min((zone.rescue_teams + zone.ambulances) / zone.demand_units, 1.0)
    resource_shortage = 1.0 - resource_coverage

    components = {
        'affected_population_score': WEIGHTS['affected_population'] * pop_norm,
        'flood_severity_score':      WEIGHTS['flood_severity']      * flood_norm,
        'medical_urgency_score':     WEIGHTS['medical_urgency']     * medical_norm,
        'road_accessibility_score':  WEIGHTS['road_accessibility']  * road_risk,
        'resource_shortage_score':   WEIGHTS['resource_shortage']   * resource_shortage,
    }
    raw = sum(components.values())
    score = round(min(max(raw * 100, 0.0), 100.0), 2)
    return score, components

def calculate_zone_results(state: SimulationState, population_max: int) -> list[ZoneResult]:
    results = []
    for zone in state.zones:
        score, components = calculate_risk_score(zone, population_max)
        rt = estimate_response_time(zone)
        results.append(ZoneResult(
            zone_id=zone.zone_id,
            risk_score=score,
            risk_level=_risk_level(score),
            response_time_minutes=rt,
            risk_components=components,
        ))
    return results
```

### response_time.py

Folded into `risk_scorer.py`'s `calculate_zone_results` call, but remains its own importable function for testing:

```python
BASE_RESPONSE_MINUTES = 10.0

def estimate_response_time(zone: ZoneParams) -> float:
    """
    Deterministic formula using only road accessibility, resource availability,
    and emergency demand. No external APIs.

    road_factor     = 1 + 2 × (1 - road_accessibility)   → range [1, 3]
    resource_ratio  = clamp((rescue_teams + ambulances) / demand_units, 0, 1)
    resource_factor = 1 + (1 - resource_ratio)            → range [1, 2]
    demand_factor   = 1 + medical_urgency                 → range [1, 2]

    response_time = BASE × road_factor × resource_factor × demand_factor
    Clamped to [5, 120] minutes.

    Monotonicity guarantees:
    - Lower road_accessibility → higher road_factor → longer time  ✓
    - Fewer resources → lower resource_ratio → higher resource_factor → longer time  ✓
    - Higher medical_urgency → higher demand_factor → longer time  ✓
    """
    road_factor = 1.0 + 2.0 * (1.0 - zone.road_accessibility)
    resource_ratio = min((zone.rescue_teams + zone.ambulances) / zone.demand_units, 1.0)
    resource_factor = 1.0 + (1.0 - resource_ratio)
    demand_factor = 1.0 + zone.medical_urgency
    raw = BASE_RESPONSE_MINUTES * road_factor * resource_factor * demand_factor
    return round(min(max(raw, 5.0), 120.0), 2)
```

### bottleneck_detector.py

Evaluates four constraint types and ranks by severity score:

| Constraint | Formula | Label template |
|---|---|---|
| Resource shortage | 1 - (resources / demand) per zone | "Resource shortage in {zone}" |
| Shelter capacity | 1 - (capacity / occupancy) where occupancy > capacity | "Shelter overcapacity in {shelter}" |
| Hospital capacity | 1 - (capacity / demand) | "Hospital capacity critical at {hospital}" |
| Road access | 1 - road_accessibility for highest-risk zones | "Road access blocked in {zone}" |

Primary bottleneck = item with highest severity score.

### intervention_engine.py

Generates modified `ZoneParams` for each of the four strategies:

- **Baseline**: returns params unchanged.
- **Resource Reallocation**: sorts zones by risk score. Takes up to 2 resources (rescue teams or ambulances) from the lowest-risk zone that has surplus (> 1 unit) and adds them to the highest-risk zone.
- **Capacity Expansion**: increases shelter capacity by 20% and hospital surge capacity by 15% for the most constrained facilities.
- **Combined**: applies both resource reallocation and capacity expansion.

All moves are bounded — no zone is reduced below 1 rescue team and 1 ambulance.

### recommender.py

```python
RECOMMENDATION_WEIGHTS = {
    'risk_reduction_pct':                  0.40,
    'bottleneck_resolution_score':         0.30,
    'resource_efficiency':                 0.20,  # inverse of resource_cost
    'response_time_improvement_minutes':   0.10,
}

def rank_and_recommend(interventions: List[InterventionResult]) -> str:
    """
    Normalizes each metric across all strategies to [0, 1],
    applies weights, sums composite score.
    Returns strategy name with highest composite score.
    Ties broken by risk_reduction_pct.
    """
```

---

## 5. Data Models (JSON Examples)

### Scenario (stored in DynamoDB)

```json
{
  "scenario_id": "flood-scenario-001",
  "name": "River Delta Flood — Category 3",
  "description": "Severe flooding across 5 urban zones following dam overflow.",
  "severity": "high",
  "created_at": "2026-09-10T00:00:00Z",
  "zones": [
    {
      "zone_id": "zone-1",
      "name": "Zone 1 — North Bank",
      "coordinates": [[51.505, -0.09], [51.51, -0.09], [51.51, -0.08], [51.505, -0.08]],
      "centroid": [51.5075, -0.085],
      "flood_severity": 0.8,
      "affected_population": 12000,
      "medical_urgency": 0.7,
      "road_accessibility": 0.3,
      "rescue_teams": 2,
      "ambulances": 3,
      "demand_units": 8
    }
  ],
  "shelters": [
    {
      "shelter_id": "shelter-1",
      "name": "Community Center Alpha",
      "coordinates": [51.508, -0.087],
      "capacity": 500,
      "current_occupancy": 420
    }
  ],
  "hospitals": [
    {
      "hospital_id": "hospital-1",
      "name": "North General Hospital",
      "coordinates": [51.512, -0.082],
      "capacity": 200,
      "surge_capacity": 50,
      "current_occupancy": 185
    }
  ]
}
```

### SimulationResult (stored in DynamoDB)

```json
{
  "result_id": "result-abc123",
  "scenario_id": "flood-scenario-001",
  "run_at": "2026-09-10T13:45:00Z",
  "params_used": [
    {
      "zone_id": "zone-1",
      "flood_severity": 0.9,
      "affected_population": 12000,
      "medical_urgency": 0.7,
      "road_accessibility": 0.3,
      "rescue_teams": 2,
      "ambulances": 3,
      "demand_units": 8
    }
  ],
  "baseline_zone_results": [
    {
      "zone_id": "zone-1",
      "risk_score": 72.5,
      "risk_level": "high",
      "response_time_minutes": 38.4,
      "risk_components": {
        "affected_population_score": 0.30,
        "flood_severity_score": 0.225,
        "medical_urgency_score": 0.175,
        "road_accessibility_score": 0.105,
        "resource_shortage_score": 0.089
      }
    }
  ],
  "bottlenecks": [
    {
      "type": "resource_shortage",
      "zone_id": "zone-1",
      "description": "Resource shortage in Zone 1 — North Bank",
      "severity_score": 0.83
    }
  ],
  "interventions": [
    {
      "strategy": "baseline",
      "label": "Baseline / No Intervention",
      "avg_risk_score": 72.5,
      "avg_response_time_minutes": 38.4,
      "risk_reduction_pct": 0.0,
      "response_time_improvement_minutes": 0.0,
      "bottleneck_resolution_score": 0.0,
      "resource_cost": 0,
      "composite_score": 0.0
    },
    {
      "strategy": "combined",
      "label": "Combined Intervention",
      "avg_risk_score": 54.1,
      "avg_response_time_minutes": 24.2,
      "risk_reduction_pct": 25.4,
      "response_time_improvement_minutes": 14.2,
      "bottleneck_resolution_score": 0.71,
      "resource_cost": 3,
      "composite_score": 0.81
    }
  ],
  "recommended_strategy": "combined"
}
```

---

## 6. DynamoDB Design

Two tables. Simple, flat design — no nested document queries needed.

### Table 1: `crisissim-scenarios`

| Attribute | Type | Role |
|---|---|---|
| `scenario_id` (PK) | String | Partition key |

Stores the full scenario JSON (zones, shelters, hospitals, default params).
One item per scenario. MVP has one scenario.

### Table 2: `crisissim-results`

| Attribute | Type | Role |
|---|---|---|
| `scenario_id` (PK) | String | Partition key |
| `run_at` (SK) | String (ISO 8601) | Sort key — enables getting latest result |

Stores full simulation results including all intervention evaluations.

**Access Patterns:**
- Load scenario: `GetItem` on `crisissim-scenarios` by `scenario_id`
- Save result: `PutItem` on `crisissim-results`
- Get latest result: `Query` on `crisissim-results` where PK = `scenario_id`, `ScanIndexForward=False`, `Limit=1`
- List scenarios: `Scan` on `crisissim-scenarios` (one item in MVP, acceptable)

No GSIs needed for MVP. No separate tables for zones, resources, or interventions — all embedded in the scenario/result documents.

---

## 7. REST API Design

Base path: `/api/v1`

### GET /scenarios

Returns list of available scenarios (name, description, severity).

**Response:**
```json
{
  "scenarios": [
    {
      "scenario_id": "flood-scenario-001",
      "name": "River Delta Flood — Category 3",
      "description": "Severe flooding across 5 urban zones.",
      "severity": "high"
    }
  ]
}
```

---

### GET /scenarios/{scenario_id}

Returns full scenario data including zones, shelters, hospitals, and default params.

**Response:** Full `Scenario` object (see data model above).

---

### POST /simulate

Runs the simulation with the provided What-If parameters. Persists result.

**Request body:**
```json
{
  "scenario_id": "flood-scenario-001",
  "params": [
    {
      "zone_id": "zone-1",
      "flood_severity": 0.9,
      "affected_population": 12000,
      "medical_urgency": 0.7,
      "road_accessibility": 0.3,
      "rescue_teams": 4,
      "ambulances": 3,
      "demand_units": 8
    }
  ]
}
```

**Response:** Full `SimulationResult` object.

---

### GET /results/{scenario_id}/latest

Returns the most recent simulation result for a scenario.

**Response:** Full `SimulationResult` object, or `404` if no result exists yet.

---

### POST /explain

Calls Amazon Bedrock to generate a plain-language explanation of the recommended intervention.

**Request body:**
```json
{
  "result_id": "result-abc123"
}
```

**Response:**
```json
{
  "explanation": "The simulation identified a critical resource shortage in Zone 1...",
  "strategy_explained": "combined",
  "generated_at": "2026-09-10T13:46:00Z"
}
```

**Error / fallback:**
```json
{
  "explanation": "AI explanation is temporarily unavailable. The recommended strategy is Combined Intervention, which reduces average risk by 25.4% and improves response time by 14.2 minutes.",
  "fallback": true
}
```

---

## 8. Amazon Bedrock Integration

### Model
Claude 3 Sonnet (via `bedrock-runtime` `invoke_model`).

### Prompt Structure

```python
def build_explanation_prompt(result: SimulationResult) -> str:
    recommended = next(i for i in result.interventions 
                       if i.strategy == result.recommended_strategy)
    primary_bottleneck = result.bottlenecks[0]
    
    return f"""You are an emergency management analyst. 
You are given structured simulation data from a flood emergency decision-support system.
Your task is to explain the recommendation in plain language for an emergency coordinator.

DO NOT invent numbers. Use ONLY the data provided below.
DO NOT suggest actions beyond what the simulation recommends.

SIMULATION DATA:
- Primary bottleneck: {primary_bottleneck.description} (severity: {primary_bottleneck.severity_score:.2f})
- Recommended strategy: {recommended.label}
- Risk reduction: {recommended.risk_reduction_pct:.1f}%
- Response time improvement: {recommended.response_time_improvement_minutes:.1f} minutes
- Bottleneck resolution score: {recommended.bottleneck_resolution_score:.2f}
- Resource cost: {recommended.resource_cost} units
- All strategies evaluated: {[i.label + ' (composite: ' + str(i.composite_score) + ')' for i in result.interventions]}

Write 2–4 paragraphs explaining:
1. What the primary bottleneck is and why it matters.
2. Why the recommended strategy addresses this bottleneck better than the alternatives.
3. What improvements the coordinator can expect if this strategy is applied.

Use plain, non-technical language suitable for a non-expert emergency coordinator."""
```

### Fallback Behavior

If Bedrock is unavailable (timeout, service error, or missing credentials in local dev):
- Return an auto-generated template explanation built from the structured data.
- Log the failure to CloudWatch.
- Return `"fallback": true` in the response so the frontend can display a subtle indicator.

---

## 9. Local Development Strategy

### Phase 1 — Engine Only (no HTTP, no AWS)

```bash
cd backend
pip install -r requirements-dev.txt
pytest engine/tests/          # run all property-based and unit tests
python -c "from engine import run_demo; run_demo()"
```

The simulation engine runs entirely in memory. `seed_data.py` provides a hardcoded scenario dict for local testing.

### Phase 2 — Local Full Stack

```bash
# Terminal 1 — backend
cd backend
uvicorn local_server:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev     # Vite dev server on port 5173
```

`local_server.py` is a FastAPI app that wires the same handler logic to HTTP routes. It uses an in-memory dict as the "database" instead of DynamoDB. The frontend points `VITE_API_BASE_URL=http://localhost:8000/api/v1`.

### Phase 3 — AWS Deployment

1. Deploy DynamoDB tables (via AWS Console or CLI).
2. Run `python seed_data.py --target dynamodb` to seed the scenario.
3. Package each Lambda handler with dependencies using a deployment script or SAM.
4. Deploy API Gateway + Lambda.
5. Deploy frontend to Amplify, set `VITE_API_BASE_URL` to the API Gateway URL.

No infrastructure-as-code framework required for MVP — manual AWS Console setup is acceptable for a student project.

---

## 10. Testing Strategy

### Backend — Python

**Tool:** `pytest` + `hypothesis` (property-based testing)

```
backend/engine/tests/
  test_risk_scorer.py         # unit + property-based tests
  test_response_time.py       # unit + property-based tests
  test_bottleneck_detector.py # unit tests
  test_evaluator.py           # unit tests
  test_recommender.py         # unit tests

backend/handlers/tests/
  test_run_simulation.py      # integration test: handler → engine → mock DB
  test_get_explanation.py     # integration test: handler → mock Bedrock
```

**Property-based tests (hypothesis):**

```python
# P-1: Risk score always in [0, 100]
@given(zone_params_strategy())
def test_risk_score_bounds(zone):
    result = calculate_risk_score(zone, population_max=100000)
    assert 0 <= result.risk_score <= 100

# P-2: Increasing flood severity never decreases risk score
@given(zone_params_strategy(), floats(0, 1))
def test_risk_score_monotone_flood_severity(zone, higher_severity):
    assume(higher_severity >= zone.flood_severity)
    zone_high = zone._replace(flood_severity=higher_severity)
    r1 = calculate_risk_score(zone, 100000)
    r2 = calculate_risk_score(zone_high, 100000)
    assert r2.risk_score >= r1.risk_score

# P-4: More resources never increases response time
@given(zone_params_strategy(), integers(0, 10))
def test_response_time_monotone_resources(zone, extra_resources):
    zone_more = zone._replace(rescue_teams=zone.rescue_teams + extra_resources)
    t1 = estimate_response_time(zone)
    t2 = estimate_response_time(zone_more)
    assert t2 <= t1

# P-7: Determinism
@given(zone_params_strategy())
def test_simulation_determinism(zone):
    r1 = calculate_risk_score(zone, 100000)
    r2 = calculate_risk_score(zone, 100000)
    assert r1.risk_score == r2.risk_score
```

### Frontend — TypeScript

**Tool:** Vitest + React Testing Library

```
frontend/src/
  components/__tests__/
    MetricsSummary.test.tsx
    ComparisonTable.test.tsx
    BeforeAfterToggle.test.tsx
  services/__tests__/
    simulation.test.ts         # API service mock tests
```

Tests focus on: correct rendering of risk levels and colors, metric display accuracy, component state transitions (before/after toggle, loading/error states).

---

## 11. Folder Structure

```
crisissim/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── MetricsSummary.tsx
│   │   │   │   ├── RiskRankingList.tsx
│   │   │   │   └── BottleneckAlert.tsx
│   │   │   ├── map/
│   │   │   │   ├── SimMap.tsx
│   │   │   │   ├── ZoneLayer.tsx
│   │   │   │   ├── ResourceMarkers.tsx
│   │   │   │   ├── FacilityMarkers.tsx
│   │   │   │   └── ZoneDetailPanel.tsx
│   │   │   ├── simulator/
│   │   │   │   ├── WhatIfPanel.tsx
│   │   │   │   └── ZoneParameterRow.tsx
│   │   │   ├── results/
│   │   │   │   ├── ComparisonTable.tsx
│   │   │   │   ├── BeforeAfterToggle.tsx
│   │   │   │   └── AIExplanation.tsx
│   │   │   └── common/
│   │   │       ├── SeverityBadge.tsx
│   │   │       ├── LoadingSpinner.tsx
│   │   │       └── ErrorBanner.tsx
│   │   ├── context/
│   │   │   ├── ScenarioContext.tsx
│   │   │   └── SimulationContext.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── scenarios.ts
│   │   │   ├── simulation.ts
│   │   │   └── explanation.ts
│   │   ├── types/
│   │   │   └── index.ts          # all TypeScript interfaces
│   │   ├── pages/
│   │   │   ├── ScenarioSelectPage.tsx
│   │   │   └── DashboardPage.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── risk_scorer.py
│   │   ├── response_time.py
│   │   ├── bottleneck_detector.py
│   │   ├── intervention_engine.py
│   │   ├── evaluator.py
│   │   ├── recommender.py
│   │   └── tests/
│   │       ├── test_risk_scorer.py
│   │       ├── test_response_time.py
│   │       ├── test_bottleneck_detector.py
│   │       ├── test_evaluator.py
│   │       └── test_recommender.py
│   ├── handlers/
│   │   ├── get_scenarios.py
│   │   ├── get_scenario.py
│   │   ├── run_simulation.py
│   │   ├── get_result.py
│   │   └── get_explanation.py
│   ├── persistence/
│   │   └── dynamodb.py
│   ├── bedrock/
│   │   └── explainer.py
│   ├── local_server.py
│   ├── seed_data.py
│   ├── requirements.txt          # production deps
│   └── requirements-dev.txt      # + pytest, hypothesis, httpx, fastapi, uvicorn
│
└── README.md
```

---

## 12. Implementation Order

Build in this exact sequence to keep each phase runnable and testable independently:

**Phase 1 — Simulation Engine (local, no AWS, no HTTP)**
1. Define `engine/models.py` (all dataclasses)
2. Implement `engine/risk_scorer.py` + tests
3. Implement `engine/response_time.py` + tests
4. Implement `engine/bottleneck_detector.py` + tests
5. Implement `engine/intervention_engine.py` + tests
6. Implement `engine/evaluator.py` + tests
7. Implement `engine/recommender.py` + tests
8. Write `seed_data.py` with hardcoded scenario
9. Verify: `pytest engine/` passes all tests including property-based

**Phase 2 — Local Backend API**
10. Implement `local_server.py` (FastAPI) wiring all handlers to routes
11. Implement handler logic (thin wrappers over engine)
12. Test all endpoints with curl or httpx
13. Implement `bedrock/explainer.py` with fallback for local dev
14. Verify: full simulation run + explanation via HTTP locally

**Phase 3 — Frontend**
15. Scaffold Vite + React + TypeScript project
16. Define `types/index.ts`
17. Implement API service layer (`services/`)
18. Implement ScenarioContext + SimulationContext
19. Build `ScenarioSelectPage`
20. Build `DashboardPage` layout shell
21. Build `SimMap` with zone polygons (hardcoded test data first)
22. Build `MetricsSummary`, `RiskRankingList`, `BottleneckAlert`
23. Build `WhatIfPanel` with parameter controls
24. Build `ComparisonTable`
25. Build `BeforeAfterToggle`
26. Build `AIExplanation`
27. Wire all components to contexts (real API calls)
28. Verify: full user flow works end-to-end locally

**Phase 4 — AWS Deployment**
29. Create DynamoDB tables in AWS Console
30. Run `seed_data.py --target dynamodb`
31. Package and deploy Lambda functions
32. Create API Gateway and connect routes to Lambdas
33. Configure CORS on API Gateway
34. Deploy frontend to AWS Amplify
35. Set `VITE_API_BASE_URL` in Amplify environment
36. Verify: full flow works on deployed stack

---

## Dependencies

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "axios": "^1.7.7"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@types/leaflet": "^1.9.12",
    "typescript": "^5.5.3",
    "vite": "^5.4.2",
    "@vitejs/plugin-react": "^4.3.1",
    "vitest": "^2.0.5",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.5.0"
  }
}
```

### Backend (`requirements.txt`)
```
boto3==1.35.0
```

### Backend (`requirements-dev.txt`)
```
boto3==1.35.0
fastapi==0.112.2
uvicorn==0.30.6
httpx==0.27.2
pytest==8.3.2
hypothesis==6.112.1
```

The production Lambda dependency is only `boto3` (pre-installed on Lambda runtimes). The engine itself has zero third-party dependencies.

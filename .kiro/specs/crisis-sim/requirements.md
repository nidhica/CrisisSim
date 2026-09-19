# CrisisSim Requirements

## Overview

CrisisSim is an AI-powered emergency simulation and decision-support platform for disaster preparedness and emergency operations. The initial version focuses on flood emergencies. It is a simulation and decision-support prototype — not a real emergency control system — that helps users model evolving flood scenarios, identify bottlenecks, test interventions, and compare strategies.

---

## User Stories

### 1. Scenario Management

**US-1.1** As a user, I want to open a pre-loaded flood emergency scenario so that I can immediately see a realistic emergency situation without manual setup.

Acceptance Criteria:
- The system provides at least one default flood scenario with zones, resources, shelters, and hospitals pre-populated.
- The scenario loads within 3 seconds.
- The scenario includes metadata: name, description, severity level, and timestamp.

**US-1.2** As a user, I want to see a list of available scenarios so that I can choose which one to simulate.

Acceptance Criteria:
- The scenario list shows name, severity, and a brief description.
- Selecting a scenario navigates to the simulation dashboard.

---

### 2. Emergency Dashboard

**US-2.1** As a user, I want to see a dashboard overview of the flood emergency so that I can quickly assess the current situation.

Acceptance Criteria:
- The dashboard displays: affected zones count, total population at risk, available resources (rescue teams, ambulances), shelter capacity vs. occupancy, hospital capacity vs. occupancy, and estimated response time per zone.
- Data refreshes when a simulation run completes.
- The dashboard is responsive and usable on desktop screens.

**US-2.2** As a user, I want to see an interactive map showing affected zones, resources, shelters, and hospitals so that I can understand the geographic distribution of the emergency.

Acceptance Criteria:
- The map renders all zones with color-coded risk levels: Low (green), Medium (yellow), High (orange), Critical (red).
- Resource locations (rescue teams, ambulances) are displayed as icons.
- Shelter and hospital locations are marked and distinguishable.
- Clicking a zone opens a detail panel showing: risk score, flood severity, affected population, medical urgency, road accessibility, resource coverage, and estimated response time.
- The map is pannable and zoomable.

---

### 3. Zone Risk Scoring

**US-3.1** As a user, I want each zone to have a dynamically calculated risk score so that I can prioritize response efforts.

Acceptance Criteria:
- Risk score is calculated deterministically using a weighted algorithm — no LLM involvement.
- Inputs and weights:
  - Affected population: 25%
  - Flood severity: 25%
  - Medical urgency: 25%
  - Road accessibility risk: 15%
  - Resource shortage (inverse of resource coverage): 10%
- Each input is normalized to a [0, 1] scale before weighting.
- Final risk score is a value in [0, 100] mapped to severity levels:
  - Low: 0–25
  - Medium: 26–50
  - High: 51–75
  - Critical: 76–100
- Risk scores are recalculated only after the user explicitly triggers "Run Simulation".
- Population density, infrastructure vulnerability, and proximity to critical assets are not used in MVP risk scoring.

**US-3.2** As a user, I want to see which zone has the highest risk so that I can focus attention there first.

Acceptance Criteria:
- The highest-risk zone is highlighted on the map and called out in the dashboard.
- A sortable risk ranking list is shown on the dashboard.

---

### 4. Estimated Response Time

**US-4.1** As a user, I want to see an estimated response time for each zone so that I can understand how quickly help can arrive.

Acceptance Criteria:
- Response time is calculated deterministically using:
  - Road accessibility (lower accessibility = longer time)
  - Resource availability (fewer resources = longer time)
  - Emergency demand (higher demand = longer time)
- Response time is expressed in minutes and shown per zone.
- Response time is displayed on: the dashboard summary, zone detail panel, simulation results, strategy comparison table, and before vs. after visualization.
- Response time updates after each "Run Simulation" execution.

---

### 5. Bottleneck Detection

**US-5.1** As a user, I want the system to automatically identify the primary bottleneck in the emergency response so that I understand where the system is most constrained.

Acceptance Criteria:
- Bottleneck detection is algorithm-based — no LLM involvement.
- The system evaluates: resource-to-demand ratios per zone, shelter capacity gaps, hospital capacity gaps, road accessibility scores.
- The primary bottleneck is displayed prominently on the dashboard with a label describing what is constrained (e.g., "Rescue team shortage in Zone 3").
- If multiple bottlenecks exist, they are ranked by severity.

---

### 6. What-If Scenario Simulator

**US-6.1** As a user, I want to modify simulation parameters to model different conditions so that I can explore how changes affect the emergency situation.

Acceptance Criteria:
- Adjustable parameters include: flood water level (per zone or global), number of rescue teams deployed per zone, number of ambulances deployed per zone, shelter capacity adjustments, hospital surge capacity.
- Parameter changes update a local draft state only — they do not modify the active simulation results until "Run Simulation" is clicked.
- The UI provides sliders or input controls for each parameter with defined min/max bounds.
- A "Run Simulation" button triggers recalculation of risk scores, response times, bottlenecks, and intervention options, and persists the results.

**US-6.2** As a user, I want to reset the simulation to its original state so that I can start a fresh analysis.

Acceptance Criteria:
- A "Reset" button restores all parameters to the scenario's default values.
- The map and dashboard reflect the reset state immediately, without requiring a new simulation run.
- The original scenario state is never mutated by What-If adjustments.

---

### 7. Intervention Strategies

**US-7.1** As a user, I want the system to evaluate a defined set of intervention strategies so that I can compare structured response options.

Acceptance Criteria:
- The system evaluates exactly the following four strategies:
  1. **Baseline / No Intervention** — current state, no changes applied.
  2. **Resource Reallocation** — moves available ambulances and/or rescue teams from lower-risk zones to higher-risk zones.
  3. **Capacity Expansion** — increases shelter capacity and/or hospital surge capacity in constrained zones.
  4. **Combined Intervention** — applies both resource reallocation and capacity expansion.
- Each strategy is evaluated deterministically by the simulation engine.
- Each strategy produces: projected risk scores per zone, projected response times per zone, projected bottleneck severity, resource cost (units consumed or reallocated).

**US-7.2** As a user, I want to compare the four intervention strategies side by side so that I can understand the trade-offs.

Acceptance Criteria:
- A comparison view shows all four strategies in a table or card layout.
- Metrics shown per strategy: projected overall risk reduction (%), projected average response time improvement (minutes), projected bottleneck resolution score, resource cost.
- Strategies are sortable by each metric.
- The recommended strategy is visually highlighted.

---

### 8. Best Intervention Recommendation

**US-8.1** As a user, I want the system to recommend the best intervention strategy so that I have a clear starting point for decision-making.

Acceptance Criteria:
- The recommendation is selected algorithmically using a weighted composite score — no LLM involvement.
- Scoring weights:
  - Risk reduction: 40%
  - Bottleneck resolution: 30%
  - Resource efficiency: 20%
  - Response time improvement: 10%
- The recommended strategy is highlighted in the comparison view with a "Recommended" badge.
- The composite score for each strategy is shown transparently.

---

### 9. Before vs. After Visualization

**US-9.1** As a user, I want to see a before vs. after comparison of applying the recommended intervention so that I can visualize its projected impact.

Acceptance Criteria:
- A toggle or side-by-side view shows the current (baseline) state vs. the projected state after applying the recommended intervention.
- The map reflects zone risk color changes between the two states.
- The following metrics are shown for both states: overall risk score, average response time, bottleneck severity, shelter capacity utilization, hospital capacity utilization.

---

### 10. AI Explanation (Amazon Bedrock)

**US-10.1** As a user, I want the system to explain in plain language why the recommended intervention was selected so that I can understand the reasoning without reading raw numbers.

Acceptance Criteria:
- Amazon Bedrock generates the explanation using structured simulation results as input.
- The explanation covers:
  - What the primary bottleneck is and why it matters.
  - Why the recommended intervention addresses this bottleneck.
  - The projected improvements in key metrics (risk reduction, response time, capacity).
- The explanation is 2–4 paragraphs in plain, non-technical English.
- Bedrock is never called to perform numerical calculations, risk scoring, bottleneck detection, intervention ranking, or any decision-making logic.
- The Bedrock call always receives the full structured simulation result as grounding context.
- Natural-language Q&A chat is out of scope for MVP.

---

### 11. Architecture & Non-Functional Requirements

**US-11.1** The simulation engine must be deterministic.

Acceptance Criteria:
- Given identical inputs, the engine always produces identical outputs.
- No randomness, external API calls, or LLM calls are used in risk scoring, response time estimation, bottleneck detection, or intervention ranking.

**US-11.2** The backend must be AWS Lambda-compatible.

Acceptance Criteria:
- All backend logic is stateless and deployable as individual Lambda functions.
- Each Lambda function targets completion within 30 seconds for API-facing calls.

**US-11.3** The frontend must be deployable via AWS Amplify.

Acceptance Criteria:
- The React/TypeScript frontend builds to a static bundle deployable on Amplify.
- API endpoint URLs are configurable via Amplify environment variables.

**US-11.4** Simulation data must persist in DynamoDB.

Acceptance Criteria:
- Scenarios, simulation states, and intervention results are stored in and retrievable from DynamoDB.
- Data access patterns are optimized with appropriate partition key / sort key design.

**US-11.5** The system must handle errors gracefully.

Acceptance Criteria:
- API errors return structured JSON responses with HTTP status codes and messages.
- The frontend displays user-friendly error states — no raw stack traces exposed.
- Lambda functions log all errors to CloudWatch.

---

## Correctness Properties

These properties must hold at all times and will be validated via property-based tests:

**P-1: Risk Score Bounds**
For any zone with any valid input parameters, the calculated risk score must always be in the range [0, 100].

**P-2: Risk Score Monotonicity**
Increasing flood severity in a zone must never decrease its risk score, all else being equal.

**P-3: Risk Score Weight Integrity**
The sum of all input weights used in the risk scoring formula must always equal 1.0 (affected population 0.25 + flood severity 0.25 + medical urgency 0.25 + road accessibility 0.15 + resource shortage 0.10 = 1.0).

**P-4: Response Time Monotonicity**
Increasing resource availability in a zone must never increase the estimated response time for that zone, all else being equal.

**P-5: Bottleneck Consistency**
The identified primary bottleneck must always correspond to the zone or resource with the worst constraint ratio among all evaluated metrics.

**P-6: Intervention Dominance**
The recommended intervention must always have a composite score ≥ all other candidate interventions under the defined weighting model.

**P-7: Simulation Determinism**
Given identical scenario state and parameters, the simulation engine must always return identical risk scores, response times, bottleneck identification, and intervention rankings.

**P-8: Before/After Accuracy**
The projected "after" state for intervention I must equal the result of running the simulation engine with the parameter changes specified by I applied to the current baseline state.

**P-9: AI Explanation Grounding**
The Bedrock explanation call must always receive the full structured simulation result as context and must never be called with empty or partial simulation data.

---

## MVP Scope

In scope for the initial MVP:

- Single pre-loaded flood scenario
- Emergency dashboard with key metrics including estimated response time
- Interactive map with color-coded zone risk visualization
- Deterministic zone risk scoring engine (5-factor weighted model)
- Deterministic estimated response time calculation per zone
- Bottleneck detection algorithm
- What-If parameter adjustment with explicit "Run Simulation" trigger
- Four defined intervention strategies: Baseline, Resource Reallocation, Capacity Expansion, Combined
- Intervention comparison view (side-by-side metrics)
- Best intervention recommendation (weighted composite scoring)
- Before vs. after visualization (toggle view with response time included)
- AI explanation of recommended intervention via Amazon Bedrock
- REST API via API Gateway + Lambda
- DynamoDB persistence
- React/TypeScript frontend deployed on AWS Amplify

## Out of Scope for MVP (Future Features)

- Natural-language Q&A chat (Bedrock conversational interface)
- User-created custom scenarios
- Real-time data ingestion (weather APIs, sensor feeds)
- EventBridge event-driven simulation updates
- S3 report generation / PDF export
- AWS Cognito / authentication and role-based access control
- Multi-user collaboration
- Multi-hazard support (beyond floods)
- Mobile-optimized map interactions
- Historical simulation playback
- Multiple disaster type templates

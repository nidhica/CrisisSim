# CrisisSim

## AI-Assisted Multi-Hazard Emergency Simulation & Decision Support Platform

CrisisSim is an AI-assisted emergency simulation and decision-support platform designed to help authorities explore emergency response strategies before acting on them.

It connects citizen-reported incidents with an authority command center and a deterministic multi-hazard simulation engine. Authorities can assess incidents, simulate response strategies, compare interventions, and understand potential bottlenecks.

CrisisSim currently supports:

- Flood
- Fire
- Earthquake
- Cyclone / Severe Storm
- Industrial Accident

> **Important:** CrisisSim is a simulation and decision-support prototype. It is not a live emergency control system and does not provide real-time disaster intelligence, verified emergency boundaries, or operational instructions.

---

# 1. Problem

During emergencies, responders may need to make decisions while dealing with:

- Limited emergency resources
- Multiple affected zones
- Different levels of risk
- Road accessibility constraints
- Medical urgency
- Specialist resource requirements
- Response-time bottlenecks
- Uncertainty about the consequences of different interventions

A simple dashboard showing incident information is not enough.

CrisisSim explores a different approach:

> **What happens if we simulate the response before committing resources?**

The platform allows an authority to move from an incident report to a simulated response strategy and compare the projected outcome against a baseline.

---

# 2. What CrisisSim Does

CrisisSim provides an end-to-end prototype workflow:

```text
Citizen
   |
   v
Report Crisis
   |
   v
Authority Command Center
   |
   v
Acknowledge / Assess
   |
   v
Simulate Response
   |
   v
Multi-Hazard Simulation Engine
   |
   +----------------------+
   |                      |
   v                      v
Risk Analysis       Bottleneck Detection
   |                      |
   +----------+-----------+
              |
              v
       Intervention Engine
              |
              v
       Response Recommendation
              |
              v
      Command Dashboard
````

The system combines:

* Citizen crisis reporting
* Authority incident management
* Location-aware simulation
* Multi-hazard risk scoring
* Resource allocation analysis
* Bottleneck detection
* What-If intervention analysis
* Projected impact comparison
* Optional AI-generated explanations
* Deterministic fallback explanations

---

# 3. Supported Hazards

## Flood

Factors include:

* Affected population
* Flood severity
* Medical urgency
* Road accessibility
* Resource shortage

Specialist resources:

* Rescue teams
* Ambulances

---

## Fire

Factors include:

* Fire intensity
* Smoke exposure
* Spread potential

Specialist resources:

* Fire crews

---

## Earthquake

Factors include:

* Structural damage
* Trapped-person likelihood
* Aftershock risk

Specialist resources:

* Search and rescue teams

---

## Cyclone / Severe Storm

Factors include:

* Wind severity
* Storm-surge exposure
* Power-outage severity

Specialist resources:

* Evacuation teams
* Utility crews

---

## Industrial Accident

Factors include:

* Toxic-release severity
* Exposure level
* Containment failure

Specialist resources:

* Hazmat teams
* Containment units

---

# 4. Location-Aware Simulation

CrisisSim accepts a real-world location entered by the user.

For example:

```text
Bengaluru, Karnataka
Mumbai, Maharashtra
Bhopal, Madhya Pradesh
Chennai, Tamil Nadu
Delhi, India
```

The application uses geocoding to identify the selected location and centers the map on that geography.

The simulation then generates deterministic simulated emergency zones and facilities around that location.

```text
Real Location
      |
      v
Geocoding
      |
      v
Map Center
      |
      v
Deterministic Simulated Zones
      |
      v
Risk & Response Simulation
```

> The geography is real, but the emergency conditions, affected zones, facilities, and response conditions are simulated. CrisisSim does not claim that these represent actual current emergency conditions.

---

# 5. Citizen Reporting

Citizens can submit a crisis report containing:

* Hazard type
* Location
* Latitude / longitude
* Severity
* Description
* Optional evidence

Example:

```text
Hazard: Fire
Location: Bengaluru, Karnataka
Severity: High
Description: Smoke and fire reported near a commercial area.
```

Each report receives an incident ID such as:

```text
INC-2026-0001
```

Incident status follows a controlled workflow:

```text
reported
    |
    v
acknowledged
    |
    v
assessing
    |
    v
response_dispatched
    |
    v
resolved
```

Invalid status transitions are rejected by the backend.

---

# 6. Authority Command Center

Emergency personnel can view submitted incidents through the authority command center.

For each incident, the authority can:

* View hazard information
* View location
* View severity
* View description
* View the incident on a map
* Update incident status
* Start a response simulation

The incident can then be converted into a simulation scenario while preserving:

* Hazard type
* Location
* Severity
* Source incident ID

This provides traceability between the original citizen report and the simulated response.

---

# 7. Simulation Engine

The simulation engine is implemented as a pure Python module.

The main stages are:

```text
Simulation State
      |
      v
Risk Scoring
      |
      v
Response Time Estimation
      |
      v
Bottleneck Detection
      |
      v
Intervention Engine
      |
      v
Evaluation
      |
      v
Recommendation
```

Major engine components include:

```text
backend/engine/

models.py
hazards.py
risk_scorer.py
response_time.py
bottleneck_detector.py
intervention_engine.py
evaluator.py
recommender.py
```

The engine is designed to be deterministic so that the same simulation inputs produce reproducible results.

---

# 8. What-If Analysis

CrisisSim allows authorities to compare different intervention strategies.

Current intervention types include:

* Baseline
* Resource Reallocation
* Capacity Expansion
* Combined Intervention

The system compares the baseline scenario with the selected intervention and displays projected changes in existing simulation metrics.

Example:

```text
BASELINE
   |
   | Risk / Response / Bottleneck
   |
   v
INTERVENTION
   |
   | Risk / Response / Bottleneck
   |
   v
PROJECTED IMPACT
```

The system does not claim that these projections represent real-world emergency outcomes.

---

# 9. Command Brief

After a simulation, CrisisSim generates a concise command brief using existing simulation results.

The brief can surface:

* Hazard
* Overall risk
* Highest-risk zone
* Primary bottleneck
* Estimated response time
* Recommended intervention
* Reason for the recommendation

This gives the authority a quick summary before inspecting the detailed simulation results.

---

# 10. Risk Visualization

The map visualizes simulated zones using risk levels:

```text
CRITICAL  → High Risk
HIGH      → Elevated Risk
MEDIUM    → Medium Risk
LOW       → Lower Risk
```

The dashboard also displays simulated assets such as:

* Emergency facilities
* Resources
* Simulated zones
* Citizen incident locations

The map includes a legend and explicit prototype disclaimers.

---

# 11. AI Explanation Layer

CrisisSim includes an optional AI explanation layer using Amazon Bedrock.

Bedrock is used for:

> **Natural-language explanation of existing simulation results.**

The AI layer does not calculate the simulation or determine the underlying risk scores.

The architecture is:

```text
Simulation Engine
      |
      v
Structured Simulation Result
      |
      v
Bedrock Explanation Layer
      |
      v
Natural-Language Explanation
```

If Bedrock is unavailable or unauthorized, CrisisSim uses a deterministic fallback explanation.

This ensures that the core application remains functional without depending on AI model availability.

> Bedrock is an explanation layer, not the simulation engine.

---

# 12. AWS Architecture

CrisisSim is deployed as a serverless AWS application.

```text
                    +----------------+
                    |  AWS Amplify   |
                    |    Frontend    |
                    +-------+--------+
                            |
                            v
                    +---------------+
                    | API Gateway   |
                    | REST API      |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | AWS Lambda    |
                    | Python Backend |
                    +-------+-------+
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
        +-----------+ +-----------+ +-------------+
        | DynamoDB  | | DynamoDB  | |  Bedrock    |
        | Scenarios | | Incidents | | Explanation |
        +-----------+ +-----------+ +-------------+
              |
              v
        +-----------+
        | DynamoDB  |
        | Results   |
        +-----------+

                    CloudWatch
                        |
                        v
                 Lambda Monitoring
```

---

# 13. AWS Services Used

## AWS Amplify

Used to host and deploy the React frontend.

The live application is deployed through an Amplify application and `main` branch.

---

## Amazon API Gateway

Provides the REST API entry point between the frontend and the serverless backend.

Example API routes include:

```text
GET    /api/v1/health

GET    /api/v1/scenarios
GET    /api/v1/scenarios/{scenario_id}

POST   /api/v1/simulate

GET    /api/v1/results/{scenario_id}/latest

POST   /api/v1/incidents
GET    /api/v1/incidents
GET    /api/v1/incidents/{incident_id}
PATCH  /api/v1/incidents/{incident_id}

POST   /api/v1/explain
```

---

## AWS Lambda

Runs the Python backend without requiring a continuously running server.

Lambda handles:

* Scenario retrieval
* Incident creation
* Incident retrieval
* Incident status updates
* Simulation requests
* Simulation result retrieval
* Explanation requests

The deployed Lambda function is:

```text
crisissim-api-lambda
```

Runtime:

```text
Python 3.12
```

---

## Amazon DynamoDB

DynamoDB provides persistent storage for CrisisSim.

### `crisissim-scenarios`

Stores emergency scenarios.

Primary key:

```text
scenario_id
```

### `crisissim-results`

Stores simulation results.

Primary key:

```text
scenario_id
```

Sort key:

```text
run_at
```

### `crisissim-incidents`

Stores citizen-submitted crisis reports and their authority workflow status.

Primary key:

```text
incident_id
```

Example item:

```text
incident_id   : INC-2026-0001
hazard_type   : fire
location_name : Bengaluru, Karnataka
severity      : high
status        : reported
created_at    : ...
```

All three tables use:

```text
PAY_PER_REQUEST
```

billing.

---

## AWS IAM

IAM controls permissions for the Lambda function.

The Lambda role provides access required for:

* DynamoDB
* Bedrock
* CloudWatch Logs

The DynamoDB permissions are scoped to the CrisisSim tables.

---

## Amazon CloudWatch

CloudWatch provides Lambda logging and monitoring.

Application errors and backend execution information can be inspected through Lambda logs.

---

## Amazon Bedrock

Bedrock provides the optional natural-language explanation layer.

The simulation engine remains independent of Bedrock.

---

# 14. AWS Deployment

The project includes an automated deployment script:

```text
backend/deploy_aws.py
```

Deployment command:

```bash
cd backend
python deploy_aws.py --region us-east-1
```

The deployment script handles:

```text
1. DynamoDB table creation
2. Scenario seeding
3. IAM role configuration
4. Lambda packaging
5. Lambda deployment
6. API Gateway deployment
7. Frontend production build
8. Amplify deployment
```

The deployment automatically creates:

```text
crisissim-scenarios
crisissim-results
crisissim-incidents
```

The frontend production API URL is configured automatically during deployment.

---

# 15. Current AWS Deployment

Region:

```text
us-east-1
```

Lambda:

```text
crisissim-api-lambda
```

API Gateway:

```text
CrisisSimAPI
```

Amplify application:

```text
CrisisSim
```

Live application:

[https://main.d2l4es46nt5jz1.amplifyapp.com](https://main.d2l4es46nt5jz1.amplifyapp.com)

API base URL:

[https://gvgtmkv58b.execute-api.us-east-1.amazonaws.com/prod/api/v1](https://gvgtmkv58b.execute-api.us-east-1.amazonaws.com/prod/api/v1)

---

# 16. System Architecture

```text
React + TypeScript
        |
        v
   API Client
        |
        v
API Gateway
        |
        v
AWS Lambda
        |
        +-------------------+
        |                   |
        v                   v
Incident Handlers     Simulation Handlers
        |                   |
        v                   v
DynamoDB Incidents    Simulation Engine
                            |
                            v
                     Risk Analysis
                            |
                            v
                    Intervention Engine
                            |
                            v
                     DynamoDB Results
```

The simulation engine is kept independent from the web/API layer.

This makes it possible to:

* Test the engine independently
* Run simulations locally
* Deploy the same engine through Lambda
* Keep business logic separate from infrastructure code

---

# 17. Technology Stack

## Frontend

* React 18
* TypeScript
* Vite
* React Router
* Axios
* Leaflet
* React-Leaflet
* OpenStreetMap

## Backend

* Python
* FastAPI for local development
* AWS Lambda for production
* API Gateway
* Boto3

## Data

* Amazon DynamoDB
* In-memory store for local development

## AI

* Amazon Bedrock
* Deterministic fallback explanation layer

## Cloud

* AWS Amplify
* AWS API Gateway
* AWS Lambda
* Amazon DynamoDB
* AWS IAM
* Amazon CloudWatch
* Amazon Bedrock

## Development

* Git
* GitHub
* VS Code
* Pytest
* npm

---

# 18. Project Structure

```text
CrisisSim/
|
├── backend/
|   |
|   ├── engine/
|   |   ├── models.py
|   |   ├── hazards.py
|   |   ├── risk_scorer.py
|   |   ├── response_time.py
|   |   ├── bottleneck_detector.py
|   |   ├── intervention_engine.py
|   |   ├── evaluator.py
|   |   └── recommender.py
|   |
|   ├── handlers/
|   |   ├── scenarios.py
|   |   ├── simulation.py
|   |   ├── incidents.py
|   |   └── explanation.py
|   |
|   ├── persistence/
|   |   ├── memory_store.py
|   |   └── dynamodb.py
|   |
|   ├── bedrock/
|   |   └── explainer.py
|   |
|   ├── tests/
|   |
|   ├── lambda_function.py
|   ├── local_server.py
|   ├── seed_data.py
|   └── deploy_aws.py
|
├── frontend/
|   |
|   ├── src/
|   |   ├── components/
|   |   ├── context/
|   |   ├── pages/
|   |   ├── services/
|   |   ├── styles/
|   |   ├── types/
|   |   └── utils/
|   |
|   └── package.json
|
├── .kiro/
|   └── specs/
|
├── README.md
└── .gitignore
```

---

# 19. Running Locally

## Backend

Navigate to the backend:

```bash
cd backend
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the local API:

```bash
python local_server.py
```

The local backend uses the in-memory persistence implementation unless configured otherwise.

---

## Frontend

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend can then be accessed through the Vite development URL.

---

# 20. Testing

Backend tests:

```bash
cd backend
pytest -q
```

Frontend tests:

```bash
cd frontend
npm test
```

Production frontend build:

```bash
npm run build
```

The final implementation was validated with:

```text
Backend tests:   151 passed
Frontend tests:  64/64 passed
Frontend build:  successful
```

---

# 21. Prototype Limitations

CrisisSim is intentionally a simulation prototype.

The following limitations apply:

### Not real-time emergency intelligence

The platform does not consume live disaster feeds or emergency-service data.

### Simulated zones

Map zones and simulated facilities are generated deterministically around the selected location.

They should not be interpreted as actual hazard boundaries or verified emergency facilities.

### Prototype coefficients

Risk weights and response modifiers are transparent prototype assumptions.

They have not been presented as validated emergency-science models.

### No operational control

CrisisSim does not control:

* Emergency vehicles
* Hospitals
* Fire departments
* Police systems
* Shelters
* Utility infrastructure

### No emergency guarantees

Simulation outputs are hypothetical projections and should not be treated as guaranteed real-world outcomes.

### AI limitations

Amazon Bedrock is used only for explanation.

The deterministic simulation engine remains responsible for the actual calculations.

If Bedrock is unavailable, the system uses a deterministic fallback explanation.

---

# 22. Design Principles

CrisisSim follows several architectural principles.

## Deterministic simulation

The simulation engine produces reproducible outputs from the same inputs.

## Transparent assumptions

Risk factors and intervention logic are explicit rather than hidden inside an AI model.

## AI as an explanation layer

AI is used to communicate simulation results rather than replace the underlying decision logic.

## Separation of concerns

The architecture separates:

```text
Frontend
    |
API
    |
Handlers
    |
Simulation Engine
    |
Persistence
```

## Hazard-aware resources

Specialist resources are associated with the relevant hazard rather than being freely transferred between unrelated response domains.

## Traceability

Citizen incidents can be connected to the simulations created from them.

---

# 23. Why CrisisSim

Emergency response involves decisions under uncertainty.

CrisisSim explores how simulation can provide an intermediate step between:

```text
Incident
   ↓
Assessment
   ↓
Simulation
   ↓
Comparison
   ↓
Decision
```

Instead of presenting a single opaque recommendation, the platform exposes:

* Risk
* Response time
* Bottlenecks
* Resources
* Intervention options
* Projected impact

This makes the prototype focused on **decision support and explainability**, rather than simply producing an AI-generated answer.

---

# 24. Project Status

CrisisSim is currently deployed on AWS.

The production deployment includes:

```text
✓ Multi-hazard simulation
✓ Location-aware scenarios
✓ Citizen crisis reporting
✓ Authority incident command center
✓ Incident status workflow
✓ Incident persistence in DynamoDB
✓ Response simulation from incidents
✓ Risk visualization
✓ Bottleneck detection
✓ Intervention comparison
✓ What-If analysis
✓ Command Brief
✓ Projected Impact
✓ Amazon Bedrock explanation layer
✓ Deterministic fallback explanation
✓ AWS Amplify deployment
✓ API Gateway
✓ AWS Lambda
✓ DynamoDB persistence
✓ IAM configuration
✓ CloudWatch-compatible Lambda logging
```

---

# 25. Repository

GitHub:

[https://github.com/nidhica/CrisisSim](https://github.com/nidhica/CrisisSim)

---

# 26. Demo

The demonstration focuses on the complete workflow:

```text
1. Citizen reports a crisis
2. Incident appears in the authority command center
3. Authority acknowledges and assesses it
4. Authority launches a response simulation
5. CrisisSim generates simulated risk zones
6. Response bottlenecks are identified
7. Intervention strategies are compared
8. Projected impact is displayed
9. Command Brief summarizes the result
10. AWS services supporting the workflow are shown
```

---

# 27. AWS Feedback

Building CrisisSim on AWS made it possible to deploy the application as a serverless architecture without managing traditional backend servers.

The combination of:

```text
Amplify
   +
API Gateway
   +
Lambda
   +
DynamoDB
```

provided a straightforward way to connect the frontend, backend APIs, simulation engine, and persistent data.

One of the challenges during development was configuring cloud permissions and service access, particularly around Amazon Bedrock.

The architecture allowed the AI explanation layer to remain optional, while the deterministic simulation engine continued to operate independently.

This separation helped keep the application functional even when AI model access was unavailable.

---

# 28. Disclaimer

CrisisSim is an academic and hackathon prototype created to demonstrate AI-assisted simulation and decision-support concepts.

It is not intended for real-world emergency management, public safety operations, medical decisions, disaster response coordination, or infrastructure control.

All simulated emergency conditions, risk scores, response estimates, facilities, resources, and recommendations should be treated as hypothetical outputs generated from prototype assumptions.

Real emergency decisions should rely on qualified authorities, verified data, established emergency procedures, and appropriate professional systems.


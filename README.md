# 🚨 CrisisSim

## AI-Assisted Multi-Hazard Emergency Simulation & Decision Support

CrisisSim is a location-aware emergency simulation and decision-support platform that connects **citizen crisis reporting** with **authority assessment, deterministic multi-hazard simulation, bottleneck detection, and response strategy comparison**.

### Supported Hazards

🌊 Flood · 🔥 Fire · 🏚️ Earthquake · 🌀 Cyclone · ☣️ Industrial Accident

> ⚠️ **Prototype Disclaimer:** CrisisSim uses real-world geography but simulated emergency conditions, resources, facilities, risk zones, and response outcomes. It is not a production emergency-management system or real-time disaster intelligence platform.

---

# 🎯 Problem

During an emergency, receiving a citizen report is only the beginning.

Emergency personnel may need to understand:

- Where the incident is located
- What type of hazard is involved
- How severe the situation may be
- Which areas have higher simulated risk
- Where response bottlenecks may occur
- How resources could be allocated
- How different response strategies compare

Traditional incident reporting primarily records **what happened**.

CrisisSim extends the workflow from:

**Report → Assess → Simulate → Analyze → Compare → Decide**

---

# 💡 Solution

CrisisSim connects citizens and emergency personnel through a unified workflow:

```text
Citizen Report
      ↓
Authority Assessment
      ↓
Location-Aware Simulation
      ↓
Risk & Bottleneck Analysis
      ↓
What-If Strategy Comparison
      ↓
Projected Impact
      ↓
Decision Support

🛠️ Technology Stack
Frontend
Technology	Purpose
React 18	User interface
TypeScript	Type-safe frontend development
Vite	Frontend development and build tooling
React-Leaflet	Interactive maps
Leaflet	Map rendering
Axios	API communication
CSS	UI styling
Backend
Technology	Purpose
Python	Backend and simulation engine
FastAPI	Local development API
AWS Lambda	Serverless backend execution
Amazon API Gateway	REST API layer
Simulation & Decision Engine
Component	Purpose
Risk Scorer	Calculates simulated zone risk
Response Time Engine	Estimates simulated response time
Bottleneck Detector	Identifies simulated resource constraints
Intervention Engine	Applies response strategies
Evaluator	Compares simulation outcomes
Recommender	Produces strategy recommendations
Data & Storage
Technology	Purpose
Amazon DynamoDB	Scenario and simulation-result persistence
In-memory Store	Local development persistence
AI
Technology	Purpose
Amazon Bedrock	Optional natural-language explanation of simulation results
Deterministic Fallback	Explanation when Bedrock is unavailable
Maps & Location
Technology	Purpose
OpenStreetMap	Map tiles
Nominatim	Location search/geocoding
Development & Testing
Technology	Purpose
Git	Version control
GitHub	Source repository
Pytest	Backend testing
Vitest	Frontend testing
Kiro	Specification-driven development
☁️ AWS SERVICES USED

CrisisSim is built using a serverless AWS architecture.

AWS Service	How CrisisSim Uses It
AWS Amplify	Hosts and serves the React frontend
Amazon API Gateway	Exposes the REST API
AWS Lambda	Runs the Python backend and API handlers
Amazon DynamoDB	Stores scenarios and simulation results
Amazon Bedrock	Provides optional AI-generated explanations
Amazon CloudWatch	Lambda monitoring and logs
AWS IAM	Controls permissions between AWS resources

##AWS Architecture

                         ┌─────────────────────┐
                         │        USERS        │
                         │ Citizen / Authority │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    AWS AMPLIFY      │
                         │   React Frontend    │
                         └──────────┬──────────┘
                                    │
                                    │ HTTPS
                                    ▼
                         ┌─────────────────────┐
                         │  AMAZON API GATEWAY │
                         │      REST API       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     AWS LAMBDA      │
                         │   Python Backend    │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
          ┌────────────────┐ ┌──────────────┐ ┌────────────────┐
          │  SIMULATION    │ │   DYNAMODB   │ │    BEDROCK     │
          │     ENGINE     │ │              │ │                │
          │                │ │ Scenarios    │ │ AI Explanation │
          │ Risk Scoring   │ │ Results      │ │    Layer       │
          │ Response Time  │ │              │ │                │
          │ Bottlenecks    │ └──────────────┘ └────────────────┘
          │ Interventions  │
          │ Recommendations│
          └────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    CLOUDWATCH       │
                         │  Logs & Monitoring   │
                         └─────────────────────┘

Key Features
👤 Citizen Crisis Reporting

Citizens can:

Select a hazard
Search for a real-world location
Set incident severity
Add a description
Submit a crisis report
Track report status
🏢 Authority Command Center

Authorities can:

View reported incidents
Inspect incident details
View incident locations
Update incident status
Assess incoming reports
Start a response simulation
Trace simulations back to incidents
Incident Lifecycle
Reported
   ↓
Acknowledged
   ↓
Assessing
   ↓
Response Dispatched
   ↓
Resolved
📍 Location-Aware Simulation

CrisisSim uses real-world geography to position simulated emergency scenarios.

The system generates deterministic simulated:

Risk zones
Facilities
Resources
Population impact
Hazard conditions

Real geography + simulated conditions

🌍 Multi-Hazard Simulation
Hazard	Specialist Resources
🌊 Flood	Rescue teams, ambulances
🔥 Fire	Fire crews
🏚️ Earthquake	Search & rescue teams
🌀 Cyclone	Evacuation teams, utility crews
☣️ Industrial Accident	Hazmat teams, containment units
📊 Risk & Bottleneck Analysis

The simulation evaluates factors such as:

Affected population
Hazard severity
Medical urgency
Road accessibility
Resource shortage
Hazard-specific conditions

It produces:

Simulated zone risk levels
Risk rankings
Response-time estimates
Resource bottlenecks
Recommended interventions
🔄 What-If Analysis

Responders can compare:

Baseline
Resource Reallocation
Capacity Expansion
Combined Intervention
             BASELINE
                 │
                 ▼
        ┌────────────────┐
        │ Simulation     │
        │ Result         │
        └───────┬────────┘
                │
         Apply Strategy
                │
                ▼
       ┌───────────────────┐
       │ What-If Strategy  │
       ├───────────────────┤
       │ Reallocation      │
       │ Capacity Expansion│
       │ Combined          │
       └─────────┬─────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Projected Impact│
        └─────────────────┘
🧠 Command Brief

After a simulation, CrisisSim summarizes:

Hazard
Overall risk
Highest-risk zone
Primary bottleneck
Estimated response time
Recommended intervention
Reason for recommendation

The Command Brief is derived from simulation results.

🤖 AI-Assisted Explanation

The core emergency simulation is not performed by an LLM.

The deterministic engine performs:

Risk Scoring
     ↓
Response Time
     ↓
Bottleneck Detection
     ↓
Intervention Evaluation
     ↓
Recommendation

Amazon Bedrock is then used as an optional explanation layer.

Simulation Result
       │
       ▼
Amazon Bedrock
       │
       ▼
Natural-Language Explanation

If Bedrock is unavailable, a deterministic fallback explanation is used.

🏗️ System Architecture

                     CRISISSIM APPLICATION

 ┌───────────────────────────────────────────────────────────┐
 │                     USER INTERFACE                        │
 │                                                           │
 │        React + TypeScript + Vite + Leaflet               │
 └──────────────────────────┬────────────────────────────────┘
                            │
                            ▼
 ┌───────────────────────────────────────────────────────────┐
 │                    AWS AMPLIFY                            │
 │                  Frontend Hosting                         │
 └──────────────────────────┬────────────────────────────────┘
                            │
                            ▼
 ┌───────────────────────────────────────────────────────────┐
 │                 AMAZON API GATEWAY                        │
 │                      REST API                             │
 └──────────────────────────┬────────────────────────────────┘
                            │
                            ▼
 ┌───────────────────────────────────────────────────────────┐
 │                     AWS LAMBDA                            │
 │                    Python Backend                         │
 │                                                           │
 │  Incidents │ Scenarios │ Simulation │ Explanation        │
 └─────────────┬───────────────────────┬─────────────────────┘
               │                       │
               ▼                       ▼
 ┌────────────────────────┐   ┌─────────────────────────────┐
 │   SIMULATION ENGINE    │   │       AWS SERVICES          │
 │                        │   │                             │
 │ • Risk Scoring         │   │ DynamoDB → Persistence      │
 │ • Response Time        │   │ Bedrock → Explanation       │
 │ • Bottlenecks          │   │ CloudWatch → Monitoring     │
 │ • Interventions        │   │ IAM → Permissions           │
 │ • Evaluation           │   │                             │
 │ • Recommendations      │   │                             │
 └────────────────────────┘   └─────────────────────────────┘

🧮 Simulation Engine

The simulation engine is a separate Python module and does not depend on the frontend or LLM.

Scenario
   │
   ▼
Risk Scoring
   │
   ▼
Response-Time Estimation
   │
   ▼
Bottleneck Detection
   │
   ▼
Intervention Evaluation
   │
   ▼
Strategy Recommendation
   │
   ▼
Simulation Result

Hazard-Specific Factors

Flood

Flood severity
Water velocity
Drainage failure

Fire

Fire intensity
Smoke exposure
Spread potential

Earthquake

Structural damage
Trapped-person likelihood
Aftershock risk

Cyclone

Wind severity
Storm-surge exposure
Power-outage severity

Industrial Accident

Toxic-release severity
Exposure level
Containment failure


---

# 📁 Project Structure

```text
CrisisSim/
├── .kiro/specs/crisis-sim/
├── backend/
│   ├── bedrock/
│   ├── engine/
│   ├── handlers/
│   ├── persistence/
│   ├── tests/
│   ├── lambda_function.py
│   ├── local_server.py
│   ├── seed_data.py
│   └── deploy_aws.py
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── context/
│       ├── pages/
│       ├── services/
│       ├── styles/
│       ├── types/
│       └── utils/
├── .gitignore
└── README.md
```

---

# 🚀 Running Locally

## Prerequisites

- Python 3.12+
- Node.js and npm
- Git

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn local_server:app --reload --port 8000
```

The local API runs at:

```text
http://localhost:8000
```

## Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite.

---

# 🧪 Testing

## Backend

From `backend/`:

```bash
pytest
```

The backend tests cover simulation logic, risk scoring, response-time calculations, bottleneck detection, interventions, recommendations, multi-hazard behavior, incident APIs, and handlers.

## Frontend

From `frontend/`:

```bash
npm test
```

The frontend tests cover citizen reporting, incident workflows, simulation creation, location handling, maps, risk visualization, Command Brief, Projected Impact, and What-If analysis.

## Production Build

```bash
npm run build
```

---

# ☁️ Deployment

CrisisSim uses a serverless AWS deployment:

```text
React Frontend
      │
      ▼
AWS Amplify
      │
      ▼
Amazon API Gateway
      │
      ▼
AWS Lambda
      │
      ├── Simulation Engine
      ├── DynamoDB
      └── Bedrock Explanation Layer
```

The deployment tooling is located at:

```text
backend/deploy_aws.py
```

AWS credentials, access keys, private keys, and environment secrets must never be committed to the repository.

---

# ⚠️ Prototype Limitations

CrisisSim is an **emergency simulation and decision-support prototype**, not a production emergency-management system.

## Simulated Conditions

The following are simulated or generated:

- Hazard conditions
- Risk zones
- Facilities
- Resource availability
- Population impact
- Response-time estimates
- Bottlenecks
- Intervention outcomes

The selected location represents real geography, while the emergency conditions and assets around it are simulated.

## Deterministic Simulation

The core simulation uses transparent deterministic coefficients and assumptions intended to demonstrate a decision-support workflow. These assumptions have not been presented as validated emergency-response models.

## AI Limitations

Amazon Bedrock is an explanation layer. The deterministic simulation engine performs the numerical calculations.

Bedrock does not determine:

- Risk scores
- Response times
- Bottlenecks
- Resource allocations
- Intervention outcomes

If Bedrock is unavailable, CrisisSim uses a deterministic fallback explanation.

## Operational Limitations

CrisisSim does not:

- Provide real-time disaster intelligence
- Connect to emergency dispatch systems
- Predict actual disasters
- Represent live hospital or shelter availability
- Issue real emergency alerts
- Replace trained emergency personnel
- Provide validated operational emergency instructions

> **CrisisSim should not be used to make real emergency-response decisions.**

---

# 🎯 Why CrisisSim?

CrisisSim extends an incident-reporting workflow beyond simply recording what happened.

```text
REPORT
   ↓
ASSESS
   ↓
SIMULATE
   ↓
ANALYZE
   ↓
COMPARE
   ↓
DECIDE
```

The platform connects citizen reporting with authority assessment and simulation-based exploration of response strategies.

---

# 📌 Project Status

CrisisSim currently demonstrates:

- ✅ Multi-hazard emergency simulation
- ✅ Citizen crisis reporting
- ✅ Authority incident management
- ✅ Location-aware scenarios
- ✅ Risk analysis
- ✅ Bottleneck detection
- ✅ Response strategy comparison
- ✅ What-If analysis
- ✅ Projected impact analysis
- ✅ Command Brief
- ✅ AWS serverless architecture
- ✅ DynamoDB persistence for scenarios and simulation results
- ✅ Optional Bedrock explanation
- ✅ Backend testing
- ✅ Frontend testing

---

# 🔗 Repository

**GitHub:**  
https://github.com/nidhica/CrisisSim

---

# ⚖️ Disclaimer

CrisisSim is a prototype created for demonstrating emergency simulation and decision-support concepts.

All simulated emergency conditions, resources, facilities, risk zones, response times, and response outcomes are intended for demonstration purposes only.

The platform does not represent live emergency conditions and should not be used as a substitute for trained emergency personnel, official emergency systems, or validated emergency-response models.

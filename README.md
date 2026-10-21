# Cloud Package Advisor

An AI-powered infrastructure consulting agent built with the Google Agent Development Kit (ADK) and Gemini on Google Cloud Agent Engine.

Cloud Package Advisor assists users in evaluating cloud hosting requirements, right-sizing virtual machine configurations, comparing local pricing against equivalent hyperscaler options, generating architectural diagrams, and performing precise budget projections in an execution sandbox.

> **Note on Data:** All package specifications, tiers, and pricing values are illustrative dummy data.

---

## Key Capabilities & Implemented Tools

1. **Firestore Package Catalog & Preferences**:
   - `list_cloud_packages`: Queries available compute packages from Firestore (`cloud_packages` collection) filtered by workload category.
   - `get_cloud_package`: Retrieves detailed hardware specifications (vCPU, RAM, NVMe storage, bandwidth) and baseline pricing.
   - `save_user_workload_preference` & `get_user_workload_preference`: Persists and retrieves user workload specs, preferred operating stacks, and target monthly budgets in IDR across sessions.

2. **Real-time Currency Conversion & Pricing Comparison**:
   - `get_usd_to_idr_rate`: Queries the live Frankfurter exchange rate API for real-time USD to IDR currency conversion without API keys.
   - `compare_package_cost`: Computes side-by-side comparisons of local IDR pricing against USD hyperscaler alternatives converted to IDR with calculated percentage savings.

3. **Cloud Architecture Visualization**:
   - `generate_architecture_image`: Prompts `gemini-3.1-flash-lite-image` on Vertex AI to produce custom 3D isometric architecture diagrams for recommended setups, stores them as ADK artifacts, and uploads the image bytes directly to a public Google Cloud Storage bucket.

4. **Agent Engine Sandbox Code Execution**:
   - Integrated with `AgentEngineSandboxCodeExecutor` on Agent Engine to execute arbitrary Python code safely within an isolated remote sandbox for precise total cost of ownership (TCO) formulas and multi-year sizing projections.

5. **FastAPI Proxy & Web Chat Interface**:
   - Built with a minimal FastAPI proxy communicating with the deployed agent over the Agent-to-Agent (A2A) protocol.
   - Clean web chat frontend with native markdown rendering and A2UI support.

---

## Project Structure

```
├── app/
│   ├── __init__.py
│   └── agent.py              # Root agent, tools, sandbox executor, and ADK configuration
├── frontend/
│   ├── main.py               # FastAPI proxy talking A2A protocol to Agent Engine
│   ├── requirements.txt      # Frontend runtime dependencies
│   ├── Dockerfile            # Container build specification for Cloud Run
│   └── static/
│       └── index.html        # Responsive web chat UI
├── seed_firestore.py         # Catalog population script for Firestore
├── project_brief.md          # Architecture and design brief
├── agents-cli-manifest.yaml  # ADK project manifest
└── pyproject.toml            # Python dependencies and packaging configuration
```

---

## Setup & Running Locally

### Prerequisites

- Python 3.11+
- Google Cloud CLI (`gcloud`) authenticated with Application Default Credentials:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  gcloud config set project <YOUR_GCP_PROJECT_ID>
  ```
- Google Cloud project with Firestore, Vertex AI, and Cloud Storage enabled.

### 1. Agent Setup

1. Install project dependencies:
   ```bash
   pip install -e .
   ```

2. Seed the Firestore catalog:
   ```bash
   python seed_firestore.py
   ```

3. Run the local ADK developer playground:
   ```bash
   agents-cli playground
   ```

### 2. Frontend Setup

1. Navigate to the `frontend/` directory and install dependencies:
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. Set required environment variables:
   ```bash
   export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<REGION>/reasoningEngines/<ENGINE_ID>"
   export AGENT_DIRECTORY="app"
   ```

3. Start the FastAPI proxy and chat interface:
   ```bash
   python main.py
   ```

---

## Deployment Instructions

### Deploy Agent to Agent Engine
```bash
agents-cli deploy --project <YOUR_GCP_PROJECT_ID> --region <REGION>
```

### Deploy Frontend to Cloud Run
```bash
cd frontend
gcloud run deploy cloud-package-advisor-frontend \
  --source . \
  --project <YOUR_GCP_PROJECT_ID> \
  --region <REGION> \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<REGION>/reasoningEngines/<ENGINE_ID>",AGENT_DIRECTORY="app"
```

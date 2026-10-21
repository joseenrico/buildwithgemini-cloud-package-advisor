# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import time
import urllib.request
from typing import Any, Dict, List, Optional
from google import genai
from google.cloud import firestore, storage
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.genai import types

MODEL = "gemini-3.8-flash"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"
PROJECT_ID = "qwiklabs-gcp-03-2cb26d0bff37"
GCS_BUCKET_NAME = "cloud-package-advisor-qwiklabs-gcp-03-2cb26d0bff37"
AGENT_ENGINE_RESOURCE = "projects/153161458973/locations/us-east1/reasoningEngines/1809016585575202816"

_firestore_client: Optional[firestore.Client] = None
_storage_client: Optional[storage.Client] = None
_genai_client: Optional[genai.Client] = None

def get_firestore_client() -> firestore.Client:
    """Returns a singleton Firestore client with the hardcoded project ID."""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project=PROJECT_ID)
    return _firestore_client

def get_storage_client() -> storage.Client:
    """Returns a singleton Cloud Storage client with the hardcoded project ID."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client

def get_genai_client() -> genai.Client:
    """Returns a singleton GenAI client configured for Vertex AI in global location."""
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    return _genai_client


def list_cloud_packages(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists available cloud VM packages from the Firestore catalog.

    Args:
        category: Optional category filter (e.g. 'Web', 'E-Commerce', 'Microservices', 'Analytics').

    Returns:
        A list of cloud package dictionaries with specs, IDR pricing, and USD hyperscaler equivalents.
    """
    db = get_firestore_client()
    collection = db.collection("cloud_packages")
    docs = collection.stream()
    
    results = []
    for doc in docs:
        data = doc.to_dict()
        if category:
            cat_match = category.lower() in data.get("category", "").lower() or category.lower() in data.get("recommended_for", "").lower()
            if not cat_match:
                continue
        results.append(data)
    
    return results


def get_cloud_package(package_id: str) -> Dict[str, Any]:
    """Gets detailed specifications for a specific cloud package by ID.

    Args:
        package_id: The ID of the package (e.g. 'starter-compute', 'business-pro', 'scale-workload', 'enterprise-turbo').

    Returns:
        The package details or an error message if not found.
    """
    db = get_firestore_client()
    doc_ref = db.collection("cloud_packages").document(package_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Package '{package_id}' not found in catalog."}
    return doc.to_dict()


def get_usd_to_idr_rate() -> Dict[str, Any]:
    """Fetches the live USD to IDR currency exchange rate from Frankfurter API.

    Returns:
        Dictionary with base currency, target currency, date, and live exchange rate.
    """
    url = "https://api.frankfurter.dev/v1/latest?base=USD&symbols=IDR"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CloudPackageAdvisor/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rate = data.get("rates", {}).get("IDR")
            return {
                "base": "USD",
                "target": "IDR",
                "rate": rate,
                "date": data.get("date"),
            }
    except Exception as e:
        return {"error": f"Failed to fetch exchange rate: {str(e)}", "fallback_rate": 16000.0}


def compare_package_cost(package_id: str) -> Dict[str, Any]:
    """Compares the local IDR package price with its hyperscaler USD equivalent converted to IDR.

    Args:
        package_id: The ID of the package to compare (e.g. 'starter-compute', 'business-pro', 'scale-workload', 'enterprise-turbo').

    Returns:
        Side-by-side cost comparison including local IDR price, hyperscaler USD price, converted IDR price, and savings.
    """
    pkg = get_cloud_package(package_id)
    if "error" in pkg:
        return pkg

    rate_info = get_usd_to_idr_rate()
    rate = rate_info.get("rate") or rate_info.get("fallback_rate", 16000.0)

    local_price_idr = pkg.get("monthly_price_idr", 0)
    hyperscaler_usd = pkg.get("hyperscaler_monthly_price_usd", 0.0)
    hyperscaler_equiv_name = pkg.get("hyperscaler_equiv_name", "Hyperscaler Alternative")
    hyperscaler_price_idr = round(hyperscaler_usd * rate)
    diff_idr = hyperscaler_price_idr - local_price_idr
    pct_savings = round((diff_idr / hyperscaler_price_idr) * 100, 1) if hyperscaler_price_idr > 0 else 0

    return {
        "package_id": package_id,
        "package_name": pkg.get("name"),
        "specs": f"{pkg.get('vcpus')} vCPU / {pkg.get('ram_gb')} GB RAM / {pkg.get('storage_gb')} GB SSD",
        "exchange_rate_usd_idr": rate,
        "local_provider": {
            "name": pkg.get("name"),
            "monthly_price_idr": local_price_idr,
            "formatted_price": f"IDR {local_price_idr:,.0f}",
        },
        "hyperscaler_equivalent": {
            "name": hyperscaler_equiv_name,
            "monthly_price_usd": hyperscaler_usd,
            "monthly_price_idr_converted": hyperscaler_price_idr,
            "formatted_price_usd": f"${hyperscaler_usd:.2f}",
            "formatted_price_idr": f"IDR {hyperscaler_price_idr:,.0f}",
        },
        "comparison": {
            "monthly_savings_idr": diff_idr,
            "percentage_savings": f"{pct_savings}%",
            "is_local_cheaper": diff_idr > 0,
        },
    }


def _generate_image_bytes(prompt: str) -> tuple[Optional[bytes], str]:
    """Helper running in thread to generate image bytes via GenAI."""
    client = get_genai_client()
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=prompt,
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return part.inline_data.data, part.inline_data.mime_type or "image/jpeg"
    return None, "image/jpeg"


def _upload_blob_to_gcs(filename: str, image_bytes: bytes, mime_type: str) -> str:
    """Helper running in thread to upload image bytes to GCS."""
    storage_client = get_storage_client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(f"diagrams/{filename}")
    blob.upload_from_string(image_bytes, content_type=mime_type)
    return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/diagrams/{filename}"


async def generate_architecture_image(
    package_id: str,
    workload_description: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generates an illustrative cloud architecture diagram for a recommended package.

    Args:
        package_id: The ID of the recommended cloud package (e.g. 'starter-compute', 'business-pro', 'scale-workload', 'enterprise-turbo').
        workload_description: Short description of the user workload (e.g. 'E-commerce API with PostgreSQL and Redis').
        tool_context: ADK tool context for saving artifacts.

    Returns:
        Dictionary containing the public image URL, package ID, and filename.
    """
    pkg = await asyncio.to_thread(get_cloud_package, package_id)
    pkg_name = pkg.get("name", package_id)
    specs = f"{pkg.get('vcpus', 2)} vCPU, {pkg.get('ram_gb', 4)}GB RAM, {pkg.get('storage_gb', 80)}GB SSD" if "error" not in pkg else "Cloud VM"

    prompt = (
        f"A clean, modern, high-quality isometric cloud architecture diagram illustration for '{workload_description}'. "
        f"Features a central cloud server cluster representing {pkg_name} ({specs}), with incoming traffic load balancer, "
        f"database storage block, caching tier, and security shield. Minimalist tech aesthetic, crisp vector style, "
        f"vibrant blue and teal neon accents on dark clean background, 3D isometric perspective, no messy text."
    )

    image_bytes, mime_type = await asyncio.to_thread(_generate_image_bytes, prompt)
    if not image_bytes:
        return {"error": "Failed to generate image from model response."}

    timestamp = int(time.time())
    extension = "png" if "png" in mime_type else "jpg"
    filename = f"arch_{package_id}_{timestamp}.{extension}"

    try:
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=part)
    except Exception as e:
        print(f"Warning: Failed to save artifact in tool_context: {e}")

    public_url = await asyncio.to_thread(_upload_blob_to_gcs, filename, image_bytes, mime_type)

    return {
        "status": "success",
        "package_id": package_id,
        "filename": filename,
        "image_url": public_url,
        "description": f"Illustrative cloud architecture for {pkg_name} ({workload_description})",
    }


def save_user_workload_preference(
    user_id: str,
    app_type: str,
    monthly_budget_idr: int,
    preferred_stack: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Saves or updates a user's workload preference and budget in Firestore.

    Args:
        user_id: Unique identifier for the user or organization (e.g. 'user_default', or user name).
        app_type: Type of workload/application (e.g. 'E-Commerce Store', 'Node.js Microservices').
        monthly_budget_idr: User's target monthly budget in IDR.
        preferred_stack: Preferred stack or OS (e.g. 'Ubuntu + Nginx + PostgreSQL', 'Docker + Node.js').
        notes: Optional additional notes about sizing or traffic expectations.

    Returns:
        Confirmation dictionary with saved data.
    """
    db = get_firestore_client()
    doc_ref = db.collection("user_preferences").document(user_id)
    data = {
        "user_id": user_id,
        "app_type": app_type,
        "monthly_budget_idr": monthly_budget_idr,
        "preferred_stack": preferred_stack,
        "notes": notes or "",
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(data, merge=True)
    return {"status": "success", "message": f"Preferences saved for user '{user_id}'", "data": {k: v for k, v in data.items() if k != 'updated_at'}}


def get_user_workload_preference(user_id: str) -> Dict[str, Any]:
    """Retrieves a user's stored workload preferences and budget from Firestore.

    Args:
        user_id: Unique identifier for the user (e.g. 'user_default', or user name).

    Returns:
        The stored preference dictionary or a not found message.
    """
    db = get_firestore_client()
    doc_ref = db.collection("user_preferences").document(user_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"status": "not_found", "message": f"No stored preferences for user '{user_id}'"}
    data = doc.to_dict()
    if "updated_at" in data:
        data["updated_at"] = str(data["updated_at"])
    return data


root_agent = Agent(
    name="cloud_package_advisor",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Cloud Package Advisor, an expert cloud infrastructure consultant. "
        "Your role is to help users select the right cloud VM package for their workload.\n"
        "Guidelines:\n"
        "1. Consult the Firestore catalog using `list_cloud_packages` or `get_cloud_package` to recommend suitable packages.\n"
        "2. Use `get_usd_to_idr_rate` to fetch real-time USD to IDR currency conversion rates.\n"
        "3. Use `compare_package_cost` to provide side-by-side cost comparisons between local IDR packages and hyperscaler USD alternatives converted to IDR.\n"
        "4. Generate an illustrative architecture visual using `generate_architecture_image` when recommending a package or setup.\n"
        "5. Save and retrieve user requirements, budgets (in IDR), and preferred stacks using `save_user_workload_preference` and `get_user_workload_preference`.\n"
        "6. Use Python code execution in your sandbox environment for precise budget calculations, sizing formulas, and multi-year TCO projections.\n"
        "7. Always present clear comparison tables showing specs (vCPUs, RAM, storage), IDR monthly price, hyperscaler USD equivalent, and converted IDR cost.\n"
    ),
    code_executor=AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=AGENT_ENGINE_RESOURCE,
    ),
    tools=[
        list_cloud_packages,
        get_cloud_package,
        get_usd_to_idr_rate,
        compare_package_cost,
        generate_architecture_image,
        save_user_workload_preference,
        get_user_workload_preference,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)

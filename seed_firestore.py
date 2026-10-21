#!/usr/bin/env python3
"""Seed script for Cloud Package Advisor Firestore database."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-2cb26d0bff37"

PACKAGES = [
    {
        "id": "starter-compute",
        "name": "IDCloud Starter Compute",
        "category": "General Purpose / Web",
        "vcpus": 2,
        "ram_gb": 4,
        "storage_gb": 80,
        "bandwidth_tb": 2,
        "recommended_for": "Small blogs, landing pages, dev environments",
        "monthly_price_idr": 250000,
        "hyperscaler_equiv_name": "AWS t4g.medium / GCP e2-medium",
        "hyperscaler_monthly_price_usd": 28.50,
    },
    {
        "id": "business-pro",
        "name": "IDCloud Business Pro",
        "category": "E-Commerce / API Backend",
        "vcpus": 4,
        "ram_gb": 8,
        "storage_gb": 160,
        "bandwidth_tb": 5,
        "recommended_for": "Medium traffic e-commerce, REST API backends, Laravel/Django apps",
        "monthly_price_idr": 550000,
        "hyperscaler_equiv_name": "AWS c7g.xlarge / GCP c2-standard-4",
        "hyperscaler_monthly_price_usd": 68.00,
    },
    {
        "id": "scale-workload",
        "name": "IDCloud Scale Master",
        "category": "High Concurrency / Microservices",
        "vcpus": 8,
        "ram_gb": 16,
        "storage_gb": 320,
        "bandwidth_tb": 10,
        "recommended_for": "High-traffic web apps, microservices clusters, database servers",
        "monthly_price_idr": 1150000,
        "hyperscaler_equiv_name": "AWS m7g.2xlarge / GCP n2-standard-8",
        "hyperscaler_monthly_price_usd": 142.00,
    },
    {
        "id": "enterprise-turbo",
        "name": "IDCloud Enterprise Turbo",
        "category": "Heavy Data / AI & Analytics",
        "vcpus": 16,
        "ram_gb": 32,
        "storage_gb": 640,
        "bandwidth_tb": 20,
        "recommended_for": "Data processing, analytics engines, enterprise ERP, high-load APIs",
        "monthly_price_idr": 2250000,
        "hyperscaler_equiv_name": "AWS c7g.4xlarge / GCP c2-standard-16",
        "hyperscaler_monthly_price_usd": 285.00,
    },
]

def seed():
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("cloud_packages")
    
    for pkg in PACKAGES:
        doc_id = pkg["id"]
        doc_ref = collection.document(doc_id)
        doc_ref.set(pkg)
        print(f"  ✓ Seeded package: {doc_id} ({pkg['name']}) - IDR {pkg['monthly_price_idr']:,}")
    
    print(f"Successfully seeded {len(PACKAGES)} packages into 'cloud_packages' collection.")

if __name__ == "__main__":
    seed()

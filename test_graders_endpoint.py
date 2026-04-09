#!/usr/bin/env python3
"""Test /graders endpoint to verify all 3 graders are exposed."""
import json
from app import app

with app.test_client() as client:
    # Test /graders endpoint
    resp = client.get('/graders')
    data = resp.get_json()
    
    print("=== /graders Response ===")
    print(json.dumps(data, indent=2))
    
    print("\n=== /graders/<grader_id> for each grader ===")
    for grader in data.get('graders', []):
        grader_id = grader['id']
        resp = client.get(f'/graders/{grader_id}')
        print(f"\n{grader_id}:")
        print(json.dumps(resp.get_json(), indent=2))

import urllib.request
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def post_json(endpoint, payload):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_hackathon_demo_flow():
    session_id = f"judge-demo-{int(time.time())}"
    print(f"\n--- Testing Hackathon Demo Flow on session: {session_id} ---")

    steps = [
        ("When is my Physics exam?", "EXAM_QUERY"),
        ("Where is it?", "LOCATION_QUERY"),
        ("What do I need to bring?", "EXAM_QUERY"),
        ("Remind me tomorrow.", "REMINDER_CREATE")
    ]

    for i, (query, expected_intent) in enumerate(steps, 1):
        print(f"\n[Step {i}] User: '{query}'")
        data = post_json("/api/chat", {
            "session_id": session_id,
            "message": query,
            "speak_aloud": False
        })
        print(f"  AI: {data['response_text'][:100]}...")
        print(f"  Standard Intent: {data.get('standard_intent')}")
        print(f"  Action Executed: {data.get('action_executed')}")
        print(f"  Metrics: {data.get('metrics')}")
        print(f"  Source details count: {len(data.get('source_details', []))}")
        
        # Verify step assertions
        if i == 1:
            assert "Physics" in data['response_text'] or "October 14" in data['response_text'], "Step 1 missing Physics exam date"
            assert data.get('standard_intent') == expected_intent
        elif i == 2:
            assert "Hall B-204" in data['response_text'] or "Science Block" in data['response_text'], "Step 2 missing hall location"
            assert data.get('standard_intent') == expected_intent
        elif i == 3:
            assert "Hall Ticket" in data['response_text'] or "calculator" in data['response_text'], "Step 3 missing exam equipment info"
            assert data.get('standard_intent') == expected_intent
        elif i == 4:
            assert data.get('standard_intent') == expected_intent
            assert data.get('action_executed') == "create_reminder"
            print("  Action Result:", data.get('action_result'))
            assert "Physics" in data.get('action_result', {}).get('title', '')

    print("\n>>> ALL 4 DEMO STEPS PASSED WITH 100% SUCCESS! <<<")

if __name__ == "__main__":
    test_hackathon_demo_flow()

import asyncio
import httpx
import uuid
import random
import time
from datetime import datetime

# CONFIG
API_URL = "http://localhost:8080"
TEST_USER_UUID = "d290f1ee-6c54-4b01-90e6-d701748f0851" # Must be a valid UUID format
AUTH_TOKEN = f"Bearer {TEST_USER_UUID}"

async def create_test_user():
    # In a real scenario, we'd hit a registration endpoint.
    # Here, we assume the DB seed script or manual setup has prepared the environment.
    # However, to ensure the test works, we'll try to insert a user directly via a helper if possible
    # or rely on the server handling it.
    pass

def generate_batch_data(row_count=1000):
    print(f"Generating {row_count} rows of synthetic DNA/Vitals data...")
    data = []
    
    # Metric codes must match what's seeded in init_db.sql or ingestion service
    metrics = ['HEALX_TEST_TOTAL', 'HEALX_VIT_D', 'HK_HR_RESTING', 'HK_VO2_MAX']
    
    for _ in range(row_count):
        metric = random.choice(metrics)
        data.append({
            "metric_code": metric,
            "recorded_at": datetime.utcnow().isoformat(),
            "value_numeric": round(random.uniform(10, 1000), 2),
            "value_text": None,
            "raw_metadata": {"device": "TestHarness v1"}
        })
    
    return {
        "source_name": "Test Harness Load Test",
        "data": data
    }

async def run_test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        resp = await client.get(f"{API_URL}/")
        print(f"Health Check: {resp.status_code} - {resp.json()}")
        if resp.status_code != 200:
            print("API not healthy. Is docker-compose up running?")
            return

        # 2. Prepare Payload
        row_count = 5000
        payload = generate_batch_data(row_count)

        # 3. Send Request
        print(f"Sending batch of {row_count} observations...")
        start_time = time.time()
        
        try:
            resp = await client.post(
                f"{API_URL}/observations/batch",
                json=payload,
                headers={"Authorization": AUTH_TOKEN}
            )
            end_time = time.time()
            duration = end_time - start_time
            
            if resp.status_code in [200, 201]:
                print(f"✅ Success! Status: {resp.status_code}")
                print(f"⏱️ Time taken: {duration:.4f} seconds")
                print(f"⚡ Throughput: {row_count / duration:.0f} rows/sec")
                print(f"Response: {resp.json()}")
            else:
                print(f"❌ Failed. Status: {resp.status_code}")
                print(resp.text)

        except Exception as e:
            print(f"Connection failed: {e}")
            print("Ensure the API is running on localhost:8080")

        # 4. Test Media Presigned URL
        print("\nTesting Media Presigned URL generation...")
        media_payload = {
            "filename": "lab_report.pdf",
            "file_type": "LabReport",
            "content_type": "application/pdf"
        }
        resp = await client.post(
             f"{API_URL}/media/upload-url",
             json=media_payload,
             headers={"Authorization": AUTH_TOKEN}
        )
        print(f"Media Response: {resp.json()}")

if __name__ == "__main__":
    # Ensure the user exists in DB before running this if strictly enforcing FKs
    # For this test, you might need to insert the user manually into the postgres container:
    # INSERT INTO users (id, email) VALUES ('d290f1ee-6c54-4b01-90e6-d701748f0851', 'test@healx.ai');
    
    print("Ensure you have inserted the test user UUID into the database if FK constraints are active.")
    print(f"User ID: {TEST_USER_UUID}")
    asyncio.run(run_test())

import requests

BASE_URL = "http://localhost:8000"
ADMIN_CREDS = {"email": "admin@platform.com", "password": "admin123!"}
STUDENT_CREDS = {"email": "student@student.com", "password": "studentpassword"}

def login(creds):
    r = requests.post(f"{BASE_URL}/auth/login", json=creds)
    if r.status_code == 200:
        return r.json().get("access_token")
    print(f"Login failed for {creds['email']}: {r.status_code} {r.text}")
    return None

def test():
    # Wait for the backend to be fully up
    try:
        r = requests.get(f"{BASE_URL}/docs")
    except requests.exceptions.ConnectionError:
        print("Backend is not accessible at", BASE_URL)
        return

    admin_token = login(ADMIN_CREDS)
    student_token = login(STUDENT_CREDS)

    if not student_token:
        print("Could not get student token! Using admin token for tests.")
        student_token = admin_token

    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Test AI FAQs
    print("\n--- Testing AI FAQs ---")
    r = requests.get(f"{BASE_URL}/ai/faqs", headers=headers)
    print("GET /ai/faqs -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    # 2. Test Learning Dashboard
    print("\n--- Testing Learning Dashboard ---")
    r = requests.get(f"{BASE_URL}/learning/dashboard", headers=headers)
    print("GET /learning/dashboard -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    # 3. Test Monthly Exams
    print("\n--- Testing Monthly Exams ---")
    r = requests.get(f"{BASE_URL}/exams/monthly", headers=headers)
    print("GET /exams/monthly -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    # 4. Test Lesson Completion
    print("\n--- Testing Lesson Completion ---")
    lesson_payload = {"course_id": 1, "lesson_id": 1}
    r = requests.post(f"{BASE_URL}/learning/lesson/complete", json=lesson_payload, headers=headers)
    print("POST /learning/lesson/complete -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    # 5. Test Exam Constraints & Payment Flow (Mock)
    print("\n--- Testing Exam Payment System ---")
    payment_payload = {"exam_id": 1, "payment_method": "credit_card", "success": True}
    r = requests.post(f"{BASE_URL}/exams/pay", json=payment_payload, headers=headers)
    print("POST /exams/pay -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    # 6. Test Exam Security & Monitoring
    print("\n--- Testing Exam Violations & Security Flow ---")
    # Using dummy attempt_id = 999 to test logic constraints
    violation_payload = {"attempt_id": 999, "violation_type": "tab_switch"}
    r = requests.post(f"{BASE_URL}/exams/violation", json=violation_payload, headers=headers)
    print("POST /exams/violation -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    camera_payload = {"attempt_id": 999, "camera_on": False}
    r = requests.post(f"{BASE_URL}/exams/camera-status", json=camera_payload, headers=headers)
    print("POST /exams/camera-status -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    session_payload = {"attempt_id": 999, "device_id": "test_device_123"}
    r = requests.post(f"{BASE_URL}/exams/session-close", json=session_payload, headers=headers)
    print("POST /exams/session-close -> Status:", r.status_code)
    try:
        print(r.json())
    except:
        print(r.text)

    print("\n--- Test complete ---")

if __name__ == "__main__":
    test()

"""Test script for dashboard announcements + advertisements endpoints."""

import requests

BASE_URL = "http://localhost:8000"
ADMIN_CREDS = {"email": "admin@platform.com", "password": "admin123!"}

def login():
    r = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDS)
    if r.status_code == 200:
        return r.json().get("access_token")
    print(f"Login failed: {r.status_code} {r.text}")
    return None

def test(method, path, headers, json_data=None, label=None):
    url = f"{BASE_URL}{path}"
    label = label or f"{method.upper()} {path}"
    try:
        r = getattr(requests, method)(url, headers=headers, json=json_data)
        try:
            body = r.json()
        except:
            body = r.text
        print(f"  {label} -> {r.status_code}")
        if r.status_code >= 400:
            print(f"    Response: {body}")
        return r.status_code, body
    except Exception as e:
        print(f"  {label} -> ERROR: {e}")
        return 0, None

def main():
    print("=== Phase 1/2/3 Regression ===")
    test("get", "/health", {}, label="Health")

    token = login()
    if not token:
        return
    h = {"Authorization": f"Bearer {token}"}

    test("get", "/ai/faqs", h, label="AI FAQs")
    test("get", "/learning/dashboard", h, label="Learning Dashboard")
    test("get", "/exams/monthly", h, label="Monthly Exams")
    test("get", "/simulator/profiles", h, label="Simulator Profiles")
    test("get", "/placement/status", h, label="Placement Status")
    test("get", "/feedback/my", h, label="My Feedback")
    test("get", "/admin/reports", h, label="Admin Reports")

    # === Announcements CRUD ===
    print("\n=== Announcements CRUD ===")

    # Create
    s, body = test("post", "/dashboard/admin/announcements", h,
                    {"title": "System Maintenance", "content": "Backend will be down for 2 hours on Sunday.", "priority": "high"},
                    "Create Announcement")
    ann_id = body.get("id") if s == 201 else None

    # List (admin)
    test("get", "/dashboard/admin/announcements", h, label="Admin List Announcements")

    # List (student view)
    test("get", "/dashboard/announcements", h, label="Student List Announcements")

    # Update
    if ann_id:
        test("put", f"/dashboard/admin/announcements/{ann_id}", h,
             {"title": "Updated: System Maintenance", "priority": "urgent"},
             f"Update Announcement #{ann_id}")

    # Delete
    if ann_id:
        test("delete", f"/dashboard/admin/announcements/{ann_id}", h,
             label=f"Delete Announcement #{ann_id}")

    # Verify deleted
    test("get", "/dashboard/announcements", h, label="Announcements After Delete")

    # === Advertisements CRUD ===
    print("\n=== Advertisements CRUD ===")

    # Create
    s, body = test("post", "/dashboard/admin/advertisements", h,
                    {"title": "New Course Launch!", "description": "Master Trading Strategies", "image_url": "/uploads/ad_banner.jpg", "link_url": "/courses/5", "placement": "banner"},
                    "Create Advertisement")
    ad_id = body.get("id") if s == 201 else None

    # List (admin)
    test("get", "/dashboard/admin/advertisements", h, label="Admin List Advertisements")

    # List (student view)
    test("get", "/dashboard/advertisements", h, label="Student List Advertisements")

    # List with placement filter
    test("get", "/dashboard/advertisements?placement=banner", h, label="Filter Ads by placement=banner")

    # Update
    if ad_id:
        test("put", f"/dashboard/admin/advertisements/{ad_id}", h,
             {"title": "Updated Ad", "is_active": False},
             f"Update Advertisement #{ad_id}")

    # Delete
    if ad_id:
        test("delete", f"/dashboard/admin/advertisements/{ad_id}", h,
             label=f"Delete Advertisement #{ad_id}")

    print("\n=== All tests complete ===")

if __name__ == "__main__":
    main()

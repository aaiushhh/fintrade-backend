# FItTrade LMS — Android API Integration Guide

> **Base URL** (Production): `https://<your-render-url>`  
> **Base URL** (Local Dev): `http://localhost:8000`  
> **Auth Header**: `Authorization: Bearer <access_token>`  
> **Content-Type**: `application/json`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Dashboard — Announcements & Advertisements](#2-dashboard--announcements--advertisements)
3. [Courses](#3-courses)
4. [Exams](#4-exams)
5. [Offers](#5-offers)
6. [Lectures](#6-lectures)
7. [Learning Progress](#7-learning-progress)
8. [Certificates](#8-certificates)
9. [Trading Simulator](#9-trading-simulator)
10. [Placement](#10-placement)
11. [Feedback](#11-feedback)
12. [AI Chatbot](#12-ai-chatbot)
13. [Faculty APIs *(Role: faculty)*](#13-faculty-apis-role-faculty)
14. [Distributor APIs *(Role: distributor)*](#14-distributor-apis-role-distributor)
15. [Admin APIs *(Role: admin)*](#15-admin-apis-role-admin)
16. [Error Reference](#16-error-reference)

---

## 1. Authentication

### 1.1 Register
`POST /auth/register`

Register a new **student** account. Returns JWT tokens on success.

**Request Body:**
```json
{
  "email": "student@example.com",
  "full_name": "John Doe",
  "phone": "+919876543210",
  "password": "securePass123"
}
```

| Field | Type | Required |
|---|---|---|
| `email` | string | ✅ |
| `full_name` | string | ✅ |
| `password` | string | ✅ |
| `phone` | string | ❌ |

**Response `201`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "student@example.com",
    "full_name": "John Doe",
    "phone": "+919876543210",
    "is_active": true,
    "is_verified": false,
    "avatar_url": null,
    "roles": [{"id": 1, "name": "student"}],
    "created_at": "2026-04-22T05:30:00Z"
  }
}
```

| Status | Meaning |
|---|---|
| `201` | Account created, tokens returned |
| `400` | Email already exists or invalid data |

---

### 1.2 Login
`POST /auth/login`

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "securePass123"
}
```

**Response `200`:** Same shape as register response.

| Status | Meaning |
|---|---|
| `200` | Login successful |
| `401` | Invalid credentials |

---

### 1.3 Get Current User
`GET /auth/me`  
🔒 **Auth Required**

Returns the logged-in user's profile.

**Response `200`:**
```json
{
  "id": 1,
  "email": "student@example.com",
  "full_name": "John Doe",
  "phone": "+919876543210",
  "is_active": true,
  "is_verified": false,
  "avatar_url": null,
  "roles": [{"id": 1, "name": "student"}],
  "created_at": "2026-04-22T05:30:00Z"
}
```

| Status | Meaning |
|---|---|
| `200` | Profile returned |
| `401` | Token missing or expired |

---

### 1.4 Logout
`POST /auth/logout`  
🔒 **Auth Required**

Revokes the current session token.

**Response `200`:**
```json
{ "message": "Logged out successfully" }
```

---

## 2. Dashboard — Announcements & Advertisements

### 2.1 Get Active Announcements
`GET /dashboard/announcements`  
🔒 **Auth Required**

**Response `200`:** Array of announcement objects.
```json
[
  {
    "id": 1,
    "title": "New Course Launch",
    "content": "Check out the new Trading Psychology module...",
    "is_active": true,
    "created_at": "2026-04-22T05:00:00Z"
  }
]
```

---

### 2.2 Get Active Advertisements
`GET /dashboard/advertisements`  
🔒 **Auth Required**

**Query Params (Optional):**

| Param | Type | Description |
|---|---|---|
| `placement` | string | Filter by placement: `dashboard`, `sidebar`, `banner` |

**Response `200`:** Array of advertisement objects.
```json
[
  {
    "id": 1,
    "title": "Special Discount",
    "image_url": "https://...",
    "link_url": "https://...",
    "placement": "banner",
    "is_active": true
  }
]
```

---

## 3. Courses

### 3.1 List All Published Courses
`GET /courses`

No auth required. Supports pagination.

**Query Params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 20 | Max records |

**Response `200`:** Array of courses.
```json
[
  {
    "id": 1,
    "title": "Technical Analysis Masterclass",
    "description": "...",
    "price": 4999.0,
    "thumbnail_url": "https://...",
    "is_published": true,
    "created_at": "2026-03-01T10:00:00Z"
  }
]
```

---

### 3.2 Get Course Details
`GET /courses/{course_id}`

Returns full course with all modules and lessons.

**Response `200`:**
```json
{
  "id": 1,
  "title": "Technical Analysis Masterclass",
  "description": "...",
  "price": 4999.0,
  "thumbnail_url": "https://...",
  "modules": [
    {
      "id": 1,
      "title": "Module 1: Chart Patterns",
      "order": 1,
      "lessons": [
        {
          "id": 1,
          "title": "Introduction to Candlesticks",
          "content_type": "video",
          "content_url": "https://...",
          "order": 1,
          "is_published": true
        }
      ]
    }
  ]
}
```

| Status | Meaning |
|---|---|
| `200` | Course details returned |
| `404` | Course not found |

---

### 3.3 Get User's Enrolled Courses
`GET /courses/enrolled`  
🔒 **Auth Required**

**Response `200`:** Array of enrollment objects.
```json
[
  {
    "id": 1,
    "user_id": 3,
    "course_id": 1,
    "enrolled_at": "2026-04-01T10:00:00Z",
    "is_active": true,
    "progress_percent": 40.0,
    "discount_applied": 500.0,
    "price_paid": 4499.0,
    "course": { "id": 1, "title": "Technical Analysis Masterclass", "..." }
  }
]
```

---

### 3.4 Enroll in a Course
`POST /courses/{course_id}/enroll`  
🔒 **Auth Required**

**Request Body (Optional):**
```json
{
  "distributor_code": "REGION123"
}
```

**Response `200`:** Full enrollment object (see 3.3 shape).

| Status | Meaning |
|---|---|
| `200` | Enrolled successfully |
| `409` | Already enrolled |
| `404` | Course not found |

---

## 4. Exams

### 4.1 List Active Entrance Exams
`GET /exams/entrance`

No auth required.

**Response `200`:**
```json
[
  {
    "id": 1,
    "title": "Financial Markets Entrance Exam",
    "description": "...",
    "course_id": 1,
    "duration_minutes": 60,
    "passing_score": 60.0,
    "is_active": true,
    "created_at": "2026-03-01T00:00:00Z"
  }
]
```

---

### 4.2 Start an Entrance Exam
`POST /exams/start?exam_id={id}`  
🔒 **Auth Required**

| Query Param | Type | Required |
|---|---|---|
| `exam_id` | int | ✅ |

**Response `200`:**
```json
{
  "attempt_id": 5,
  "exam_id": 1,
  "started_at": "2026-04-22T10:00:00Z",
  "duration_minutes": 60,
  "total_questions": 30
}
```

| Status | Meaning |
|---|---|
| `200` | Exam started |
| `403` | 30-day cooldown restriction active |

---

### 4.3 Get Exam Questions
`GET /exams/questions?exam_id={id}`  
🔒 **Auth Required**

**⚠️ Note:** Correct answers are hidden from the response.

**Response `200`:**
```json
[
  {
    "id": 101,
    "question_text": "What is a Doji candlestick?",
    "question_type": "mcq",
    "marks": 1.0,
    "order": 1,
    "options": [
      {"id": 201, "option_text": "A bullish reversal signal", "order": 1},
      {"id": 202, "option_text": "A pattern with equal open and close", "order": 2}
    ]
  }
]
```

---

### 4.4 Submit Single Answer
`POST /exams/answer?attempt_id={id}`  
🔒 **Auth Required**

| Query Param | Type | Required |
|---|---|---|
| `attempt_id` | int | ✅ |

**Request Body:**
```json
{
  "question_id": 101,
  "selected_option_id": 202
}
```

**Response `200`:**
```json
{ "message": "Answer saved" }
```

---

### 4.5 Submit Exam (Bulk)
`POST /exams/submit`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "attempt_id": 5,
  "answers": [
    {"question_id": 101, "selected_option_id": 202},
    {"question_id": 102, "selected_option_id": 205}
  ]
}
```

**Response `200`:**
```json
{
  "id": 3,
  "attempt_id": 5,
  "total_questions": 30,
  "correct_answers": 22,
  "total_marks": 30.0,
  "obtained_marks": 22.0,
  "percentage": 73.3,
  "passed": true,
  "evaluated_at": "2026-04-22T11:00:00Z"
}
```

---

### 4.6 Get Exam Result
`GET /exams/result?exam_id={id}`  
🔒 **Auth Required**

Returns the most recent result for a given exam.

**Response `200`:** Same shape as submit response.

---

### 4.7 List Monthly Exams
`GET /exams/monthly`  
🔒 **Auth Required**

**Response `200`:**
```json
[
  {
    "id": 1,
    "course_id": 1,
    "month_number": 1,
    "exam": {
      "id": 10,
      "title": "Month 1 Assessment",
      "duration_minutes": 45,
      "passing_score": 60.0,
      "max_attempts": 3,
      "is_active": true,
      "exam_type": "monthly"
    }
  }
]
```

---

### 4.8 Pay Exam Fee
`POST /exams/pay`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "exam_id": 10,
  "amount": 50.0
}
```

**Response `200`:**
```json
{ "message": "Payment processed successfully" }
```

| Status | Meaning |
|---|---|
| `200` | Payment processed |
| `404` | Invalid exam ID |

---

### 4.9 Start Course Exam (with Device Lock)
`POST /exams/course/start?exam_id={id}`  
🔒 **Auth Required**

| Query Param | Type | Required |
|---|---|---|
| `exam_id` | int | ✅ |

**Request Body:**
```json
{
  "device_id": "android-device-uuid-xxxx"
}
```

**Response `200`:**
```json
{
  "attempt_id": 12,
  "exam_id": 10,
  "started_at": "2026-04-22T10:00:00Z",
  "duration_minutes": 45,
  "device_id": "android-device-uuid-xxxx"
}
```

---

### 4.10 Log Exam Violation
`POST /exams/violation`  
🔒 **Auth Required**

Used by the Android app to report proctoring violations (switching apps, multiple faces, etc.)

**Request Body:**
```json
{
  "attempt_id": 12,
  "violation_type": "multiple_faces"
}
```

**Common `violation_type` values:** `multiple_faces`, `tab_switch`, `camera_off`, `app_switch`

**Response `200`:**
```json
{ "message": "Violation logged" }
```

---

### 4.11 Camera Status Update
`POST /exams/camera-status`  
🔒 **Auth Required**

Call this periodically during exams to log camera state.

**Request Body:**
```json
{
  "attempt_id": 12,
  "camera_on": true
}
```

**Response `200`:**
```json
{ "message": "Status logged" }
```

---

### 4.12 Close Exam Session
`POST /exams/session-close`  
🔒 **Auth Required**

Call when the exam window/timer closes on the device.

**Request Body:**
```json
{
  "attempt_id": 12
}
```

**Response `200`:**
```json
{ "message": "Session closed" }
```

---

### 4.13 Get Skill Analysis
`GET /exams/results/analysis`  
🔒 **Auth Required**

Returns skill-based breakdown: strong vs weak areas with suggestions.

**Response `200`:**
```json
{
  "strong_areas": [
    {"category": "Technical Analysis", "score": 18.0, "max_score": 20.0, "percentage": 90.0}
  ],
  "weak_areas": [
    {"category": "Risk Management", "score": 4.0, "max_score": 10.0, "percentage": 40.0}
  ],
  "suggestions": [
    "Focus more on Risk Management concepts",
    "Practice position sizing exercises"
  ]
}
```

---

## 5. Offers

### 5.1 List Active Offers
`GET /offers`

No auth required.

**Response `200`:**
```json
[
  {
    "id": 1,
    "code": "LAUNCH50",
    "description": "50% off on first course",
    "discount_type": "percentage",
    "discount_value": 50.0,
    "valid_until": "2026-12-31T00:00:00Z",
    "is_active": true
  }
]
```

---

### 5.2 Apply Offer Code
`POST /offers/apply`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "code": "LAUNCH50",
  "course_id": 1
}
```

**Response `200`:**
```json
{
  "original_price": 4999.0,
  "discount_amount": 2499.5,
  "final_price": 2499.5,
  "offer_applied": "LAUNCH50"
}
```

| Status | Meaning |
|---|---|
| `200` | Offer applied |
| `404` | Invalid offer code or course |
| `400` | Offer expired or not applicable |

---

## 6. Lectures

### 6.1 List Scheduled Lectures
`GET /lectures`

No auth required. Supports filtering and pagination.

**Query Params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `course_id` | int | null | Filter by course |
| `skip` | int | 0 | Offset |
| `limit` | int | 20 | Max records |

**Response `200`:**
```json
[
  {
    "id": 1,
    "title": "Live Trading Demo",
    "course_id": 1,
    "instructor_id": 2,
    "meeting_link": "https://zoom.us/j/123456",
    "scheduled_at": "2026-04-25T10:00:00Z",
    "duration_minutes": 60,
    "is_completed": false
  }
]
```

---

### 6.2 Join a Lecture
`POST /lectures/join?lecture_id={id}`  
🔒 **Auth Required**

| Query Param | Type | Required |
|---|---|---|
| `lecture_id` | int | ✅ |

**Response `200`:**
```json
{
  "lecture_id": 1,
  "title": "Live Trading Demo",
  "meeting_link": "https://zoom.us/j/123456",
  "scheduled_at": "2026-04-25T10:00:00Z"
}
```

---

## 7. Learning Progress

### 7.1 Learning Dashboard
`GET /learning/dashboard`  
🔒 **Auth Required**

Returns full progress overview across all enrolled courses.

**Response `200`:**
```json
{
  "enrolled_courses": 3,
  "completed_lessons": 12,
  "total_lessons": 45,
  "progress_percent": 26.7,
  "courses": [
    {
      "course_id": 1,
      "course_title": "Technical Analysis Masterclass",
      "progress_percent": 40.0,
      "completed_lessons": 8,
      "total_lessons": 20
    }
  ]
}
```

---

### 7.2 Mark Lesson as Complete
`POST /learning/lesson/complete`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "course_id": 1,
  "lesson_id": 5
}
```

**Response `200`:**
```json
{
  "status": "success",
  "completed": true
}
```

| Status | Meaning |
|---|---|
| `200` | Marked as completed |
| `404` | Invalid course or lesson ID |

---

## 8. Certificates

### 8.1 Generate Certificate
`POST /certificates/generate`  
🔒 **Auth Required**

Generates certificate after course completion.

**Request Body:**
```json
{
  "course_id": 1
}
```

**Response `201`:**
```json
{
  "id": 3,
  "user_id": 1,
  "course_id": 1,
  "certificate_number": "CERT-2026-00003",
  "issued_at": "2026-04-22T12:00:00Z",
  "pdf_url": "/uploads/certificates/cert_3.pdf"
}
```

| Status | Meaning |
|---|---|
| `201` | Certificate generated |
| `400` | Course not completed yet |

---

### 8.2 View Certificate
`GET /certificates/{cert_id}`  
🔒 **Auth Required**

**Response `200`:** Certificate metadata object (same shape as generate response).

---

### 8.3 Download Certificate PDF
`GET /certificates/download/{cert_id}`  
🔒 **Auth Required**

Returns raw PDF binary file with `Content-Type: application/pdf`.

> **Android Note:** Use a `FileOutputStream` or open in a PDF viewer intent.

| Status | Meaning |
|---|---|
| `200` | PDF file returned |
| `403` | Certificate belongs to another user |
| `404` | Certificate not found |

---

## 9. Trading Simulator

### 9.1 Get Simulator Profiles
`GET /simulator/profiles`  
🔒 **Auth Required**

Returns available prop-firm simulator challenge profiles.

**Response `200`:**
```json
[
  {
    "id": 1,
    "name": "Starter Challenge",
    "description": "5% drawdown limit, 10% profit target",
    "initial_balance": 10000.0,
    "daily_loss_limit": 5.0,
    "max_position_size": 0.1,
    "stop_loss_required": true,
    "is_active": true
  }
]
```

---

### 9.2 Start Simulator Account
`POST /simulator/start`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "profile_id": 1
}
```

**Response `201`:**
```json
{
  "id": 1,
  "user_id": 3,
  "profile_id": 1,
  "balance": 10000.0,
  "initial_balance": 10000.0,
  "is_active": true,
  "created_at": "2026-04-22T10:00:00Z"
}
```

---

### 9.3 Open a Trade
`POST /simulator/trade`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "symbol": "EURUSD",
  "side": "buy",
  "quantity": 1.0,
  "price": 1.0825,
  "stop_loss": 1.0800,
  "take_profit": 1.0900
}
```

| Field | Type | Required | Rules |
|---|---|---|---|
| `symbol` | string | ✅ | max 20 chars |
| `side` | string | ✅ | `buy` or `sell` |
| `quantity` | float | ✅ | > 0 |
| `price` | float | ✅ | > 0 |
| `stop_loss` | float | ❌ | — |
| `take_profit` | float | ❌ | — |

**Response `201`:** Trade object.

---

### 9.4 Close a Position
`POST /simulator/close`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "position_id": 7,
  "exit_price": 1.0895
}
```

**Response `200`:** Updated trade object with `pnl` and `closed_at` populated.

---

### 9.5 Get Open Positions
`GET /simulator/positions`  
🔒 **Auth Required**

**Response `200`:**
```json
[
  {
    "id": 7,
    "account_id": 1,
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": 1.0,
    "entry_price": 1.0825,
    "current_price": 1.0860,
    "unrealized_pnl": 35.0,
    "stop_loss": 1.0800,
    "take_profit": 1.0900,
    "opened_at": "2026-04-22T10:15:00Z"
  }
]
```

---

### 9.6 Get Trade History
`GET /simulator/trades`  
🔒 **Auth Required**

**Response `200`:** Array of closed trade objects including `pnl` and `closed_at`.

---

### 9.7 Get Performance Metrics
`GET /simulator/performance`  
🔒 **Auth Required**

**Response `200`:**
```json
{
  "total_trades": 50,
  "winning_trades": 32,
  "losing_trades": 18,
  "total_pnl": 1250.75,
  "win_rate": 64.0,
  "avg_win": 85.5,
  "avg_loss": -42.3,
  "max_drawdown": 350.0,
  "risk_score": 72.5,
  "consistency_score": 68.0,
  "computed_at": "2026-04-22T11:00:00Z"
}
```

---

## 10. Placement

### 10.1 Get Placement Status
`GET /placement/status`  
🔒 **Auth Required**

**Response `200`:**
```json
{
  "is_eligible": false,
  "reason": "Minimum 60% win rate required. Current: 54%",
  "requirements_met": {
    "certificate": true,
    "simulator_score": false,
    "exam_passed": true
  }
}
```

---

### 10.2 Request Placement Evaluation
`POST /placement/evaluate`  
🔒 **Auth Required**

No request body required.

**Response `200`:**
```json
{
  "evaluated": true,
  "eligible": false,
  "score": 58.5,
  "threshold": 70.0,
  "next_evaluation_at": "2026-05-22T00:00:00Z"
}
```

---

## 11. Feedback

### 11.1 Submit Feedback
`POST /feedback`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "rating": 5,
  "comments": "The trading simulator is very realistic!",
  "course_id": 1
}
```

**Response `201`:**
```json
{
  "id": 12,
  "user_id": 3,
  "course_id": 1,
  "rating": 5,
  "comments": "The trading simulator is very realistic!",
  "created_at": "2026-04-22T11:00:00Z"
}
```

---

### 11.2 Get My Feedback
`GET /feedback/my`  
🔒 **Auth Required**

**Response `200`:** Array of feedback objects submitted by the current user.

---

## 12. AI Chatbot

### 12.1 Ask a Question
`POST /ai/ask`  
🔒 **Auth Required**

**Request Body:**
```json
{
  "question": "What is the RSI indicator and how do I use it?",
  "session_id": "uuid-session-abc123",
  "course_id": 1
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `question` | string | ✅ | User's question |
| `session_id` | string | ❌ | Continue an existing chat session |
| `course_id` | int | ❌ | Context-specific course |

**Response `200`:**
```json
{
  "answer": "RSI (Relative Strength Index) is a momentum oscillator...",
  "session_id": "uuid-session-abc123",
  "sources": ["Module 3 - Lesson 2", "Technical Analysis Guide"]
}
```

---

### 12.2 Get Chat History
`GET /ai/chat-history`  
🔒 **Auth Required**

**Response `200`:**
```json
{
  "sessions": [
    {
      "id": "uuid-session-abc123",
      "created_at": "2026-04-22T10:00:00Z",
      "messages": [
        {"role": "user", "content": "What is RSI?", "timestamp": "2026-04-22T10:01:00Z"},
        {"role": "assistant", "content": "RSI is...", "timestamp": "2026-04-22T10:01:05Z"}
      ]
    }
  ]
}
```

---

### 12.3 Get FAQs
`GET /ai/faqs`  
🔒 **Auth Required**

Returns dynamically generated FAQs.

**Response `200`:**
```json
[
  {
    "id": 1,
    "question": "How do I start paper trading?",
    "answer": "Go to the Simulator section and click 'Start Account'..."
  }
]
```

---

## 13. Faculty APIs *(Role: faculty)*

> All endpoints require `Authorization: Bearer <token>` from a **faculty** user.

### 13.1 Get My Courses
`GET /faculty/courses`

**Response `200`:** Array of course detail objects (same shape as `GET /courses/{id}`).

---

### 13.2 Upload a Lesson
`POST /faculty/lessons/upload`

**Request Body:**
```json
{
  "module_id": 3,
  "title": "Advanced Chart Patterns",
  "content": "In this lesson we cover...",
  "content_type": "text",
  "content_url": "https://...",
  "order": 4,
  "is_published": true
}
```

**Response `201`:** Lesson object.

---

### 13.3 Create a Lecture
`POST /faculty/lectures/create`

**Request Body:**
```json
{
  "title": "Live Trading Q&A Session",
  "course_id": 1,
  "meeting_link": "https://zoom.us/j/987654",
  "scheduled_at": "2026-04-30T14:00:00Z",
  "duration_minutes": 90
}
```

**Response `201`:** Lecture object.

---

### 13.4 Mark Lecture as Complete
`POST /faculty/lectures/{lecture_id}/complete`

| Path Param | Type |
|---|---|
| `lecture_id` | int |

**Response `200`:** Updated lecture object with `is_completed: true`.

---

### 13.5 Add Lecture Recording
`POST /faculty/lectures/{lecture_id}/recordings`

| Path Param | Type |
|---|---|
| `lecture_id` | int |

**Request Body:**
```json
{
  "recording_url": "https://zoom.us/recordings/abc123",
  "duration_minutes": 90
}
```

**Response `201`:** Recording object.

---

### 13.6 Get Students
`GET /faculty/students`

**Response `200`:**
```json
[
  {
    "student_id": 3,
    "student_name": "John Doe",
    "student_email": "john@example.com",
    "course_id": 1,
    "course_title": "Technical Analysis Masterclass",
    "enrolled_at": "2026-04-01T10:00:00Z"
  }
]
```

---

### 13.7 Get Faculty Reports
`GET /faculty/reports`

**Response `200`:** Aggregated performance data across faculty's courses and students.

---

## 14. Distributor APIs *(Role: distributor)*

> All endpoints require `Authorization: Bearer <token>` from a **distributor** user.

### 14.1 Get My Profile
`GET /distributor/profile`

**Response `200`:**
```json
{
  "id": 1,
  "user_id": 5,
  "region": "Maharashtra",
  "referral_code": "REGION123",
  "discount_percentage": 10.0,
  "user_name": "Regional Partner",
  "user_email": "dist@partner.com",
  "created_at": "2026-03-14T10:00:00Z"
}
```

---

### 14.2 Get Referral Code
`GET /distributor/referral-code`

**Response `200`:**
```json
{
  "referral_code": "REGION123",
  "discount_percentage": 10.0,
  "region": "Maharashtra"
}
```

---

### 14.3 Get Referrals List
`GET /distributor/referrals`

**Response `200`:**
```json
[
  {
    "id": 1,
    "student_id": 3,
    "student_name": "John Doe",
    "student_email": "john@example.com",
    "course_id": 1,
    "course_title": "Technical Analysis Masterclass",
    "created_at": "2026-04-01T10:00:00Z"
  }
]
```

---

### 14.4 Get My Stats
`GET /distributor/stats`

**Response `200`:**
```json
{
  "distributor_id": 1,
  "region": "Maharashtra",
  "referral_code": "REGION123",
  "total_students_referred": 25,
  "total_courses_purchased": 40,
  "total_revenue_generated": 175000.0
}
```

---

## 15. Admin APIs *(Role: admin)*

> All endpoints require `Authorization: Bearer <token>` from an **admin** user.
> **Default Admin Credentials** (seed): `admin@platform.com` / `admin123!`

---

### 15.1 Dashboard Stats
`GET /admin/stats`

**Response `200`:**
```json
{
  "total_users": 150,
  "total_courses": 5,
  "total_enrollments": 320,
  "total_exams": 3,
  "total_lectures": 12,
  "total_distributors": 8
}
```

---

### 15.2 Analytics Reports
`GET /admin/reports`

**Response `200`:** Aggregated student analytics data.

---

### 15.3 Certificate Stats
`GET /admin/certificates`

**Response `200`:** Overview of issued certificates and recent list.

---

### 15.4 Simulator Overview
`GET /admin/simulator`

**Response `200`:** Simulator usage stats and top performing traders.

---

### 15.5 List All Users
`GET /admin/users`

| Query Param | Default |
|---|---|
| `skip` | 0 |
| `limit` | 50 |

**Response `200`:** `{ "users": [...], "total": 150 }`

---

### 15.6 Create Admin Account
`POST /admin/users/create-admin`

**Request Body:**
```json
{
  "email": "admin2@platform.com",
  "full_name": "Admin Two",
  "password": "secureAdmin123",
  "phone": "+910000000001"
}
```

**Response `201`:** User object with `admin` role.

---

### 15.7 Create Faculty Account
`POST /admin/users/create-faculty`

**Request Body:**
```json
{
  "email": "faculty@platform.com",
  "full_name": "Prof. Smith",
  "password": "secureFaculty123",
  "phone": "+910000000002"
}
```

**Response `201`:** User object with `faculty` role.

---

### 15.8 Create Distributor Account
`POST /admin/users/create-distributor`

**Request Body:**
```json
{
  "email": "dist@partner.com",
  "full_name": "Regional Partner",
  "password": "secureDist123",
  "phone": "+910000000003",
  "region": "Maharashtra",
  "referral_code": "REGION123",
  "discount_percentage": 10.0
}
```

**Response `201`:** User object with `distributor` role.

---

### 15.9 List All Distributors
`GET /admin/distributors`

**Response `200`:** Array of distributor profiles.

---

### 15.10 Get Distributor Stats
`GET /admin/distributors/{distributor_id}/stats`

**Response `200`:** Same shape as `GET /distributor/stats`.

---

### 15.11 Create Course
`POST /admin/courses`

**Request Body:**
```json
{
  "title": "Options Trading Fundamentals",
  "description": "Learn how to trade options...",
  "price": 5999.0,
  "thumbnail_url": "https://...",
  "is_published": false
}
```

**Response `201`:** Full course detail object.

---

### 15.12 Create Module
`POST /admin/modules`

**Request Body:**
```json
{
  "course_id": 2,
  "title": "Module 1: Options Basics",
  "description": "...",
  "order": 1
}
```

**Response `201`:** Module object.

---

### 15.13 Create Lesson
`POST /admin/lessons`

**Request Body:**
```json
{
  "module_id": 5,
  "title": "What is a Call Option?",
  "content": "A call option gives the buyer the right...",
  "content_type": "text",
  "content_url": null,
  "order": 1,
  "is_published": true
}
```

**Response `201`:** Lesson object.

---

### 15.14 Upload Media File
`POST /admin/upload`  
*(multipart/form-data)*

Used to upload video/audio files for lessons.

**Form Field:** `file` (binary)

**Response `201`:**
```json
{ "url": "/uploads/a1b2c3d4-uuid.mp4" }
```

---

### 15.15 Create Entrance Exam
`POST /admin/exams/create`

**Request Body:**
```json
{
  "title": "Financial Markets Entry Test",
  "description": "...",
  "course_id": 1,
  "duration_minutes": 60,
  "passing_score": 60.0,
  "is_active": true,
  "questions": [
    {
      "question_text": "What is a bull market?",
      "question_type": "mcq",
      "marks": 1.0,
      "order": 1,
      "explanation": "A bull market is...",
      "options": [
        {"option_text": "Rising prices", "is_correct": true, "order": 1},
        {"option_text": "Falling prices", "is_correct": false, "order": 2}
      ]
    }
  ]
}
```

**Response `201`:** Exam object.

---

### 15.16 Create Course Exam
`POST /admin/exams/course-create`

**Request Body:**
```json
{
  "title": "Month 1 Assessment",
  "course_id": 1,
  "module_id": 3,
  "exam_type": "monthly",
  "duration_minutes": 45,
  "passing_score": 60.0,
  "max_attempts": 3,
  "is_active": true,
  "questions": []
}
```

**`exam_type` values:** `course_final`, `monthly`, `module`

**Response `201`:** Course exam object.

---

### 15.17 Update Entrance Exam
`PUT /admin/exams/{exam_id}`

**Request Body (all fields optional):**
```json
{
  "title": "Updated Exam Title",
  "duration_minutes": 90,
  "passing_score": 70.0,
  "is_active": false
}
```

**Response `200`:** Updated exam object.

---

### 15.18 Update Course Exam
`PUT /admin/course-exams/{exam_id}`

Same request body as Update Entrance Exam.

**Response `200`:** Updated course exam object.

---

### 15.19 List All Exams
`GET /admin/exams/all`

**Response `200`:**
```json
{
  "entrance_exams": [
    {"id": 1, "title": "...", "duration_minutes": 60, "passing_score": 60.0, "is_active": true, "questions_count": 30, "type": "entrance"}
  ],
  "course_exams": [
    {"id": 10, "title": "...", "duration_minutes": 45, "passing_score": 60.0, "is_active": true, "questions_count": 20, "type": "monthly", "course_id": 1, "module_id": 3}
  ]
}
```

---

### 15.20 Add Questions to Existing Exam
`POST /admin/exams/questions?exam_id={id}`

**Request Body:** Array of question objects.
```json
[
  {
    "question_text": "Define leverage in trading.",
    "question_type": "mcq",
    "marks": 2.0,
    "order": 5,
    "options": [
      {"option_text": "Borrowing to amplify returns", "is_correct": true, "order": 1},
      {"option_text": "Reducing risk exposure", "is_correct": false, "order": 2}
    ]
  }
]
```

**Response `201`:**
```json
{ "message": "Added 1 questions to exam 1" }
```

---

### 15.21 Create Offer
`POST /admin/offers`

**Request Body:**
```json
{
  "code": "SUMMER25",
  "description": "25% off this summer",
  "discount_type": "percentage",
  "discount_value": 25.0,
  "valid_until": "2026-08-31T23:59:59Z",
  "is_active": true
}
```

**Response `201`:** Offer object.

---

### 15.22 List All Offers (Including Inactive)
`GET /admin/offers`

**Response `200`:** Array of all offers.

---

### 15.23 Schedule a Lecture
`POST /admin/lectures`

**Request Body:**
```json
{
  "title": "Special Market Analysis Session",
  "course_id": 1,
  "instructor_id": 2,
  "meeting_link": "https://meet.google.com/abc-xyz",
  "scheduled_at": "2026-05-01T10:00:00Z",
  "duration_minutes": 120
}
```

**Response `201`:** Lecture object.

---

### 15.24 Manage Announcements (Admin)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/admin/announcements` | List all (including inactive) |
| `POST` | `/dashboard/admin/announcements` | Create new |
| `PUT` | `/dashboard/admin/announcements/{ann_id}` | Update |
| `DELETE` | `/dashboard/admin/announcements/{ann_id}` | Delete |

**POST Request Body:**
```json
{
  "title": "Platform Maintenance Tonight",
  "content": "Scheduled downtime from 2 AM to 4 AM IST.",
  "is_active": true
}
```

---

### 15.25 Manage Advertisements (Admin)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/admin/advertisements` | List all (including inactive) |
| `POST` | `/dashboard/admin/advertisements` | Create new |
| `PUT` | `/dashboard/admin/advertisements/{ad_id}` | Update |
| `DELETE` | `/dashboard/admin/advertisements/{ad_id}` | Delete |

**POST Request Body:**
```json
{
  "title": "Refer & Earn",
  "image_url": "https://...",
  "link_url": "https://...",
  "placement": "banner",
  "is_active": true
}
```

---

### 15.26 List All Feedback (Admin)
`GET /feedback`  
*(Role: admin)*

**Response `200`:** Array of all feedback submissions from all users.

---

## 16. Error Reference

All error responses share this shape:
```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Status | Meaning | Android Handling |
|---|---|---|
| `400` | Bad Request — invalid/missing fields | Show validation toast |
| `401` | Unauthorized — invalid or expired token | Redirect to Login screen |
| `403` | Forbidden — insufficient role permissions | Show "Access Denied" screen |
| `404` | Resource not found | Show empty state / 404 screen |
| `409` | Conflict — duplicate entry (e.g. already enrolled) | Show appropriate message |
| `422` | Validation error — wrong data types | Show field-level errors |
| `500` | Internal Server Error | Show generic error, log to crash reporter |

---

## Quick Reference Table

| # | Method | Endpoint | Auth | Role |
|---|---|---|---|---|
| 1 | POST | `/auth/register` | ❌ | — |
| 2 | POST | `/auth/login` | ❌ | — |
| 3 | GET | `/auth/me` | ✅ | Any |
| 4 | POST | `/auth/logout` | ✅ | Any |
| 5 | GET | `/dashboard/announcements` | ✅ | Any |
| 6 | GET | `/dashboard/advertisements` | ✅ | Any |
| 7 | GET | `/courses` | ❌ | — |
| 8 | GET | `/courses/enrolled` | ✅ | Any |
| 9 | GET | `/courses/{id}` | ❌ | — |
| 10 | POST | `/courses/{id}/enroll` | ✅ | Any |
| 11 | GET | `/exams/entrance` | ❌ | — |
| 12 | POST | `/exams/start` | ✅ | Any |
| 13 | GET | `/exams/questions` | ✅ | Any |
| 14 | POST | `/exams/answer` | ✅ | Any |
| 15 | POST | `/exams/submit` | ✅ | Any |
| 16 | GET | `/exams/result` | ✅ | Any |
| 17 | GET | `/exams/monthly` | ✅ | Any |
| 18 | POST | `/exams/pay` | ✅ | Any |
| 19 | POST | `/exams/course/start` | ✅ | Any |
| 20 | POST | `/exams/violation` | ✅ | Any |
| 21 | POST | `/exams/camera-status` | ✅ | Any |
| 22 | POST | `/exams/session-close` | ✅ | Any |
| 23 | GET | `/exams/results/analysis` | ✅ | Any |
| 24 | GET | `/offers` | ❌ | — |
| 25 | POST | `/offers/apply` | ✅ | Any |
| 26 | GET | `/lectures` | ❌ | — |
| 27 | POST | `/lectures/join` | ✅ | Any |
| 28 | GET | `/learning/dashboard` | ✅ | Any |
| 29 | POST | `/learning/lesson/complete` | ✅ | Any |
| 30 | POST | `/certificates/generate` | ✅ | Any |
| 31 | GET | `/certificates/{id}` | ✅ | Any |
| 32 | GET | `/certificates/download/{id}` | ✅ | Any |
| 33 | GET | `/simulator/profiles` | ✅ | Any |
| 34 | POST | `/simulator/start` | ✅ | Any |
| 35 | POST | `/simulator/trade` | ✅ | Any |
| 36 | POST | `/simulator/close` | ✅ | Any |
| 37 | GET | `/simulator/positions` | ✅ | Any |
| 38 | GET | `/simulator/trades` | ✅ | Any |
| 39 | GET | `/simulator/performance` | ✅ | Any |
| 40 | GET | `/placement/status` | ✅ | Any |
| 41 | POST | `/placement/evaluate` | ✅ | Any |
| 42 | POST | `/feedback` | ✅ | Any |
| 43 | GET | `/feedback/my` | ✅ | Any |
| 44 | POST | `/ai/ask` | ✅ | Any |
| 45 | GET | `/ai/chat-history` | ✅ | Any |
| 46 | GET | `/ai/faqs` | ✅ | Any |
| 47 | GET | `/faculty/courses` | ✅ | faculty |
| 48 | POST | `/faculty/lessons/upload` | ✅ | faculty |
| 49 | POST | `/faculty/lectures/create` | ✅ | faculty |
| 50 | POST | `/faculty/lectures/{id}/complete` | ✅ | faculty |
| 51 | POST | `/faculty/lectures/{id}/recordings` | ✅ | faculty |
| 52 | GET | `/faculty/students` | ✅ | faculty |
| 53 | GET | `/faculty/reports` | ✅ | faculty |
| 54 | GET | `/distributor/profile` | ✅ | distributor |
| 55 | GET | `/distributor/referral-code` | ✅ | distributor |
| 56 | GET | `/distributor/referrals` | ✅ | distributor |
| 57 | GET | `/distributor/stats` | ✅ | distributor |
| 58 | GET | `/admin/stats` | ✅ | admin |
| 59 | GET | `/admin/reports` | ✅ | admin |
| 60 | GET | `/admin/certificates` | ✅ | admin |
| 61 | GET | `/admin/simulator` | ✅ | admin |
| 62 | GET | `/admin/users` | ✅ | admin |
| 63 | POST | `/admin/users/create-admin` | ✅ | admin |
| 64 | POST | `/admin/users/create-faculty` | ✅ | admin |
| 65 | POST | `/admin/users/create-distributor` | ✅ | admin |
| 66 | GET | `/admin/distributors` | ✅ | admin |
| 67 | GET | `/admin/distributors/{id}/stats` | ✅ | admin |
| 68 | POST | `/admin/courses` | ✅ | admin/faculty |
| 69 | POST | `/admin/modules` | ✅ | admin/faculty |
| 70 | POST | `/admin/lessons` | ✅ | admin/faculty |
| 71 | POST | `/admin/upload` | ✅ | admin/faculty |
| 72 | POST | `/admin/exams/create` | ✅ | admin |
| 73 | POST | `/admin/exams/course-create` | ✅ | admin |
| 74 | PUT | `/admin/exams/{id}` | ✅ | admin |
| 75 | PUT | `/admin/course-exams/{id}` | ✅ | admin |
| 76 | GET | `/admin/exams/all` | ✅ | admin |
| 77 | POST | `/admin/exams/questions` | ✅ | admin |
| 78 | POST | `/admin/offers` | ✅ | admin |
| 79 | GET | `/admin/offers` | ✅ | admin |
| 80 | POST | `/admin/lectures` | ✅ | admin/faculty |
| 81 | GET | `/dashboard/admin/announcements` | ✅ | admin |
| 82 | POST | `/dashboard/admin/announcements` | ✅ | admin |
| 83 | PUT | `/dashboard/admin/announcements/{id}` | ✅ | admin |
| 84 | DELETE | `/dashboard/admin/announcements/{id}` | ✅ | admin |
| 85 | GET | `/dashboard/admin/advertisements` | ✅ | admin |
| 86 | POST | `/dashboard/admin/advertisements` | ✅ | admin |
| 87 | PUT | `/dashboard/admin/advertisements/{id}` | ✅ | admin |
| 88 | DELETE | `/dashboard/admin/advertisements/{id}` | ✅ | admin |
| 89 | GET | `/feedback` | ✅ | admin |
| 90 | GET | `/health` | ❌ | — |

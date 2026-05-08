from pydantic import ValidationError
from app.modules.courses.schemas import CourseCreate, CourseDetailResponse
from datetime import datetime

data = {
    "title": "My Title",
    "description": "",
    "short_description": "",
    "price": 0,
    "difficulty_level": "beginner",
    "duration_hours": 0
}

try:
    c = CourseCreate(**data)
    print("CourseCreate Valid:", c.model_dump())
except ValidationError as e:
    print("CourseCreate Error:", e)

# Test Response
response_data = {
    "id": 1,
    "title": "My Title",
    "slug": "my-title",
    "description": "",
    "short_description": "",
    "price": 0.0,
    "difficulty_level": "beginner",
    "duration_hours": 0,
    "is_published": False,
    "modules": [],
    "created_at": datetime.now()
}

try:
    r = CourseDetailResponse(**response_data)
    print("CourseDetailResponse Valid:", r.model_dump())
except ValidationError as e:
    print("CourseDetailResponse Error:", e)

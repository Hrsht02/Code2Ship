from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now_utc():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    profile_image: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default="student")
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    visits: Mapped[int] = mapped_column(Integer, default=1)
    student_profile: Mapped["StudentProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    class_year: Mapped[str | None] = mapped_column(String(100), nullable=True)
    school_college: Mapped[str | None] = mapped_column(String(250), nullable=True)
    registration_status: Mapped[str] = mapped_column(String(30), default="pending")
    user: Mapped[User] = relationship(back_populates="student_profile")

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(80), default="Beginner")
    status: Mapped[str] = mapped_column(String(30), default="published")
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    status: Mapped[str] = mapped_column(String(30), default="active")
    progress: Mapped[float] = mapped_column(Float, default=0)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    lesson_type: Mapped[str] = mapped_column(String(50), default="lesson")
    position: Mapped[int] = mapped_column(Integer, default=0)
    published: Mapped[bool] = mapped_column(Boolean, default=True)

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(200))
    instructions: Mapped[str] = mapped_column(Text, default="")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_marks: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    answer: Mapped[str] = mapped_column(Text, default="")
    file_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="submitted")
    marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Announcement(Base):
    __tablename__ = "announcements"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    audience: Mapped[str] = mapped_column(String(30), default="all")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

class Attendance(Base):
    __tablename__ = "attendance"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    present: Mapped[bool] = mapped_column(Boolean, default=False)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

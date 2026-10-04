from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .auth import router as auth_router, get_current_user
from .config import settings
from .database import Base, engine, get_db
from .models import (
    User, StudentProfile, Course, Enrollment, Lesson, Assignment, Submission,
    Announcement, Attendance, ActivityLog
)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Cod2Ship LMS API", version="1.0.0")

allowed_origins = [origin.strip().rstrip("/") for origin in settings.frontend_url.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["Content-Type","Authorization"]
)
app.include_router(auth_router)

def role_required(user: User, *roles):
    if user.role not in roles:
        raise HTTPException(403, "Insufficient permissions")

def iso(value):
    return value.isoformat() if value else None

@app.get("/health")
def health():
    return {"status":"ok","service":"cod2ship-api","environment":settings.environment}

@app.get("/config/registration-form")
def registration_form():
    if settings.google_form_url:
        return RedirectResponse(settings.google_form_url)
    return {"configured":False,"message":"Registration form is not configured yet. Ask an admin to configure GOOGLE_FORM_URL."}

@app.post("/api/code/run")
async def run_code(data: dict, user: User = Depends(get_current_user)):
    role_required(user, "student", "teacher", "admin")
    language = str(data.get("language", "")).lower()
    code = str(data.get("code", ""))
    stdin = str(data.get("stdin", ""))
    if language not in {"python", "cpp", "java", "javascript"}:
        raise HTTPException(400, "Unsupported language")
    if not code.strip():
        raise HTTPException(400, "Code cannot be empty")
    if len(code) > 50000 or len(stdin) > 10000:
        raise HTTPException(413, "Code or input is too large")
    if not settings.code_executor_url:
        raise HTTPException(503, "Code runner is not configured")
    import httpx
    headers = {"X-Executor-Key": settings.code_executor_key} if settings.code_executor_key else {}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                settings.code_executor_url.rstrip("/") + "/run",
                json={"language": language, "code": code, "stdin": stdin},
                headers=headers,
            )
        if response.status_code >= 500:
            raise HTTPException(503, "Code runner unavailable")
        if response.status_code >= 400:
            detail = response.json().get("detail", "Code execution failed")
            raise HTTPException(response.status_code, detail)
        return response.json()
    except httpx.TimeoutException:
        raise HTTPException(504, "Execution timed out")
    except httpx.HTTPError:
        raise HTTPException(503, "Code runner unavailable")

@app.get("/api/bootstrap")
def bootstrap(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == "admin":
        stats = {
            "students": db.query(User).filter(User.role=="student").count(),
            "teachers": db.query(User).filter(User.role=="teacher").count(),
            "pending": db.query(StudentProfile).filter(StudentProfile.registration_status=="pending").count(),
            "courses": db.query(Course).count(),
            "assignments": db.query(Assignment).count(),
        }
        return {"user":user_payload(user), "stats":stats, "announcements":announcements_for(db,user)}
    if user.role == "teacher":
        courses = db.query(Course).filter(Course.teacher_id==user.id).all()
        course_ids=[c.id for c in courses]
        pending = db.query(Submission).filter(Submission.assignment_id.in_(
            db.query(Assignment.id).filter(Assignment.course_id.in_(course_ids))
        ), Submission.status=="submitted").count() if course_ids else 0
        return {"user":user_payload(user),"courses":[course_payload(c) for c in courses],"pending_submissions":pending,"announcements":announcements_for(db,user)}
    enrollments=db.query(Enrollment).filter(Enrollment.student_id==user.id).all()
    courses=[db.get(Course,e.course_id) for e in enrollments]
    assignments=db.query(Assignment).filter(Assignment.course_id.in_([c.id for c in courses])).all() if courses else []
    return {"user":user_payload(user),"courses":[course_payload(c, next((e.progress for e in enrollments if e.course_id==c.id),0)) for c in courses],"assignments":[assignment_payload(a,db,user.id) for a in assignments],"announcements":announcements_for(db,user)}

def user_payload(u):
    return {"id":u.id,"name":u.name,"email":u.email,"profile_image":u.profile_image,"role":u.role,"status":u.status,
            "registration_status":u.student_profile.registration_status if u.student_profile else "approved"}

def course_payload(c,progress=0):
    return {"id":c.id,"title":c.title,"code":c.code,"description":c.description,"level":c.level,"status":c.status,"teacher_id":c.teacher_id,"progress":progress}

def assignment_payload(a,db,student_id=None):
    sub=None
    if student_id:
        sub=db.query(Submission).filter(Submission.assignment_id==a.id,Submission.student_id==student_id).first()
    return {"id":a.id,"course_id":a.course_id,"title":a.title,"instructions":a.instructions,"due_at":iso(a.due_at),"max_marks":a.max_marks,
            "submission":None if not sub else {"id":sub.id,"status":sub.status,"marks":sub.marks,"feedback":sub.feedback,"submitted_at":iso(sub.submitted_at)}}

def announcements_for(db,user):
    rows=db.query(Announcement).order_by(Announcement.created_at.desc()).limit(20).all()
    return [{"id":a.id,"title":a.title,"body":a.body,"audience":a.audience,"created_at":iso(a.created_at)} for a in rows if a.audience=="all" or a.audience==user.role]

@app.get("/api/admin/users")
def admin_users(user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    role_required(user,"admin")
    users=db.query(User).order_by(User.created_at.desc()).all()
    return [user_payload(u) for u in users]

@app.patch("/api/admin/users/{user_id}")
def admin_update_user(user_id:int, data:dict, user:User=Depends(get_current_user), db:Session=Depends(get_db)):
    role_required(user,"admin")
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,"User not found")
    if "role" in data and data["role"] in {"student","teacher","admin"}: target.role=data["role"]
    if "status" in data and data["status"] in {"active","blocked"}: target.status=data["status"]
    if "registration_status" in data and target.student_profile: target.student_profile.registration_status=data["registration_status"]
    db.add(ActivityLog(user_id=user.id,event="admin_user_update"))
    db.commit()
    return user_payload(target)

@app.get("/api/admin/courses")
def admin_courses(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"admin")
    return [course_payload(c) for c in db.query(Course).order_by(Course.title).all()]

@app.post("/api/admin/courses")
def admin_create_course(data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"admin")
    if not data.get("title") or not data.get("code"): raise HTTPException(400,"Title and code are required")
    if db.query(Course).filter(Course.code==data["code"]).first(): raise HTTPException(409,"Course code already exists")
    c=Course(title=data["title"],code=data["code"],description=data.get("description",""),level=data.get("level","Beginner"),teacher_id=data.get("teacher_id"))
    db.add(c); db.commit(); db.refresh(c); return course_payload(c)

@app.patch("/api/admin/courses/{course_id}")
def admin_update_course(course_id:int,data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"admin")
    c=db.get(Course,course_id)
    if not c: raise HTTPException(404,"Course not found")
    for key in ("title","description","level","status"):
        if key in data: setattr(c,key,data[key])
    if "teacher_id" in data:
        teacher_id=data["teacher_id"]
        teacher=db.get(User,int(teacher_id)) if teacher_id else None
        if teacher_id and (not teacher or teacher.role!="teacher"): raise HTTPException(400,"Selected user is not a teacher")
        c.teacher_id=teacher_id
    db.commit();return course_payload(c)

@app.get("/api/courses/{course_id}")
def get_course(course_id:int,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    c=db.get(Course,course_id)
    if not c: raise HTTPException(404,"Course not found")
    if user.role=="student" and not db.query(Enrollment).filter_by(student_id=user.id,course_id=course_id).first(): raise HTTPException(403,"Not enrolled")
    if user.role=="teacher" and c.teacher_id!=user.id: raise HTTPException(403,"Not your course")
    lessons=db.query(Lesson).filter(Lesson.course_id==course_id).order_by(Lesson.position).all()
    assignments=db.query(Assignment).filter(Assignment.course_id==course_id).order_by(Assignment.due_at).all()
    return {"course":course_payload(c),"lessons":[{"id":l.id,"title":l.title,"content":l.content,"type":l.lesson_type,"position":l.position} for l in lessons],
            "assignments":[assignment_payload(a,db,user.id if user.role=="student" else None) for a in assignments]}

@app.post("/api/teacher/courses/{course_id}/lessons")
def create_lesson(course_id:int,data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    c=db.get(Course,course_id)
    if not c: raise HTTPException(404,"Course not found")
    if user.role=="teacher" and c.teacher_id!=user.id: raise HTTPException(403,"Not your course")
    role_required(user,"admin","teacher")
    l=Lesson(course_id=course_id,title=data.get("title","Untitled lesson"),content=data.get("content",""),lesson_type=data.get("type","lesson"),position=data.get("position",0))
    db.add(l);db.commit();db.refresh(l);return {"id":l.id,"title":l.title,"content":l.content,"type":l.lesson_type,"position":l.position}

@app.post("/api/teacher/courses/{course_id}/assignments")
def create_assignment(course_id:int,data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    c=db.get(Course,course_id)
    if not c: raise HTTPException(404,"Course not found")
    if user.role=="teacher" and c.teacher_id!=user.id: raise HTTPException(403,"Not your course")
    role_required(user,"admin","teacher")
    due=None
    if data.get("due_at"):
        due=datetime.fromisoformat(data["due_at"].replace("Z","+00:00"))
    a=Assignment(course_id=course_id,title=data.get("title","Assignment"),instructions=data.get("instructions",""),due_at=due,max_marks=int(data.get("max_marks",100)))
    db.add(a);db.commit();db.refresh(a);return assignment_payload(a,db)

@app.post("/api/student/assignments/{assignment_id}/submit")
def submit_assignment(assignment_id:int,data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"student")
    a=db.get(Assignment,assignment_id)
    if not a: raise HTTPException(404,"Assignment not found")
    enrolled=db.query(Enrollment).filter_by(student_id=user.id,course_id=a.course_id).first()
    if not enrolled: raise HTTPException(403,"Not enrolled")
    sub=db.query(Submission).filter_by(assignment_id=a.id,student_id=user.id).first()
    if not sub: sub=Submission(assignment_id=a.id,student_id=user.id)
    sub.answer=data.get("answer","");sub.file_url=data.get("file_url");sub.status="submitted";sub.submitted_at=datetime.now()
    db.add(sub);db.commit();db.refresh(sub)
    return {"id":sub.id,"status":sub.status,"submitted_at":iso(sub.submitted_at)}

@app.get("/api/teacher/submissions")
def teacher_submissions(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"teacher","admin")
    course_ids=[c.id for c in db.query(Course).filter(Course.teacher_id==user.id).all()] if user.role=="teacher" else [c.id for c in db.query(Course).all()]
    assignments=db.query(Assignment).filter(Assignment.course_id.in_(course_ids)).all() if course_ids else []
    ids=[a.id for a in assignments]
    rows=db.query(Submission).filter(Submission.assignment_id.in_(ids)).order_by(Submission.submitted_at.desc()).all() if ids else []
    return [{"id":s.id,"assignment_id":s.assignment_id,"student_id":s.student_id,"answer":s.answer,"status":s.status,"marks":s.marks,"feedback":s.feedback,"submitted_at":iso(s.submitted_at)} for s in rows]

@app.patch("/api/teacher/submissions/{submission_id}")
def grade_submission(submission_id:int,data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"teacher","admin")
    s=db.get(Submission,submission_id)
    if not s: raise HTTPException(404,"Submission not found")
    a=db.get(Assignment,s.assignment_id);c=db.get(Course,a.course_id)
    if user.role=="teacher" and c.teacher_id!=user.id: raise HTTPException(403,"Not your course")
    s.marks=data.get("marks");s.feedback=data.get("feedback","");s.status="graded"
    db.commit();return {"ok":True}

@app.post("/api/admin/announcements")
def create_announcement(data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"admin","teacher")
    a=Announcement(title=data.get("title","Announcement"),body=data.get("body",""),audience=data.get("audience","all"),created_by=user.id)
    db.add(a);db.commit();db.refresh(a);return {"id":a.id,"title":a.title,"body":a.body,"audience":a.audience}

@app.post("/api/admin/enrollments")
def enroll_student(data:dict,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"admin")
    student=db.get(User,int(data["student_id"]));course=db.get(Course,int(data["course_id"]))
    if not student or student.role!="student" or not course: raise HTTPException(404,"Student or course not found")
    existing=db.query(Enrollment).filter_by(student_id=student.id,course_id=course.id).first()
    if existing:return {"id":existing.id,"message":"Already enrolled"}
    e=Enrollment(student_id=student.id,course_id=course.id);db.add(e);db.commit();db.refresh(e);return {"id":e.id}

@app.get("/api/admin/overview")
def admin_overview(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    role_required(user,"admin")
    return {"users":db.query(User).count(),"students":db.query(User).filter(User.role=="student").count(),"teachers":db.query(User).filter(User.role=="teacher").count(),
            "courses":db.query(Course).count(),"enrollments":db.query(Enrollment).count(),"assignments":db.query(Assignment).count(),
            "submissions":db.query(Submission).count(),"pending_students":db.query(StudentProfile).filter(StudentProfile.registration_status=="pending").count()}

@app.get("/admin/users")
def legacy_admin_users(user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    role_required(user,"admin")
    return [user_payload(u) for u in db.query(User).order_by(User.created_at.desc()).all()]

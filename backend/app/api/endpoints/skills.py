from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models import Skill
from app.schemas import schemas

router = APIRouter()

@router.get("/", response_model=List[schemas.SkillResponse])
def get_skills(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    skills = db.query(Skill).offset(skip).limit(limit).all()
    return skills

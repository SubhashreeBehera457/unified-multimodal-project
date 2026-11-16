"""
backend/api/teams.py
────────────────────
Rescue teams status and assignments.
"""
from fastapi import APIRouter
from backend.state import state_manager

router = APIRouter(prefix="/teams", tags=["Rescue Teams"])


@router.get("")
def get_teams():
    return state_manager.get_teams()

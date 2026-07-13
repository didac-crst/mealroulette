from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from mealroulette.auth.dependencies import get_current_admin
from mealroulette.db.session import get_db
from mealroulette.models.user import User
from mealroulette.schemas.backup import BackupRunPublic, BackupSettingsPublic, BackupSettingsUpdateRequest
from mealroulette.services.backup_service import BackupService

router = APIRouter(tags=["backups"])


@router.get("/export/full")
def export_full_backup(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Response:
    content = BackupService(db).export_full_json()
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="mealroulette-full-export.json"'},
    )


@router.post("/import/full")
def import_full_backup(
    payload: dict,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    BackupService(db).import_full_export(payload)
    return {"status": "imported"}


@router.post("/backups/run", response_model=list[BackupRunPublic])
def run_backup_now(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[BackupRunPublic]:
    return BackupService(db).run_manual_backup()


@router.get("/backups", response_model=list[BackupRunPublic])
def list_backups(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[BackupRunPublic]:
    return BackupService(db).list_runs()


@router.get("/backups/settings", response_model=BackupSettingsPublic)
def get_backup_settings(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> BackupSettingsPublic:
    return BackupService(db).get_settings_public()


@router.put("/backups/settings", response_model=BackupSettingsPublic)
def update_backup_settings(
    payload: BackupSettingsUpdateRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> BackupSettingsPublic:
    return BackupService(db).update_settings(payload)

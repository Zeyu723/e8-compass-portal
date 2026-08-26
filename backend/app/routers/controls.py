from fastapi import APIRouter

from app.schemas import Control

router = APIRouter(tags=["controls"])


@router.get("/controls", response_model=list[Control])
def controls() -> list[Control]:
    names = [
        "Patch Applications",
        "Patch Operating Systems",
        "Multi-factor Authentication",
        "Restrict Administrative Privileges",
        "Application Control",
        "Restrict Microsoft Office Macros",
        "User Application Hardening",
        "Regular Backups",
    ]
    return [
        Control(
            id=name.lower().replace(" ", "_").replace("-", "_"),
            name=name,  # type: ignore[arg-type]
            implemented=name == "Regular Backups",
            description="Implemented for the MVP demo." if name == "Regular Backups" else "Shown in the UI as a future-supported control.",
        )
        for name in names
    ]

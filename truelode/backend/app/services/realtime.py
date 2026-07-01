"""RealtimeService: push events to role/org Socket.IO channels."""
from app.extensions import socketio


def room_for(scope: str, key: str) -> str:
    """e.g. role:REGULATOR or org:<org_id>."""
    return f"{scope}:{key}"


def emit_event(event: str, data: dict, *, roles: list[str] | None = None,
               org_ids: list[str] | None = None) -> None:
    """Emit to specific role rooms and/or org rooms. Always to 'all' too."""
    socketio.emit(event, data, room="all")
    for r in roles or []:
        socketio.emit(event, data, room=room_for("role", r))
    for o in org_ids or []:
        socketio.emit(event, data, room=room_for("org", o))

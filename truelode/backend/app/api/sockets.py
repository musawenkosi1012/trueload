"""Socket.IO room subscriptions for live per-role/org dashboards."""
from flask_socketio import join_room

from app.extensions import socketio
from app.services.realtime import room_for


@socketio.on("connect")
def on_connect():
    join_room("all")


@socketio.on("subscribe")
def on_subscribe(data):
    """Client sends {role, account_id} after login to receive scoped events."""
    data = data or {}
    if role := data.get("role"):
        join_room(room_for("role", role))
    if account_id := (data.get("account_id") or data.get("org_id")):
        join_room(room_for("org", account_id))
    return {"subscribed": True}

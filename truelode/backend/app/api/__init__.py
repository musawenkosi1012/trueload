"""Blueprint registration for the Truelode API."""
from flask import Flask


def register_blueprints(app: Flask) -> None:
    from . import sockets  # noqa: F401  (registers socket handlers)
    from .auth import bp as auth_bp
    from .handovers import bp as handovers_bp
    from .batches import bp as batches_bp
    from .billing import bp as billing_bp
    from .dashboard import bp as dashboard_bp
    from .entitlements import bp as entitlements_bp
    from .fleet import bp as fleet_bp
    from .flags import bp as flags_bp
    from .loadtickets import bp as loadtickets_bp
    from .passport import bp as passport_bp
    from .payments import bp as payments_bp
    from .processing import bp as processing_bp
    from .registry import bp as registry_bp
    from .sampling import bp as sampling_bp
    from .staff import bp as staff_bp
    from .trips import bp as trips_bp
    from .weigh import bp as weigh_bp

    for bp in (auth_bp, registry_bp, fleet_bp, loadtickets_bp, batches_bp,
               trips_bp, flags_bp, weigh_bp, sampling_bp, processing_bp,
               passport_bp, dashboard_bp, staff_bp, billing_bp, payments_bp,
               entitlements_bp, handovers_bp):
        app.register_blueprint(bp)

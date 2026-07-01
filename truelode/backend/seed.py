"""Seed demo data: plans, accounts (individual + enterprise), sites, corridor,
vehicles, wallets and one login per role."""
from app import create_app
from app.extensions import db
from app.models.account import Account
from app.models.billing import Plan, Subscription, Wallet
from app.models.enums import AccountType, OrgType, PlanType, SiteType
from app.models.fleet import Driver, Vehicle
from app.models.route import Route
from app.models.site import Site
from app.models.user import User

# Bikita-area mine -> Norton-area plant corridor (approx lat/lng waypoints).
CORRIDOR = [[-20.08, 31.80], [-19.45, 31.40], [-18.90, 31.05],
            [-18.20, 30.85], [-17.88, 30.70]]


def _account(name, role, account_type=AccountType.ENTERPRISE, exempt=False,
             balance=0.0, plan=None):
    a = Account(name=name, account_type=account_type, primary_role=role, exempt=exempt)
    db.session.add(a)
    db.session.flush()
    db.session.add(Wallet(account_id=a.id, balance_usd=balance))
    if plan and not exempt:
        db.session.add(Subscription(account_id=a.id, plan_id=plan.id))
    return a


def _user(email, role, account, name=None, owner=True):
    u = User(email=email, name=name or role.title(), role=role,
             account_id=account.id, is_account_owner=owner)
    u.set_password("password")
    db.session.add(u)
    return u


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---- plans -------------------------------------------------------
        indiv_plan = Plan(name="Individual", plan_type=PlanType.INDIVIDUAL_FLAT,
                          flat_fee_usd=15.0)
        org_plan = Plan(name="Enterprise", plan_type=PlanType.ORG,
                        seat_fee_usd=10.0, per_batch_fee_usd=5.0)
        db.session.add_all([indiv_plan, org_plan])
        db.session.flush()

        # ---- enterprise accounts (supply-chain companies) ----------------
        mine = _account("Bikita ASM Co-op", OrgType.MINE, balance=100.0, plan=org_plan)
        trans = _account("Sango Haulage", OrgType.TRANSPORTER, balance=50.0, plan=org_plan)
        proc = _account("Norton Lithium Plant", OrgType.PROCESSOR, balance=80.0, plan=org_plan)
        buyer = _account("EU Cathode GmbH", OrgType.BUYER, balance=50.0, plan=org_plan)
        lab = _account("Harare Assay Labs", OrgType.LAB, balance=50.0, plan=org_plan)
        # ---- exempt accounts (government / platform) ---------------------
        reg = _account("Ministry of Mines / MMCZ", OrgType.REGULATOR, exempt=True)
        admin = _account("Truelode", OrgType.ADMIN, exempt=True)

        # ---- sites, corridor, fleet --------------------------------------
        mine_site = Site(name="Bikita Pit 4", type=SiteType.MINE, account_id=mine.id,
                         lat=CORRIDOR[0][0], lng=CORRIDOR[0][1])
        plant_site = Site(name="Norton Sulphate Plant", type=SiteType.PLANT,
                          account_id=proc.id, lat=CORRIDOR[-1][0], lng=CORRIDOR[-1][1])
        db.session.add_all([mine_site, plant_site])
        db.session.flush()

        db.session.add(Route(name="Bikita -> Norton", origin_site_id=mine_site.id,
                             dest_site_id=plant_site.id, path=CORRIDOR, buffer_m=2000))
        db.session.add(Vehicle(plate="ABZ-1234", tare_kg=14000, transporter_id=trans.id))
        db.session.add(Driver(name="T. Moyo", license_no="ZW-99", phone="+263770000",
                              transporter_id=trans.id))

        # ---- demo logins: <role>@truelode.test / password ----------------
        for account, role in [(mine, OrgType.MINE), (trans, OrgType.TRANSPORTER),
                              (proc, OrgType.PROCESSOR), (buyer, OrgType.BUYER),
                              (lab, OrgType.LAB), (reg, OrgType.REGULATOR),
                              (admin, OrgType.ADMIN)]:
            _user(f"{role.lower()}@truelode.test", role, account)

        # Extra ORG staff to show seat billing (active, non-owner).
        _user("driver2@truelode.test", OrgType.TRANSPORTER, trans,
              name="Second Driver", owner=False)

        # An INDIVIDUAL freelance driver account (flat fee, one user).
        freelancer = _account("Freelance Driver", OrgType.TRANSPORTER,
                              account_type=AccountType.INDIVIDUAL, balance=20.0,
                              plan=indiv_plan)
        _user("freelancer@truelode.test", OrgType.TRANSPORTER, freelancer,
              name="Solo Hauler")

        db.session.commit()
        print("Seeded. Logins: <role>@truelode.test / password")
        print("Also: freelancer@truelode.test (individual), driver2@truelode.test (org staff)")
        print(f"mine_site={mine_site.id} plant_site={plant_site.id}")


if __name__ == "__main__":
    run()

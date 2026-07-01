"""Domain enumerations as plain string constants (stored as text columns)."""


class OrgType:
    MINE = "MINE"
    TRANSPORTER = "TRANSPORTER"
    PROCESSOR = "PROCESSOR"
    BUYER = "BUYER"
    LAB = "LAB"
    REGULATOR = "REGULATOR"
    ADMIN = "ADMIN"
    ALL = (MINE, TRANSPORTER, PROCESSOR, BUYER, LAB, REGULATOR, ADMIN)


class AccountType:
    INDIVIDUAL = "INDIVIDUAL"
    ENTERPRISE = "ENTERPRISE"
    ALL = (INDIVIDUAL, ENTERPRISE)


class AccountStatus:
    ACTIVE = "ACTIVE"
    DELINQUENT = "DELINQUENT"
    SUSPENDED = "SUSPENDED"


class PlanType:
    INDIVIDUAL_FLAT = "INDIVIDUAL_FLAT"
    ORG = "ORG"


class BillingKind:
    BATCH_PAYG = "BATCH_PAYG"
    SEAT_FEE = "SEAT_FEE"
    INDIVIDUAL_FLAT = "INDIVIDUAL_FLAT"
    TOPUP = "TOPUP"
    REFUND = "REFUND"


class PaymentStatus:
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class SiteType:
    MINE = "MINE"
    PLANT = "PLANT"
    WEIGHBRIDGE = "WEIGHBRIDGE"
    LAB = "LAB"


class BatchStage:
    RAW_ORE = "RAW_ORE"
    CONCENTRATE = "CONCENTRATE"
    LI_SULPHATE = "LI_SULPHATE"
    PRODUCT = "PRODUCT"


class BatchState:
    OPEN = "OPEN"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"
    CONSUMED = "CONSUMED"


class WeighKind:
    MINE_OUT = "MINE_OUT"
    PLANT_IN = "PLANT_IN"
    PLANT_OUT = "PLANT_OUT"


class FlagType:
    OFF_ROUTE = "OFF_ROUTE"
    UNKNOWN_STOP = "UNKNOWN_STOP"
    WEIGHT_MISMATCH = "WEIGHT_MISMATCH"
    GRADE_MISMATCH = "GRADE_MISMATCH"
    YIELD_ANOMALY = "YIELD_ANOMALY"
    TAMPER = "TAMPER"


class FlagStatus:
    OPEN = "OPEN"
    CLEARED = "CLEARED"


class HandoverStatus:
    PENDING  = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

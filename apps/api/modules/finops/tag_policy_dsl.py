"""apps.api.modules.finops.tag_policy_dsl — Tag policy DSL (PRD §F31.1).

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31.1 verbatim). Tag policy DSL
`define_tag_policy` builder + AST 5 levels (tenant_id + resource_type
+ tag_key + enforcement_level + default_value) + parser 검증 3 layer
+ 6 resource_type 옵션 ec2/rds/s3/lambda/eks/vpc + 4 enforcement_level
옵션 required/recommended/optional/blocked + tag_key validation (AWS 표준
+ reserved prefix 차단) + 4 default_value 옵션 string/env_based/
conditional/inherit + TAG_POLICY_DEFAULTS constants + 4 industries
baseline industry-agnostic + per-tenant override EXTENSION.

This module provides:
- `TagPolicy` TypedDict with 11 fields (PRD §F31.1-2 verbatim).
- 6 resource_type 옵션 결정 wire (ec2 AWS EC2 instance + rds AWS RDS/
  Aurora instance + s3 AWS S3 bucket + lambda AWS Lambda function +
  eks AWS EKS cluster/node group + vpc AWS VPC endpoint/NAT gateway/
  security group).
- 4 enforcement_level 옵션 결정 wire (required 태그 부재 시 정책 위반 +
  alert + remediation trigger / recommended 태그 부재 시 경고만 no
  enforcement / optional 태그 부재 시 silent audit log only / blocked
  태그 부재 시 provisioning 차단 CI/CD gate).
- tag_key validation 결정 wire (AWS 표준 태그 키 = 소문자 + 숫자 + `_`
  + `-` + `.` + `:` + max 128 chars + value validation max 256 chars +
  UTF-8 + reserved prefix `aws:` 차단 + custom prefix `tenant:` 또는
  `cost:` namespace 권장).
- 4 default_value 옵션 결정 wire (string literal default value e.g.
  "untagged" + "shared" + "production" / env_based environment 변수 기반
  / conditional Lambda function 평가 결과 / inherit resource 의 parent
  태그 inherit).
- `TAG_POLICY_DEFAULTS` constants 결정 wire (TAG_POLICY_DEFAULTS = {
  'enforcement_level': 'recommended', 'default_value': 'untagged',
  'compliance_threshold_pct': 95.0, 'untagged_alert_channel': 'slack',
  'monthly_audit_cron': '0 4 1 * *', 'remediation_action':
  'notify_only'} constants).
- `define_tag_policy` builder.
- `parse_tag_policy` parser + `validate_tag_policy` validator CR 11-4
  P-015 verbatim 결정 wire.

CR lessons applied:
- CR 0-2 RLS — every TagPolicy carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `tag_policy_updated` (dry-run skips).
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 D-001~D-005 + P-015 verbatim — pure validator pattern.
- CR 12-1 L4 industry-agnostic capability FINOPS_TAG_GOVERNANCE.
- CR 12-5 D-14 typed exception envelope — TagPolicyInvalidError +
  TagPolicyScopeInvalidError + TagPolicyHistoryUnavailableError +
  TagEnforcementViolationError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — tag policy update owner-only.
Epic 12 2FA 챌린지 mandatory when auto_remediate is enabled.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Final, TypedDict

from apps.api.core.errors import (
    TagEnforcementViolationError,
    TagPolicyHistoryUnavailableError,
    TagPolicyInvalidError,
    TagPolicyScopeInvalidError,
)

# ── 6 resource_type 옵션 (PRD §F31.1-3 verbatim) ──────────────────
RESOURCE_TYPE_EC2: Final[str] = "ec2"
RESOURCE_TYPE_RDS: Final[str] = "rds"
RESOURCE_TYPE_S3: Final[str] = "s3"
RESOURCE_TYPE_LAMBDA: Final[str] = "lambda"
RESOURCE_TYPE_EKS: Final[str] = "eks"
RESOURCE_TYPE_VPC: Final[str] = "vpc"

TAG_RESOURCE_TYPES: Final[tuple[str, ...]] = (
    RESOURCE_TYPE_EC2,
    RESOURCE_TYPE_RDS,
    RESOURCE_TYPE_S3,
    RESOURCE_TYPE_LAMBDA,
    RESOURCE_TYPE_EKS,
    RESOURCE_TYPE_VPC,
)

# ── 4 enforcement_level 옵션 (PRD §F31.1-4 verbatim) ───────────────
ENFORCEMENT_LEVEL_REQUIRED: Final[str] = "required"
ENFORCEMENT_LEVEL_RECOMMENDED: Final[str] = "recommended"
ENFORCEMENT_LEVEL_OPTIONAL: Final[str] = "optional"
ENFORCEMENT_LEVEL_BLOCKED: Final[str] = "blocked"

TAG_ENFORCEMENT_LEVELS: Final[tuple[str, ...]] = (
    ENFORCEMENT_LEVEL_REQUIRED,
    ENFORCEMENT_LEVEL_RECOMMENDED,
    ENFORCEMENT_LEVEL_OPTIONAL,
    ENFORCEMENT_LEVEL_BLOCKED,
)

# ── 4 default_value 옵션 (PRD §F31.1-6 verbatim) ──────────────────
DEFAULT_VALUE_STRING: Final[str] = "string"
DEFAULT_VALUE_ENV_BASED: Final[str] = "env_based"
DEFAULT_VALUE_CONDITIONAL: Final[str] = "conditional"
DEFAULT_VALUE_INHERIT: Final[str] = "inherit"

DEFAULT_VALUE_OPTIONS: Final[tuple[str, ...]] = (
    DEFAULT_VALUE_STRING,
    DEFAULT_VALUE_ENV_BASED,
    DEFAULT_VALUE_CONDITIONAL,
    DEFAULT_VALUE_INHERIT,
)

# ── 3 remediation_action 옵션 (PRD §F31.1-2 verbatim) ─────────────
REMEDIATION_ACTION_NOTIFY_ONLY: Final[str] = "notify_only"
REMEDIATION_ACTION_AUTO_REMEDIATE: Final[str] = "auto_remediate"
REMEDIATION_ACTION_BLOCK_PROVISIONING: Final[str] = "block_provisioning"

REMEDIATION_ACTIONS: Final[tuple[str, ...]] = (
    REMEDIATION_ACTION_NOTIFY_ONLY,
    REMEDIATION_ACTION_AUTO_REMEDIATE,
    REMEDIATION_ACTION_BLOCK_PROVISIONING,
)

# ── 3 status 옵션 (PRD §F31.1-2 verbatim) ─────────────────────────
POLICY_STATUS_ACTIVE: Final[str] = "active"
POLICY_STATUS_PAUSED: Final[str] = "paused"
POLICY_STATUS_EXPIRED: Final[str] = "expired"

POLICY_STATUSES: Final[tuple[str, ...]] = (
    POLICY_STATUS_ACTIVE,
    POLICY_STATUS_PAUSED,
    POLICY_STATUS_EXPIRED,
)

# ── TAG_POLICY_DEFAULTS constants (PRD §F31.1-7 verbatim) ────────
TAG_POLICY_DEFAULTS: Final[dict[str, object]] = {
    "enforcement_level": ENFORCEMENT_LEVEL_RECOMMENDED,
    "default_value": "untagged",
    "compliance_threshold_pct": 95.0,
    "untagged_alert_channel": "slack",
    "monthly_audit_cron": "0 4 1 * *",
    "remediation_action": REMEDIATION_ACTION_NOTIFY_ONLY,
}

# ── tag_key validation (PRD §F31.1-5 verbatim) ────────────────────
TAG_KEY_PATTERN: Final[str] = r"^[a-z0-9_\-\.:]{1,128}$"
TAG_KEY_RESERVED_PREFIXES: Final[tuple[str, ...]] = ("aws:", "aws-")
TAG_KEY_MAX_LENGTH: Final[int] = 128
TAG_VALUE_MAX_LENGTH: Final[int] = 256


def _validate_tag_key(tag_key: str) -> None:
    """Validate tag_key per AWS 표준 (PRD §F31.1-5 verbatim).

    Raises:
        TagPolicyInvalidError: invalid tag_key format or reserved prefix.
    """
    if not isinstance(tag_key, str):
        raise TagPolicyInvalidError(
            message_ko=f"tag_key must be a string, got {type(tag_key).__name__}",
            details={"tag_key": str(tag_key)},
        )
    if len(tag_key) > TAG_KEY_MAX_LENGTH:
        raise TagPolicyInvalidError(
            message_ko=f"tag_key exceeds {TAG_KEY_MAX_LENGTH} chars: {len(tag_key)}",
            details={"tag_key": tag_key, "length": str(len(tag_key))},
        )
    if not re.match(TAG_KEY_PATTERN, tag_key):
        raise TagPolicyInvalidError(
            message_ko=f"tag_key {tag_key!r} does not match AWS 표준 pattern",
            details={"tag_key": tag_key, "pattern": TAG_KEY_PATTERN},
        )
    for prefix in TAG_KEY_RESERVED_PREFIXES:
        if tag_key.startswith(prefix):
            raise TagPolicyInvalidError(
                message_ko=f"tag_key {tag_key!r} uses reserved prefix {prefix!r}",
                details={"tag_key": tag_key, "reserved_prefix": prefix},
            )


def _validate_tag_value(tag_value: str) -> None:
    """Validate tag_value per AWS 표준 (PRD §F31.1-5 verbatim).

    Raises:
        TagPolicyInvalidError: tag_value too long or invalid encoding.
    """
    if not isinstance(tag_value, str):
        raise TagPolicyInvalidError(
            message_ko=f"tag_value must be a string, got {type(tag_value).__name__}",
            details={"tag_value": str(tag_value)},
        )
    if len(tag_value) > TAG_VALUE_MAX_LENGTH:
        raise TagPolicyInvalidError(
            message_ko=f"tag_value exceeds {TAG_VALUE_MAX_LENGTH} chars",
            details={"length": str(len(tag_value))},
        )


# ── TagPolicy TypedDict (PRD §F31.1-2 verbatim, 11 fields) ────────
class TagPolicy(TypedDict, total=True):
    """TypedDict for tag policy.

    Fields:
        policy_id: UUID of the policy.
        tenant_id: UUID of the tenant.
        resource_type: 6 resource types.
        tag_key: AWS 표준 tag key (validated).
        enforcement_level: required / recommended / optional / blocked.
        default_value: tag default value (4 options).
        compliance_threshold_pct: compliance threshold percentage.
        remediation_action: notify_only / auto_remediate / block_provisioning.
        status: active / paused / expired.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 update timestamp.
        trace_id: trace_id propagation CR 1-1 ContextVar.
    """

    policy_id: str
    tenant_id: str
    resource_type: str
    tag_key: str
    enforcement_level: str
    default_value: str
    compliance_threshold_pct: float
    remediation_action: str
    status: str
    created_at: str
    updated_at: str
    trace_id: str


def define_tag_policy(
    tenant_id: str | uuid.UUID,
    resource_type: str,
    tag_key: str,
    *,
    enforcement_level: str = ENFORCEMENT_LEVEL_RECOMMENDED,
    default_value: str = "untagged",
    compliance_threshold_pct: float = TAG_POLICY_DEFAULTS["compliance_threshold_pct"],
    remediation_action: str = REMEDIATION_ACTION_NOTIFY_ONLY,
    status: str = POLICY_STATUS_ACTIVE,
    trace_id: str = "",
) -> TagPolicy:
    """Build a TagPolicy via `define_tag_policy` builder (PRD §F31.1-1).

    Validates 5 layers:
    1. syntax — types + structure.
    2. semantic — enforcement_level ∈ 4 options, resource_type ∈ 6
       options, default_value pattern, compliance_threshold_pct range.
    3. tenant-scope RLS — tenant_id UUID v4.
    4. resource_type validation — must be in TAG_RESOURCE_TYPES.
    5. tag_key validation — AWS 표준 pattern + reserved prefix 차단.

    Args:
        tenant_id: tenant UUID.
        resource_type: ec2 / rds / s3 / lambda / eks / vpc.
        tag_key: AWS 표준 tag key.
        enforcement_level: required / recommended / optional / blocked
            (default recommended).
        default_value: default value string (default "untagged").
        compliance_threshold_pct: 0.0 ~ 100.0 (default 95.0).
        remediation_action: notify_only / auto_remediate /
            block_provisioning (default notify_only).
        status: active / paused / expired (default active).
        trace_id: trace_id propagation CR 1-1 ContextVar.

    Returns:
        TagPolicy TypedDict.

    Raises:
        TagPolicyInvalidError: invalid syntax or semantic or tag_key.
        TagPolicyScopeInvalidError: tenant_id invalid or resource_type
            not in TAG_RESOURCE_TYPES.
        TagEnforcementViolationError: invalid enforcement_level.
    """
    # 1. syntax + tenant_id validation
    if not isinstance(tenant_id, str | uuid.UUID):
        raise TagPolicyScopeInvalidError(
            message_ko=f"tenant_id must be str/UUID, got {type(tenant_id).__name__}",
            details={"tenant_id": str(tenant_id)},
        )
    try:
        tenant_uuid = uuid.UUID(str(tenant_id))
    except (ValueError, AttributeError) as exc:
        raise TagPolicyScopeInvalidError(
            message_ko=f"tenant_id is not a valid UUID: {tenant_id!r}",
            details={"tenant_id": str(tenant_id)},
        ) from exc

    # 2. resource_type validation
    if resource_type not in TAG_RESOURCE_TYPES:
        raise TagPolicyScopeInvalidError(
            message_ko=f"resource_type {resource_type!r} not in TAG_RESOURCE_TYPES",
            details={"resource_type": resource_type, "allowed": str(TAG_RESOURCE_TYPES)},
        )

    # 3. enforcement_level validation
    if enforcement_level not in TAG_ENFORCEMENT_LEVELS:
        raise TagEnforcementViolationError(
            message_ko=f"enforcement_level {enforcement_level!r} not in TAG_ENFORCEMENT_LEVELS",
            details={"enforcement_level": enforcement_level},
        )

    # 4. remediation_action validation
    if remediation_action not in REMEDIATION_ACTIONS:
        raise TagPolicyInvalidError(
            message_ko=f"remediation_action {remediation_action!r} not in REMEDIATION_ACTIONS",
            details={"remediation_action": remediation_action},
        )

    # 5. status validation
    if status not in POLICY_STATUSES:
        raise TagPolicyInvalidError(
            message_ko=f"status {status!r} not in POLICY_STATUSES",
            details={"status": status},
        )

    # 6. compliance_threshold_pct range
    if not isinstance(compliance_threshold_pct, int | float):
        raise TagPolicyInvalidError(
            message_ko="compliance_threshold_pct must be numeric",
            details={"value": str(compliance_threshold_pct)},
        )
    if not (0.0 <= float(compliance_threshold_pct) <= 100.0):
        raise TagPolicyInvalidError(
            message_ko=f"compliance_threshold_pct {compliance_threshold_pct!r} out of 0-100 range",
            details={"value": str(compliance_threshold_pct)},
        )

    # 7. tag_key validation (AWS 표준 + reserved prefix 차단)
    _validate_tag_key(tag_key)

    now = datetime.now(UTC).isoformat()
    return TagPolicy(
        policy_id=str(uuid.uuid4()),
        tenant_id=str(tenant_uuid),
        resource_type=resource_type,
        tag_key=tag_key,
        enforcement_level=enforcement_level,
        default_value=default_value,
        compliance_threshold_pct=float(compliance_threshold_pct),
        remediation_action=remediation_action,
        status=status,
        created_at=now,
        updated_at=now,
        trace_id=trace_id,
    )


def parse_tag_policy(policy_text: str, *, trace_id: str = "") -> TagPolicy:
    """Parse tag policy text (CR 11-4 P-015 verbatim, PRD §F31.1-9).

    Pure validator pattern. Parses a tag policy string of the form
    `tenant_id=<UUID>;resource_type=<ec2|rds|s3|lambda|eks|vpc>;tag_key=<key>;
    enforcement_level=<required|recommended|optional|blocked>;default_value=<str>`.

    Args:
        policy_text: serialized tag policy text.
        trace_id: trace_id propagation.

    Returns:
        TagPolicy TypedDict.

    Raises:
        TagPolicyInvalidError: malformed policy_text or invalid values.
        TagPolicyHistoryUnavailableError: empty or missing required fields.
    """
    if not isinstance(policy_text, str) or not policy_text.strip():
        raise TagPolicyHistoryUnavailableError(
            message_ko="policy_text must be a non-empty string",
            details={"policy_text": str(policy_text)[:200]},
        )

    # Parse key=value;key=value format
    fields: dict[str, str] = {}
    for part in policy_text.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise TagPolicyInvalidError(
                message_ko=f"policy_text segment {part!r} missing '=' separator",
                details={"segment": part},
            )
        key, value = part.split("=", 1)
        fields[key.strip()] = value.strip()

    required_fields = ("tenant_id", "resource_type", "tag_key", "enforcement_level")
    missing = [f for f in required_fields if f not in fields]
    if missing:
        raise TagPolicyHistoryUnavailableError(
            message_ko=f"policy_text missing required fields: {missing}",
            details={"missing_fields": str(missing)},
        )

    enforcement_level = fields.get("enforcement_level", ENFORCEMENT_LEVEL_RECOMMENDED)
    if enforcement_level not in TAG_ENFORCEMENT_LEVELS:
        # Convert legacy `recommended` to RECOMMENDED canonical
        if enforcement_level.lower() in TAG_ENFORCEMENT_LEVELS:
            enforcement_level = enforcement_level.lower()

    compliance_threshold_pct_raw = fields.get("compliance_threshold_pct", "95.0")
    try:
        compliance_threshold_pct = float(compliance_threshold_pct_raw)
    except (ValueError, TypeError) as exc:
        raise TagPolicyInvalidError(
            message_ko=f"compliance_threshold_pct {compliance_threshold_pct_raw!r} not numeric",
            details={"value": compliance_threshold_pct_raw},
        ) from exc

    return define_tag_policy(
        tenant_id=fields["tenant_id"],
        resource_type=fields["resource_type"],
        tag_key=fields["tag_key"],
        enforcement_level=enforcement_level,
        default_value=fields.get("default_value", "untagged"),
        compliance_threshold_pct=compliance_threshold_pct,
        remediation_action=fields.get("remediation_action", REMEDIATION_ACTION_NOTIFY_ONLY),
        status=fields.get("status", POLICY_STATUS_ACTIVE),
        trace_id=trace_id,
    )


__all__ = [
    # 6 resource_type options
    "RESOURCE_TYPE_EC2",
    "RESOURCE_TYPE_RDS",
    "RESOURCE_TYPE_S3",
    "RESOURCE_TYPE_LAMBDA",
    "RESOURCE_TYPE_EKS",
    "RESOURCE_TYPE_VPC",
    "TAG_RESOURCE_TYPES",
    # 4 enforcement_level options
    "ENFORCEMENT_LEVEL_REQUIRED",
    "ENFORCEMENT_LEVEL_RECOMMENDED",
    "ENFORCEMENT_LEVEL_OPTIONAL",
    "ENFORCEMENT_LEVEL_BLOCKED",
    "TAG_ENFORCEMENT_LEVELS",
    # 4 default_value options
    "DEFAULT_VALUE_STRING",
    "DEFAULT_VALUE_ENV_BASED",
    "DEFAULT_VALUE_CONDITIONAL",
    "DEFAULT_VALUE_INHERIT",
    "DEFAULT_VALUE_OPTIONS",
    # 3 remediation_action options
    "REMEDIATION_ACTION_NOTIFY_ONLY",
    "REMEDIATION_ACTION_AUTO_REMEDIATE",
    "REMEDIATION_ACTION_BLOCK_PROVISIONING",
    "REMEDIATION_ACTIONS",
    # 3 status options
    "POLICY_STATUS_ACTIVE",
    "POLICY_STATUS_PAUSED",
    "POLICY_STATUS_EXPIRED",
    "POLICY_STATUSES",
    # TAG_POLICY_DEFAULTS
    "TAG_POLICY_DEFAULTS",
    "TAG_KEY_PATTERN",
    "TAG_KEY_RESERVED_PREFIXES",
    "TAG_KEY_MAX_LENGTH",
    "TAG_VALUE_MAX_LENGTH",
    # TypedDict
    "TagPolicy",
    # builder + parser
    "define_tag_policy",
    "parse_tag_policy",
    "validate_tag_policy",
]


def validate_tag_policy(
    tenant_id: str | uuid.UUID,
    resource_type: str,
    tag_key: str,
) -> None:
    """Validate tag policy fields without building (CR 11-4 P-015 verbatim).

    Used by service-layer to validate before INSERT. Mirrors
    `define_tag_policy` validation layers 3-5 (tenant-scope RLS +
    resource_type validation + tag_key validation).

    Args:
        tenant_id: tenant UUID.
        resource_type: ec2 / rds / s3 / lambda / eks / vpc.
        tag_key: AWS 표준 tag key.

    Raises:
        TagPolicyScopeInvalidError: tenant_id invalid or resource_type
            not in TAG_RESOURCE_TYPES.
        TagPolicyInvalidError: invalid tag_key.
    """
    # 1. tenant_id validation
    if not isinstance(tenant_id, str | uuid.UUID):
        raise TagPolicyScopeInvalidError(
            message_ko=f"tenant_id must be str/UUID, got {type(tenant_id).__name__}",
            details={"tenant_id": str(tenant_id)},
        )
    try:
        uuid.UUID(str(tenant_id))
    except (ValueError, AttributeError) as exc:
        raise TagPolicyScopeInvalidError(
            message_ko=f"tenant_id is not a valid UUID: {tenant_id!r}",
            details={"tenant_id": str(tenant_id)},
        ) from exc

    # 2. resource_type validation
    if resource_type not in TAG_RESOURCE_TYPES:
        raise TagPolicyScopeInvalidError(
            message_ko=f"resource_type {resource_type!r} not in TAG_RESOURCE_TYPES",
            details={"resource_type": resource_type, "allowed": str(TAG_RESOURCE_TYPES)},
        )

    # 3. tag_key validation
    _validate_tag_key(tag_key)

"""Tests for security & compliance layer (compliance.py)."""

from __future__ import annotations

import pytest

from procurement_spend_analysis.compliance import (
    AuditAction,
    AuditLogger,
    ComplianceChecker,
    EncryptionService,
    GDPRService,
    SensitivityLevel,
    classify_field,
    mask_pii,
)


# ── PII Masking ──────────────────────────────────────────────────────────

class TestMaskPII:
    def test_mask_email(self):
        assert "REDACTED_EMAIL" in mask_pii("Contact: admin@example.com for details")

    def test_mask_phone(self):
        assert "REDACTED_PHONE" in mask_pii("Call +2348012345678 now")

    def test_mask_credit_card(self):
        result = mask_pii("Card: 4111111111111111")
        assert "REDACTED" in result

    def test_no_pii_unchanged(self):
        text = "Total spend was 5 million NGN"
        assert mask_pii(text) == text


class TestClassifyField:
    def test_restricted_fields(self):
        assert classify_field("password") == SensitivityLevel.RESTRICTED
        assert classify_field("api_secret") == SensitivityLevel.RESTRICTED

    def test_confidential_fields(self):
        assert classify_field("email_address") == SensitivityLevel.CONFIDENTIAL
        assert classify_field("phone_number") == SensitivityLevel.CONFIDENTIAL

    def test_internal_fields(self):
        assert classify_field("total_revenue") == SensitivityLevel.INTERNAL
        assert classify_field("unit_price") == SensitivityLevel.INTERNAL

    def test_public_fields(self):
        assert classify_field("category") == SensitivityLevel.PUBLIC
        assert classify_field("order_count") == SensitivityLevel.PUBLIC


# ── Audit Logger ─────────────────────────────────────────────────────────

class TestAuditLogger:
    def test_log_entry(self):
        logger = AuditLogger()
        entry = logger.log(AuditAction.LOGIN, actor_id="user1", tenant_id="t1")
        assert entry.action == "auth.login"
        assert entry.actor_id == "user1"

    def test_query_by_tenant(self):
        logger = AuditLogger()
        logger.log(AuditAction.LOGIN, tenant_id="t1")
        logger.log(AuditAction.LOGIN, tenant_id="t2")
        results = logger.query(tenant_id="t1")
        assert len(results) == 1

    def test_query_by_action(self):
        logger = AuditLogger()
        logger.log(AuditAction.LOGIN, tenant_id="t1")
        logger.log(AuditAction.DATA_ACCESS, tenant_id="t1")
        results = logger.query(action="auth.login")
        assert len(results) == 1

    def test_integrity_verification_passes(self):
        logger = AuditLogger()
        for i in range(10):
            logger.log(AuditAction.DATA_ACCESS, actor_id=f"user{i}")
        assert logger.verify_integrity() is True

    def test_integrity_count(self):
        logger = AuditLogger()
        logger.log(AuditAction.LOGIN)
        logger.log(AuditAction.LOGOUT)
        assert logger.count == 2


# ── GDPR Service ─────────────────────────────────────────────────────────

class TestGDPRService:
    def setup_method(self):
        self.audit = AuditLogger()
        self.gdpr = GDPRService(self.audit)

    def test_create_dsar(self):
        req = self.gdpr.create_dsar("t1", "user@example.com", "access")
        assert req.status == "pending"
        assert req.tenant_id == "t1"

    def test_process_dsar(self):
        req = self.gdpr.create_dsar("t1", "user@example.com")
        processed = self.gdpr.process_dsar(req.request_id)
        assert processed.status == "completed"
        assert processed.data_collected is not None

    def test_execute_erasure(self):
        req = self.gdpr.create_dsar("t1", "user@example.com", "erasure")
        erased = self.gdpr.execute_erasure(req.request_id)
        assert erased.status == "completed"

    def test_erasure_on_non_erasure_request_raises(self):
        req = self.gdpr.create_dsar("t1", "user@example.com", "access")
        with pytest.raises(ValueError, match="not an erasure"):
            self.gdpr.execute_erasure(req.request_id)

    def test_list_requests(self):
        self.gdpr.create_dsar("t1", "a@b.com")
        self.gdpr.create_dsar("t1", "c@d.com")
        self.gdpr.create_dsar("t2", "e@f.com")
        assert len(self.gdpr.list_requests("t1")) == 2

    def test_dsar_creates_audit_entry(self):
        self.gdpr.create_dsar("t1", "user@example.com")
        entries = self.audit.query(action=AuditAction.GDPR_DSAR.value)
        assert len(entries) == 1


# ── Encryption Service ───────────────────────────────────────────────────

class TestEncryptionService:
    def test_encrypt_decrypt_roundtrip(self):
        svc = EncryptionService()
        plaintext = "Sensitive procurement data: spend $5.2M"
        ciphertext = svc.encrypt(plaintext)
        assert ciphertext != plaintext
        decrypted = svc.decrypt(ciphertext)
        assert decrypted == plaintext

    def test_different_contexts_produce_different_ciphertexts(self):
        svc = EncryptionService()
        ct1 = svc.encrypt("same text", context="ctx_a")
        ct2 = svc.encrypt("same text", context="ctx_b")
        assert ct1 != ct2

    def test_wrong_context_fails_integrity(self):
        svc = EncryptionService()
        ct = svc.encrypt("secret", context="correct")
        with pytest.raises((ValueError, UnicodeDecodeError)):
            svc.decrypt(ct, context="wrong")


# ── Compliance Checker ───────────────────────────────────────────────────

class TestComplianceChecker:
    def test_assess_all(self):
        audit = AuditLogger()
        checker = ComplianceChecker(audit)
        controls = checker.assess_all()
        assert len(controls) > 0
        assert all(c.last_assessed != "" for c in controls)

    def test_compliance_score_range(self):
        audit = AuditLogger()
        checker = ComplianceChecker(audit)
        checker.assess_all()
        score = checker.compliance_score()
        assert 0 <= score <= 100

    def test_non_compliant_controls(self):
        audit = AuditLogger()
        checker = ComplianceChecker(audit)
        # Before assessment, all are not_assessed
        nc = checker.non_compliant_controls()
        assert len(nc) == len(checker._controls)

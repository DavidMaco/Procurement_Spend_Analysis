# ═══════════════════════════════════════════════════════════════════════════
# WAF (Web Application Firewall) — OWASP Top-10 protection
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_wafv2_web_acl" "main" {
  name        = "procurement-intelligence-waf"
  scope       = "REGIONAL"
  description = "WAF rules for Procurement Intelligence API"

  default_action { allow {} }

  # AWS Managed — Core Rule Set (XSS, SQLi, etc.)
  rule {
    name     = "aws-managed-common"
    priority = 1
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }
    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "waf-common"
    }
  }

  # AWS Managed — SQL Injection
  rule {
    name     = "aws-managed-sqli"
    priority = 2
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }
    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "waf-sqli"
    }
  }

  # Rate-based rule — 2000 requests per 5 minutes per IP
  rule {
    name     = "rate-limit"
    priority = 3
    action { block {} }
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "waf-rate-limit"
    }
  }

  # AWS Managed — Known Bad Inputs
  rule {
    name     = "aws-managed-bad-inputs"
    priority = 4
    override_action { none {} }
    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
      }
    }
    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "waf-bad-inputs"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "waf-main"
  }
}

resource "aws_wafv2_web_acl_association" "main" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

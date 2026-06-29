import logging
import re
from typing import Optional

from app.models import Campaign, ClaimRule, CreativeVariant
from app.models.context import CampaignAnalysisContext
from app.models.evidence import RuleViolation

logger = logging.getLogger(__name__)


class RuleEngine:
    def evaluate(self, context: CampaignAnalysisContext) -> list[RuleViolation]:
        violations: list[RuleViolation] = []

        if context.campaign is None:
            logger.warning("RuleEngine: no campaign in context")
            return violations

        claim_rules = context.claim_rules
        disclaimer_text = self._get_disclaimer_text(context)
        variants = context.campaign.creative_variants

        for variant in variants:
            text_to_check = f"{variant.headline} {variant.primary_text}".lower()

            for rule in claim_rules:
                violation = self._check_rule(rule, variant, text_to_check, disclaimer_text,
                                             context.campaign)
                if violation is not None:
                    violations.append(violation)

        logger.info("RuleEngine: %d violations found", len(violations))
        return violations

    def _check_rule(self, rule: ClaimRule, variant: CreativeVariant,
                    text: str, disclaimer_text: Optional[str],
                    campaign: Campaign) -> Optional[RuleViolation]:
        if rule.applies_when == "efficacy_claim_present":
            return self._check_efficacy_claim(rule, variant, text, disclaimer_text, campaign)

        matched_term = self._match_trigger_terms(rule, text)
        if matched_term is None:
            return None

        if rule.trigger_context:
            if not self._match_context(rule, text):
                return None

        if rule.requires_field:
            field_value = getattr(variant, rule.requires_field, None)
            if field_value:
                return None

        return RuleViolation(
            rule_id=rule.rule_id,
            severity=rule.severity,
            creative_variant=variant.variant,
            campaign_id=campaign.campaign_id,
            reason=rule.description,
            matched_text=matched_term,
        )

    def _check_efficacy_claim(self, rule: ClaimRule, variant: CreativeVariant,
                              text: str, disclaimer_text: Optional[str],
                              campaign: Campaign) -> Optional[RuleViolation]:
        efficacy_keywords = {"support", "boost", "strengthen", "improve", "enhance",
                             "energy", "immunity", "healthy", "health"}
        has_efficacy = any(kw in text for kw in efficacy_keywords)
        if not has_efficacy:
            return None

        if disclaimer_text and disclaimer_text.lower() in text:
            return None

        return RuleViolation(
            rule_id=rule.rule_id,
            severity=rule.severity,
            creative_variant=variant.variant,
            campaign_id=campaign.campaign_id,
            reason=rule.description,
            matched_text="efficacy claim present",
        )

    def _match_trigger_terms(self, rule: ClaimRule, text: str) -> Optional[str]:
        for term in rule.trigger_terms:
            pattern = re.escape(term.lower())
            if re.search(pattern, text):
                return term
        return None

    def _match_context(self, rule: ClaimRule, text: str) -> bool:
        if not rule.trigger_context:
            return True
        for ctx in rule.trigger_context:
            pattern = re.escape(ctx.lower())
            if re.search(pattern, text):
                return True
        return False

    def _get_disclaimer_text(self, context: CampaignAnalysisContext) -> Optional[str]:
        return context.disclaimer_required_text

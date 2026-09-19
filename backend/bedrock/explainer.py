"""
Bedrock explainer — generates plain-language explanation of the recommended
intervention strategy using Amazon Bedrock (Claude).

Rules:
  - Bedrock ONLY explains the recommendation already made by the deterministic engine.
  - Bedrock NEVER calculates risk, response time, bottlenecks, rankings, or decisions.
  - All numbers in the prompt come from the already-computed SimulationResult.
  - If Bedrock is unavailable, a deterministic fallback explanation is returned.
  - No AWS credentials are required for local development (fallback is used automatically).
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timezone

from engine.models import SimulationResult, InterventionResult, Bottleneck

logger = logging.getLogger(__name__)

BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-sonnet-4-20250514-v1:0"
)
BEDROCK_MAX_TOKENS = 1024


def _get_bedrock_region() -> str:
    """
    Resolve the AWS region for the Bedrock client.
    Prefers APP_AWS_REGION (set explicitly by deploy_aws.py) so that
    both DynamoDB and Bedrock always use the same application region.
    Falls back to Lambda's built-in AWS_REGION, then us-east-1.
    """
    return os.environ.get("APP_AWS_REGION") or os.environ.get("AWS_REGION", "us-east-1")


# ── Prompt construction ───────────────────────────────────────────────────────

def _build_prompt(result: SimulationResult) -> str:
    """
    Build a tightly grounded prompt that prevents hallucination.
    All numbers are injected from the deterministic simulation result.
    Bedrock is instructed not to invent numbers or make decisions.
    """
    recommended: InterventionResult = next(
        i for i in result.interventions if i.strategy == result.recommended_strategy
    )
    primary_bottleneck: Bottleneck | None = result.bottlenecks[0] if result.bottlenecks else None

    bn_text = (
        f"{primary_bottleneck.description} (severity score: {primary_bottleneck.severity_score:.2f})"
        if primary_bottleneck
        else "No critical bottleneck detected."
    )

    other_strategies = "\n".join(
        f"  - {i.label}: risk reduction {i.risk_reduction_pct:.1f}%, "
        f"response time improvement {i.response_time_improvement_minutes:.1f} min, "
        f"composite score {i.composite_score:.4f}"
        for i in result.interventions
        if i.strategy != result.recommended_strategy
    )

    return f"""You are an emergency management analyst providing a briefing to a non-technical emergency coordinator.

You have been given structured output from a deterministic {result.hazard_type.replace('_', ' ')} emergency simulation system.
Your task is to explain the recommendation in plain, clear language.

STRICT RULES — you must follow these exactly:
1. DO NOT invent, estimate, or change any numbers. Use ONLY the numbers provided below.
2. DO NOT recommend a different strategy. The recommendation has already been decided by the simulation.
3. DO NOT perform any calculations. All metrics have been pre-computed.
4. Write in plain English suitable for a non-expert coordinator.
5. Write exactly 2 to 4 paragraphs. Do not use bullet points or headers.

=== SIMULATION DATA (use these numbers only) ===

Primary bottleneck identified:
  {bn_text}

Recommended strategy: {recommended.label}
  - Average risk score (after): {recommended.avg_risk_score:.1f} / 100
  - Risk reduction: {recommended.risk_reduction_pct:.1f}%
  - Average response time improvement: {recommended.response_time_improvement_minutes:.1f} minutes
  - Bottleneck resolution score: {recommended.bottleneck_resolution_score:.2f} / 1.0
  - Resource cost: {recommended.resource_cost} units
  - Composite score: {recommended.composite_score:.4f}

Other strategies evaluated (for context only):
{other_strategies}

=== YOUR TASK ===
Write 2-4 paragraphs explaining:
1. What the primary bottleneck is and why it matters for the emergency response.
2. Why the recommended strategy ({recommended.label}) addresses this bottleneck better than the alternatives.
3. What improvements the coordinator can expect if this strategy is applied (use the numbers above).

Use plain language. Do not repeat the numbers mechanically — weave them into a coherent explanation."""


# ── Fallback explanation ──────────────────────────────────────────────────────

def _build_fallback_explanation(result: SimulationResult) -> str:
    """
    Deterministic fallback explanation built entirely from simulation data.
    Used when Bedrock is unavailable. Always returns a meaningful, data-grounded explanation.
    """
    recommended: InterventionResult = next(
        i for i in result.interventions if i.strategy == result.recommended_strategy
    )
    primary_bottleneck: Bottleneck | None = result.bottlenecks[0] if result.bottlenecks else None

    bn_sentence = (
        f"The primary constraint identified in this {result.hazard_type.replace('_', ' ')} scenario is: {primary_bottleneck.description} "
        f"(severity {primary_bottleneck.severity_score:.2f} out of 1.0)."
        if primary_bottleneck
        else "No critical single bottleneck was identified, though multiple constraints exist."
    )

    improvement_sentences = []
    if recommended.risk_reduction_pct > 0:
        improvement_sentences.append(
            f"average risk is projected to fall by {recommended.risk_reduction_pct:.1f}%"
        )
    if recommended.response_time_improvement_minutes > 0:
        improvement_sentences.append(
            f"average emergency response time improves by "
            f"{recommended.response_time_improvement_minutes:.1f} minutes"
        )
    if recommended.bottleneck_resolution_score > 0:
        improvement_sentences.append(
            f"bottleneck severity is reduced by a score of {recommended.bottleneck_resolution_score:.2f}"
        )

    improvements = (
        ", and ".join(improvement_sentences) + "."
        if improvement_sentences
        else "no significant quantitative improvement over the baseline was projected."
    )

    strategy_descriptions = {
        "baseline": "taking no additional action beyond the current deployment",
        "resource_reallocation": (
            "moving rescue teams and ambulances from lower-risk zones to the highest-risk areas, "
            "improving response capacity where it is needed most"
        ),
        "capacity_expansion": (
            "expanding shelter capacity by 20% and hospital surge capacity by 15% "
            "in the most constrained facilities, reducing overcrowding pressure"
        ),
        "combined": (
            "both reallocating resources to high-risk zones and expanding shelter and hospital capacity, "
            "addressing the emergency from multiple angles simultaneously"
        ),
    }
    strategy_desc = strategy_descriptions.get(
        recommended.strategy,
        f"applying the {recommended.label} approach"
    )

    return (
        f"{bn_sentence} "
        f"This is the most critical constraint limiting effective emergency response in the current scenario.\n\n"
        f"The simulation evaluated four intervention strategies and determined that "
        f"'{recommended.label}' achieved the highest composite score ({recommended.composite_score:.4f}), "
        f"which accounts for risk reduction (40%), bottleneck resolution (30%), "
        f"resource efficiency (20%), and response time improvement (10%). "
        f"This strategy works by {strategy_desc}.\n\n"
        f"If this strategy is applied, {improvements} "
        f"The resource cost is {recommended.resource_cost} unit(s). "
        f"These projections are based entirely on the deterministic simulation — "
        f"actual outcomes will depend on real-world conditions."
    )


# ── Public interface ──────────────────────────────────────────────────────────

def generate_explanation(result: SimulationResult) -> dict:
    """
    Attempt to generate a Bedrock explanation. Falls back to deterministic explanation
    if Bedrock is unavailable or credentials are missing.

    Returns:
        {
            "explanation": str,
            "strategy_explained": str,
            "generated_at": str,
            "fallback": bool
        }
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    # Validate: must have full simulation data before calling Bedrock
    if not result.interventions or not result.recommended_strategy:
        raise ValueError("Cannot explain: simulation result is incomplete.")

    try:
        import boto3  # only imported if available
        client = boto3.client("bedrock-runtime", region_name=_get_bedrock_region())
        prompt = _build_prompt(result)

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": BEDROCK_MAX_TOKENS,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        explanation_text = response_body["content"][0]["text"].strip()

        return {
            "explanation": explanation_text,
            "strategy_explained": result.recommended_strategy,
            "generated_at": generated_at,
            "fallback": False,
        }

    except ImportError:
        logger.info("boto3 not available — using fallback explanation (local dev mode).")
    except Exception as e:
        logger.warning(f"Bedrock call failed: {e} — using fallback explanation.")

    return {
        "explanation": _build_fallback_explanation(result),
        "strategy_explained": result.recommended_strategy,
        "generated_at": generated_at,
        "fallback": True,
    }

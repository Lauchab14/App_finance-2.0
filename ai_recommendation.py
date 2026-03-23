"""
Gemini-powered recommendation helpers for the investment analysis app.
"""

from copy import deepcopy
from math import isfinite
import json
import os

from dotenv import load_dotenv


_VARIANT_TO_VALUE = {
    "positive": "Achetable",
    "warning": "Achetable sous conditions",
    "negative": "A renegocier",
}


def _sanitize_for_model(value):
    if isinstance(value, float):
        return round(value, 4) if isfinite(value) else None
    if isinstance(value, dict):
        return {key: _sanitize_for_model(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_model(item) for item in value]
    return value


def _fallback_analysis(base_analysis: dict, model: str | None, message: str) -> dict:
    fallback = deepcopy(base_analysis)
    fallback["ai_recommended_actions"] = []
    fallback["recommendation_source"] = {
        "mode": "rules",
        "provider": "Gemini",
        "model": model,
        "message": message,
        "summary": "",
    }
    return fallback


def _recommendation_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "scenario": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["label", "summary"],
                "additionalProperties": False,
            },
            "verdict": {
                "type": "object",
                "properties": {
                    "variant": {
                        "type": "string",
                        "enum": ["positive", "warning", "negative"],
                    },
                    "note": {"type": "string"},
                },
                "required": ["variant", "note"],
                "additionalProperties": False,
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
            },
            "risks": {
                "type": "array",
                "items": {"type": "string"},
            },
            "recommended_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action_key": {
                            "type": "string",
                            "enum": ["counter_offer", "down_payment", "rent_optimization"],
                        },
                        "label": {"type": "string"},
                        "value": {"type": "string"},
                        "note": {"type": "string"},
                        "variant": {
                            "type": "string",
                            "enum": ["positive", "warning", "negative", "neutral"],
                        },
                    },
                    "required": ["action_key", "label", "value", "note", "variant"],
                    "additionalProperties": False,
                },
            },
            "agent_summary": {"type": "string"},
        },
        "required": [
            "scenario",
            "verdict",
            "strengths",
            "risks",
            "recommended_actions",
            "agent_summary",
        ],
        "additionalProperties": False,
    }


def _build_agent_prompt(base_analysis: dict, dossier_context: dict) -> str:
    safe_payload = _sanitize_for_model(
        {
            "property_context": dossier_context,
            "rule_based_analysis": {
                "scenario": base_analysis.get("scenario"),
                "verdict": base_analysis.get("verdict"),
                "strengths": base_analysis.get("strengths", []),
                "risks": base_analysis.get("risks", []),
                "actions": base_analysis.get("actions", []),
                "alerts": base_analysis.get("alerts", []),
                "targets": base_analysis.get("targets", {}),
            },
        }
    )

    instructions = (
        "Tu es un agent IA d'analyse immobiliere pour des immeubles residentiels au Quebec. "
        "Tu aides un investisseur a prendre une decision d'achat claire, prudente et argumentee. "
        "Base-toi uniquement sur les chiffres fournis. N'invente jamais de donnees manquantes. "
        "Ne promets jamais un resultat certain. "
        "Le verdict doit repondre clairement a la question: est-ce un bon achat dans les conditions actuelles, et pourquoi. "
        "Le champ verdict.variant doit respecter cette logique: "
        "positive si le dossier est achetable, warning si l'achat demande des conditions claires, "
        "negative si le dossier doit etre renegocie ou refuse dans sa forme actuelle. "
        "Les listes strengths et risks doivent contenir des points tres courts, maximum 4 elements chacune. "
        "Le champ recommended_actions doit contenir de 0 a 3 actions concretes et prioritaires. "
        "Chaque action de recommended_actions doit utiliser action_key parmi counter_offer, down_payment ou rent_optimization. "
        "Quand le dossier n'est pas clairement achetable, appuie-toi sur les actions et montants deja fournis dans le dossier "
        "pour proposer une contre-offre, une hausse de loyers ou un ajustement de mise de fonds lorsque c'est pertinent. "
        "Reprends les chiffres exacts fournis dans rule_based_analysis.actions quand ils existent. "
        "Ordonne recommended_actions de la plus realiste a la plus difficile a executer. "
        "Si le dossier est achetable, recommended_actions peut etre vide ou contenir au maximum une action de suivi prudente. "
        "Le champ agent_summary doit resumer en 2 ou 3 phrases la these d'investissement et mentionner le principal levier d'action s'il y en a un. "
        "Retourne uniquement un objet JSON valide conforme au schema."
    )

    return (
        f"{instructions}\n\n"
        "Voici le dossier a analyser:\n"
        f"{json.dumps(safe_payload, ensure_ascii=False, indent=2)}"
    )


def enrich_analysis_with_ai(base_analysis: dict, dossier_context: dict) -> dict:
    load_dotenv()

    model = os.getenv("GEMINI_RECOMMENDATION_MODEL", "gemini-2.5-flash")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return _fallback_analysis(
            base_analysis,
            model,
            "Agent IA Gemini non configure. Ajoute GEMINI_API_KEY dans le fichier .env pour activer la recommandation IA.",
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _fallback_analysis(
            base_analysis,
            model,
            "Le package google-genai n'est pas installe. Lance l'installation des dependances pour activer l'agent IA Gemini.",
        )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=_build_agent_prompt(base_analysis, dossier_context),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=_recommendation_schema(),
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        output_text = getattr(response, "text", "") or ""
        if not output_text.strip():
            raise ValueError("Reponse vide de l'agent Gemini.")

        parsed = json.loads(output_text)
        verdict_variant = parsed["verdict"]["variant"]
        enriched = deepcopy(base_analysis)
        enriched["scenario"] = {
            "label": parsed["scenario"]["label"].strip()
            or base_analysis["scenario"]["label"],
            "summary": parsed["scenario"]["summary"].strip()
            or base_analysis["scenario"]["summary"],
        }
        enriched["verdict"] = {
            "label": "Verdict IA",
            "value": _VARIANT_TO_VALUE[verdict_variant],
            "note": parsed["verdict"]["note"].strip(),
            "variant": verdict_variant,
        }

        ai_strengths = [
            item.strip() for item in parsed.get("strengths", []) if item.strip()
        ]
        ai_risks = [item.strip() for item in parsed.get("risks", []) if item.strip()]
        ai_actions = []
        for action in parsed.get("recommended_actions", []):
            action_key = action.get("action_key", "").strip()
            label = action.get("label", "").strip()
            value = action.get("value", "").strip()
            note = action.get("note", "").strip()
            variant = action.get("variant", "neutral").strip()
            if variant not in {"positive", "warning", "negative", "neutral"}:
                variant = "neutral"
            if action_key in {"counter_offer", "down_payment", "rent_optimization"} and label and value and note:
                ai_actions.append(
                    {
                        "action_key": action_key,
                        "label": label,
                        "value": value,
                        "note": note,
                        "variant": variant,
                    }
                )

        if ai_strengths:
            enriched["strengths"] = ai_strengths[:4]
        if ai_risks:
            enriched["risks"] = ai_risks[:4]
        enriched["ai_recommended_actions"] = ai_actions[:3]

        enriched["recommendation_source"] = {
            "mode": "ai",
            "provider": "Gemini",
            "model": model,
            "message": "Recommandation generee par l'agent IA Gemini.",
            "summary": parsed.get("agent_summary", "").strip(),
        }
        return enriched
    except Exception as exc:
        return _fallback_analysis(
            base_analysis,
            model,
            f"Agent Gemini indisponible pour le moment. Recommandation locale affichee. Detail: {exc}",
        )

"""
Scoring logic for the Women's Health Check.

This mirrors the scoring rules in the front-end quiz exactly, so a
submission always gets the same bands whether or not the front end's
own JS is trusted. Never trust a report generated purely client-side,
recompute it here before it is stored.
"""

MENOPAUSE_STAGES = {"Perimenopause", "Menopause", "Postmenopause"}
MATERNAL_STAGES = {"Pregnant", "Postnatal (within 2 years)"}


def _band(score: int, low_max: int, mid_max: int) -> str:
    if score <= low_max:
        return "low"
    if score <= mid_max:
        return "mid"
    return "high"


def score_menopause(answers: dict) -> str:
    symptoms = [s for s in answers.get("symptoms", []) if s != "None of these"]
    severity_map = {"Not at all": 0, "A little": 1, "Moderately": 2, "Significantly": 3}
    severity = severity_map.get(answers.get("severity"), 0)
    return _band(len(symptoms) + severity * 2, 2, 6)


def score_maternal(answers: dict) -> str:
    mood_map = {"Coping well": 0, "Some low days": 1, "Struggling more days than not": 3, "Prefer not to say": 1}
    support_map = {"Yes, plenty": 0, "Some, could use more": 1, "Very little": 2}
    sleep_map = {"Not really": 0, "Somewhat": 1, "Significantly": 2}
    score = (
        mood_map.get(answers.get("mood"), 0)
        + support_map.get(answers.get("support"), 0)
        + sleep_map.get(answers.get("sleepDisruption"), 0)
    )
    return _band(score, 1, 3)


def score_strength(answers: dict) -> str:
    strength_map = {"Never": 2, "Occasionally": 1, "1 to 2 times a week": 0, "3 or more times a week": 0}
    falls_map = {"No": 0, "One": 1, "More than one": 2}
    wb_map = {"Rarely": 2, "Sometimes": 1, "Regularly": 0}
    bone_map = {"Neither": 2, "One of these": 1, "Both": 0, "Not sure": 1}
    score = (
        strength_map.get(answers.get("strength"), 0)
        + falls_map.get(answers.get("falls"), 0)
        + wb_map.get(answers.get("weightBearing"), 0)
        + bone_map.get(answers.get("boneCheck"), 0)
    )
    return _band(score, 1, 4)


BAND_COPY = {
    "menopause": {
        "low": {
            "label": "Steady",
            "text": "Your hormone-related symptoms seem mild or well managed right now. Worth checking back in as things shift.",
            "next": ["Keep a light symptom note if anything changes", "Revisit this check in 3 to 6 months"],
        },
        "mid": {
            "label": "Worth a closer look",
            "text": "You're noticing a real mix of symptoms that are starting to affect daily life. There's a lot that can help here.",
            "next": ["Talk through symptom relief options with a practitioner", "Ask about hormone testing if you haven't had it done"],
        },
        "high": {
            "label": "A focus area",
            "text": "Your symptoms are significantly affecting daily life right now. This is very treatable, and worth prioritising.",
            "next": ["Book a consultation to discuss options, including HRT", "Ask about hormone testing to build a full picture"],
        },
    },
    "maternal": {
        "low": {
            "label": "Coping",
            "text": "You're managing well right now. This stage can shift quickly, so it's worth checking in with yourself regularly.",
            "next": ["Keep leaning on the support around you", "Revisit this if anything changes"],
        },
        "mid": {
            "label": "Some strain showing",
            "text": "There are signs you're under more strain than you'd like to be. That's common, and support helps.",
            "next": ["Talk to your GP or health visitor about how you're feeling", "Ask for more practical support where you can"],
        },
        "high": {
            "label": "Worth talking to someone",
            "text": "What you've shared suggests you're finding this stage genuinely hard right now. Please don't sit with this alone.",
            "next": ["Speak with your GP or health visitor soon", "Let someone close to you know how you're actually doing"],
        },
    },
    "strength": {
        "low": {
            "label": "Strong foundation",
            "text": "Your habits and history point to good bone and strength resilience right now. Keep it up.",
            "next": ["Maintain your current strength routine", "Recheck in a year"],
        },
        "mid": {
            "label": "Some factors to watch",
            "text": "A few things here are worth paying attention to before they become bigger issues.",
            "next": ["Add weight-bearing activity a couple of times a week", "Ask about a bone density scan if you haven't had one"],
        },
        "high": {
            "label": "Worth prioritising",
            "text": "Several factors here suggest your bone health and physical resilience deserve real attention now.",
            "next": ["Book a consultation to discuss a bone density scan", "Start a structured strength routine, ideally with guidance"],
        },
    },
}

SPECIALIST_MAP = {
    "menopause": "Menopause specialist",
    "maternal": "GP or health visitor",
    "strength": "Practitioner or strength coach",
}


def build_report(life_stage: str, answers: dict) -> dict:
    """Returns the full per-track report as a plain dict, ready to store as JSON."""
    tracks = {}

    if life_stage in MENOPAUSE_STAGES:
        band = score_menopause(answers)
        tracks["menopause"] = {
            "title": "Menopause and Hormones",
            "band": band,
            **BAND_COPY["menopause"][band],
            "specialist": SPECIALIST_MAP["menopause"],
        }

    if life_stage in MATERNAL_STAGES:
        band = score_maternal(answers)
        tracks["maternal"] = {
            "title": "Maternal Wellbeing",
            "band": band,
            **BAND_COPY["maternal"][band],
            "specialist": SPECIALIST_MAP["maternal"],
        }

    band = score_strength(answers)
    tracks["strength"] = {
        "title": "Bone, Brain and Strength",
        "band": band,
        **BAND_COPY["strength"][band],
        "specialist": SPECIALIST_MAP["strength"],
    }

    return {"tracks": tracks}

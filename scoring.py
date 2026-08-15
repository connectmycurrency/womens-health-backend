"""
Scoring and content logic for the Women's Health Check.

Every band (low/mid/high) for every track carries a full content set:
summary, why it matters, expanded next steps, lifestyle tips, when to
seek help, and what to expect from the recommended specialist. This is
the authoritative source for both the account portal and the PDF, the
quiz's own on-page teaser is a lighter client-side version and does
not need to match this word for word.
"""

MENOPAUSE_STAGES = {"Perimenopause", "Menopause", "Postmenopause"}
MATERNAL_STAGES = {"Pregnant", "Postnatal (within 2 years)"}
PRECONCEPTION_STAGES = {"Trying to conceive"}

# Periods & contraception only makes sense for people who currently have,
# or could realistically expect, a period. Excludes pregnancy/postnatal
# (no periods) and Menopause/Postmenopause (periods have stopped, already
# covered by the menopause track's own periods question).
PERIODS_STAGES = {"Trying to conceive", "Perimenopause"}

# Pregnancy options (including abortion information) is relevant to
# anyone for whom pregnancy is a live possibility. Excludes Postnatal,
# Menopause, and Postmenopause.
PREGNANCY_CHOICE_STAGES = {"Trying to conceive", "Pregnant", "Perimenopause"}

# General mental health & neurodivergence track is universal except for
# pregnant/postnatal, where the dedicated Maternal Wellbeing track already
# covers mood in depth, asking twice would be redundant.
MENTAL_HEALTH_STAGES_EXCLUDE = MATERNAL_STAGES


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
    treatment_map = {"Nothing yet": 1, "Lifestyle changes": 0, "Supplements": 0, "HRT": -1, "Other": 0}
    treatment_adjust = treatment_map.get(answers.get("previousTreatment"), 0)
    return _band(len(symptoms) + severity * 2 + treatment_adjust, 2, 6)


def score_maternal(answers: dict) -> str:
    mood_map = {"Coping well": 0, "Some low days": 1, "Struggling more days than not": 3, "Prefer not to say": 1}
    support_map = {"Yes, plenty": 0, "Some, could use more": 1, "Very little": 2}
    sleep_map = {"Not really": 0, "Somewhat": 1, "Significantly": 2}
    recovery_map = {"Good": 0, "Managing": 1, "Finding it hard": 2}
    score = (
        mood_map.get(answers.get("mood"), 0)
        + support_map.get(answers.get("support"), 0)
        + sleep_map.get(answers.get("sleepDisruption"), 0)
        + recovery_map.get(answers.get("recovery"), 0)
    )
    return _band(score, 1, 4)


def score_strength(answers: dict) -> str:
    strength_map = {"Never": 2, "Occasionally": 1, "1 to 2 times a week": 0, "3 or more times a week": 0}
    falls_map = {"No": 0, "One": 1, "More than one": 2}
    wb_map = {"Rarely": 2, "Sometimes": 1, "Regularly": 0}
    bone_map = {"Neither": 2, "One of these": 1, "Both": 0, "Not sure": 1}
    calcium_map = {"Rarely": 1, "Sometimes": 0, "Regularly": 0}
    sun_map = {"Neither": 1, "One": 0, "Both": 0}
    score = (
        strength_map.get(answers.get("strength"), 0)
        + falls_map.get(answers.get("falls"), 0)
        + wb_map.get(answers.get("weightBearing"), 0)
        + bone_map.get(answers.get("boneCheck"), 0)
        + calcium_map.get(answers.get("dietCalcium"), 0)
        + sun_map.get(answers.get("sunlight"), 0)
    )
    return _band(score, 1, 5)


def score_preconception(answers: dict) -> str:
    cycle_map = {"Regular": 0, "Not sure": 1, "Irregular": 2}
    folic_map = {"Yes": 0, "Not sure": 1, "No": 2}
    lifestyle = [f for f in answers.get("lifestyleFactors", []) if f != "None of these"]
    duration_map = {"Less than 6 months": 0, "6 to 12 months": 1, "Over a year": 2}
    score = (
        cycle_map.get(answers.get("cycleRegularity"), 0)
        + folic_map.get(answers.get("folicAcid"), 0)
        + len(lifestyle)
        + duration_map.get(answers.get("tryingDuration"), 0)
    )
    return _band(score, 1, 4)


def score_periods(answers: dict) -> str:
    pain_map = {"No periods currently": 0, "Mild or manageable": 0, "Moderate, affects some days": 1, "Severe, affects daily life": 3}
    flow_map = {"No periods currently": 0, "Light": 0, "Moderate": 1, "Heavy, needs frequent changes or overnight protection": 2}
    pms_map = {"Not at all": 0, "A little": 1, "Moderately": 2, "Significantly": 3}
    score = (
        pain_map.get(answers.get("periodPain"), 0)
        + flow_map.get(answers.get("periodFlow"), 0)
        + pms_map.get(answers.get("pmsImpact"), 0)
    )
    return _band(score, 1, 4)


def score_pelvic(answers: dict) -> str:
    leak_map = {"Never": 0, "Occasionally": 1, "Regularly": 2, "Most days": 3}
    floor_map = {"Regularly": 0, "Occasionally": 0, "Never": 1, "Not sure how to": 1}
    uti_map = {"Never or rarely": 0, "Occasionally, a few times a year": 1, "Frequently, most months": 2}
    symptoms = [s for s in answers.get("pelvicSymptoms", []) if s != "None of these"]
    score = (
        leak_map.get(answers.get("bladderLeaks"), 0)
        + floor_map.get(answers.get("pelvicFloorExercise"), 0)
        + uti_map.get(answers.get("utiFrequency"), 0)
        + len(symptoms)
    )
    return _band(score, 2, 6)


def score_breast(answers: dict) -> str:
    changes_map = {"No": 0, "Yes, and I've had it checked": 0, "Yes, not checked yet": 3}
    screening_map = {"Not yet in the age range": 0, "Yes, up to date": 0, "No, overdue": 2, "Not sure": 1}
    checks_map = {"Regularly, roughly monthly": 0, "Occasionally": 0, "Rarely or never": 1}
    score = (
        changes_map.get(answers.get("breastChanges"), 0)
        + screening_map.get(answers.get("breastScreening"), 0)
        + checks_map.get(answers.get("breastChecks"), 0)
    )
    return _band(score, 1, 3)


def score_heart(answers: dict) -> str:
    family_map = {"Yes": 1, "No": 0, "Not sure": 1}
    bp_map = {"Yes, and it's normal": 0, "Yes, and it's raised": 2, "No, haven't checked recently": 1, "Not sure": 1}
    palp_map = {"No": 0, "Occasionally": 1, "Regularly": 3}
    smoking_map = {"No, never": 0, "No, but used to": 1, "Yes": 2}
    score = (
        family_map.get(answers.get("heartFamilyHistory"), 0)
        + bp_map.get(answers.get("bloodPressure"), 0)
        + palp_map.get(answers.get("palpitations"), 0)
        + smoking_map.get(answers.get("smoking"), 0)
    )
    return _band(score, 1, 4)


def score_mental_health(answers: dict) -> str:
    mood_map = {"Good, stable": 0, "Some low or anxious days": 1, "Low or anxious most days": 2, "Struggling significantly": 3}
    adhd = [t for t in answers.get("adhdTraits", []) if t != "None of these"]
    autism = [t for t in answers.get("autismTraits", []) if t != "None of these"]
    score = mood_map.get(answers.get("generalMood"), 0) + len(adhd) + len(autism)
    return _band(score, 1, 5)


def score_sexual_health(answers: dict) -> str:
    checkup_map = {"Not applicable to me": 0, "Within the last year": 0, "More than a year ago": 1, "Never, and it might be relevant": 2}
    wellbeing_map = {"Not applicable / prefer not to say": 0, "Satisfied": 0, "Some concerns": 1, "Significant concerns, e.g. pain or low desire affecting you": 2}
    symptoms = [s for s in answers.get("sexualHealthSymptoms", []) if s != "None of these"]
    score = (
        checkup_map.get(answers.get("sexualHealthCheck"), 0)
        + wellbeing_map.get(answers.get("sexualWellbeing"), 0)
        + len(symptoms)
    )
    return _band(score, 1, 4)


def score_brain(answers: dict) -> str:
    memory_map = {"No change": 0, "Slight change": 1, "Noticeable change": 2, "Significant change": 3}
    family_map = {"Yes": 2, "No": 0, "Not sure": 1}
    protective = [f for f in answers.get("brainLifestyle", []) if f != "None of these currently"]
    score = memory_map.get(answers.get("memory"), 0) + family_map.get(answers.get("brainFamilyHistory"), 0)
    if "None of these currently" in answers.get("brainLifestyle", []) or not answers.get("brainLifestyle"):
        score += 1
    else:
        score = max(0, score - min(len(protective), 2))
    return _band(score, 1, 4)


def score_blood_energy(answers: dict) -> str:
    energy_map = {"Low most days": 3, "Variable": 1, "Generally good": 0, "Consistently high": 0}
    symptoms = [s for s in answers.get("anaemiaSymptoms", []) if s != "None of these"]
    score = energy_map.get(answers.get("energy"), 0) + len(symptoms)
    if answers.get("periodFlow") == "Heavy, needs frequent changes or overnight protection":
        score += 2
    return _band(score, 1, 4)


def score_pregnancy_choices(answers: dict) -> str:
    direct_map = {
        "Not relevant to me right now": "low",
        "I already know my options and don't need more information": "low",
        "I'd find general information helpful": "mid",
        "I'd like details on accessing support now": "high",
    }
    return direct_map.get(answers.get("pregnancyOptionsInterest"), "low")


BAND_COPY = {
    "menopause": {
        "low": {
            "label": "Steady",
            "summary": "Your hormone-related symptoms seem mild or well managed right now.",
            "why_it_matters": "Perimenopause and menopause bring genuine hormonal shifts, oestrogen and progesterone levels change, which can affect sleep, mood, temperature regulation, and long-term bone and heart health. Even when symptoms are mild, this is a good stage to build habits that support you through the transition, not just react to symptoms as they appear.",
            "next_steps": [
                "Keep a light symptom note if anything changes, timing and pattern are genuinely useful if you do need to discuss this later",
                "Revisit this check in three to six months, symptoms often shift gradually",
                "Build a baseline of strength and cardiovascular exercise now, it pays off through this transition",
                "Get familiar with your family history of menopause timing and osteoporosis, if you don't know it already",
                "Consider a general health check with your GP if it's been a while, covering blood pressure, cholesterol, and bone health markers",
                "Read up on what to expect next, being informed ahead of time makes future symptoms feel less disorientating",
            ],
            "lifestyle_tips": [
                "Prioritise consistent sleep timing, even without major disruption yet, it protects you going forward",
                "Keep alcohol intake moderate, it's a common under-recognised trigger for hot flushes and disrupted sleep",
                "Stay on top of calcium and vitamin D intake for bone health",
            ],
            "when_to_seek_help": "If anything changes noticeably, heavier or more frequent symptoms, new symptoms, or anything that worries you, it's always worth a conversation rather than waiting.",
        },
        "mid": {
            "label": "Worth a closer look",
            "summary": "You're noticing a real mix of symptoms that are starting to affect daily life.",
            "why_it_matters": "A cluster of symptoms like this, hot flushes, disrupted sleep, mood changes, brain fog, usually reflects genuine hormonal fluctuation rather than something to just push through. The good news is this stage responds well to both lifestyle changes and medical options, most people who address it properly see real improvement.",
            "next_steps": [
                "Book a consultation to talk through symptom relief options, including but not limited to HRT",
                "Ask about hormone testing if you haven't had it done, it helps build a fuller picture",
                "Track your symptoms for two to three weeks before your appointment, patterns make the conversation much more useful",
                "Ask specifically about non-hormonal options too, if HRT isn't right for you there are still genuine choices",
                "Review your sleep environment, temperature regulation issues often start there",
                "Talk to people close to you about what you're experiencing, this stage is easier with support and often still under-discussed",
            ],
            "lifestyle_tips": [
                "Layer clothing and keep your bedroom cool, small changes here reduce night sweat disruption meaningfully",
                "Reduce caffeine and alcohol in the evening, both are common flush and sleep triggers",
                "Regular moderate exercise measurably reduces hot flush frequency for many people",
                "Mindfulness or breathing techniques have real evidence behind them for hot flush and mood symptoms",
            ],
            "when_to_seek_help": "If symptoms are affecting your work, relationships, or day-to-day functioning, that's already a reason to seek support, you don't need to wait until it feels unmanageable.",
        },
        "high": {
            "label": "A focus area",
            "summary": "Your symptoms are significantly affecting daily life right now.",
            "why_it_matters": "What you're describing is a genuinely difficult symptom load, and it's important to say clearly: this is very treatable. Nobody should have to just tolerate this level of disruption. Effective options exist, and getting the right support now tends to make a real, fairly fast difference.",
            "next_steps": [
                "Book a consultation as a priority to discuss options, including HRT",
                "Ask about hormone testing to build a full picture of what's happening",
                "If a previous approach hasn't worked, say so clearly, there are usually other options worth trying",
                "Ask about referral to a menopause specialist if your GP's options feel limited",
                "Bring a symptom diary to your appointment, it makes a real difference to how quickly you get the right plan",
                "Don't wait for the 'worst' symptom to raise it, the combined load matters, not just the single most severe thing",
                "Loop in people close to you, this level of symptoms is genuinely hard to carry alone",
            ],
            "lifestyle_tips": [
                "Small daily routines (consistent sleep and wake times, regular meals) help stabilise things while you get medical support in place",
                "Keep a note of what makes symptoms worse, specific foods, alcohol, stress, heat, it helps target the conversation",
                "Movement genuinely helps mood and sleep here even when motivation is low, short and frequent beats occasional and long",
            ],
            "when_to_seek_help": "Please treat this as worth addressing now rather than later, significant symptom burden at this level is exactly what medical support is for.",
        },
    },
    "maternal": {
        "low": {
            "label": "Coping",
            "summary": "You're managing well right now.",
            "why_it_matters": "Pregnancy and the postnatal period bring real physical and emotional change even when things are going well. Feeling okay now doesn't mean checking in stops mattering, this stage can shift quickly, and having a baseline for how you're doing makes it easier to notice if that changes.",
            "next_steps": [
                "Keep leaning on the support around you, it's protective even when things feel fine",
                "Revisit this check if anything changes, mood and energy in this stage can shift over weeks, not just months",
                "Stay connected with your midwife, health visitor, or GP through your normal check-ins",
                "Protect sleep where you can, it's the single biggest lever for mood in this stage",
                "Keep a small note of how you're doing week to week, it's a useful reference point for yourself",
            ],
            "lifestyle_tips": [
                "Accept practical help when it's offered, meals, childcare, errands, it genuinely protects your capacity",
                "Get outside daily if you can, even briefly, it measurably helps mood in this stage",
                "Stay connected to at least one person you can be fully honest with about how things really are",
            ],
            "when_to_seek_help": "If your mood, sleep, or ability to cope shifts noticeably at any point, it's always worth mentioning to your GP or health visitor, waiting isn't necessary.",
        },
        "mid": {
            "label": "Some strain showing",
            "summary": "There are signs you're under more strain than you'd like to be.",
            "why_it_matters": "What you're describing is common, and it's genuinely not a sign of failing at this. Sleep disruption, reduced support, and low mood in pregnancy or postnatally compound each other quickly, and they respond well to support, both practical and professional.",
            "next_steps": [
                "Talk to your GP or health visitor about how you're feeling, they see this regularly and can help",
                "Ask for more practical support where you can, from family, friends, or local services",
                "Say specifically what kind of support would help most, people often want to help but don't know how",
                "Look into local postnatal or antenatal support groups, connecting with others in the same stage helps more than people expect",
                "Prioritise sleep however you can, even short protected blocks make a measurable difference",
                "If a partner or family member is available, talk to them directly about what's changed recently",
            ],
            "lifestyle_tips": [
                "Lower the bar on non-essential tasks for now, this stage doesn't need to look a certain way",
                "Try to eat regularly even when it's simple, low blood sugar makes everything else harder",
                "Short daily walks, even five minutes, genuinely help mood and energy",
                "Limit doom-scrolling or comparison on social media in this stage, it disproportionately affects mood here",
            ],
            "when_to_seek_help": "Please raise this with your GP or health visitor soon rather than waiting to see if it passes, support at this stage tends to help quickly.",
        },
        "high": {
            "label": "Worth talking to someone",
            "summary": "What you've shared suggests you're finding this stage genuinely hard right now.",
            "why_it_matters": "This matters, and you deserve real support, not just reassurance that it will pass. What you're describing is exactly what GPs, midwives, and health visitors are there for, this is one of the most common and most treatable things they see, and getting support early tends to make the biggest difference.",
            "next_steps": [
                "Speak with your GP or health visitor soon, this week if you can",
                "Let someone close to you know how you're actually doing, not the version that's easiest to say out loud",
                "If you have a partner, consider asking them to come with you to your next appointment",
                "Ask directly about what support is available locally, postnatal mental health services, peer support, talking therapies",
                "You don't need to wait for a scheduled check-up, you can contact your GP or health visitor any time",
                "If you ever feel unable to cope or unsafe, treat that as urgent and contact your GP, midwife, or NHS 111 straight away",
            ],
            "lifestyle_tips": [
                "Focus only on the essentials for now, feeding, safety, rest, everything else can wait",
                "Accept help without qualifying it, you don't need to earn support right now",
                "If you're not sleeping when the baby sleeps, even that alone is worth raising with your GP",
            ],
            "when_to_seek_help": "Please don't sit with this alone. Speaking to your GP, midwife, or health visitor this week is the right next step, and if things ever feel urgent, contact them or NHS 111 immediately rather than waiting.",
        },
    },
    "strength": {
        "low": {
            "label": "Strong foundation",
            "summary": "Your habits and history point to good bone and strength resilience right now.",
            "why_it_matters": "Bone density peaks in your 20s and 30s and gradually declines afterward, especially after menopause, so what you do now genuinely protects your future mobility and independence. Strong current habits are worth maintaining deliberately, not just assuming they'll continue on their own.",
            "next_steps": [
                "Maintain your current strength routine, consistency matters more than intensity here",
                "Recheck in a year, habits and risk factors shift gradually and it's worth the occasional review",
                "If you haven't had a bone density scan and you're over 50 or postmenopausal, it's worth asking your GP about one",
                "Keep resistance training varied, bones respond to different types of load over time",
                "Stay on top of calcium and vitamin D intake even while things are going well",
            ],
            "lifestyle_tips": [
                "Weight-bearing cardio (walking, jogging, dancing) complements resistance training well for bone health",
                "Balance-focused exercise (yoga, tai chi) protects against falls even when strength is already good",
                "Limit smoking and excessive alcohol, both measurably reduce bone density over time",
            ],
            "when_to_seek_help": "If you experience any fall, even a minor one, or any unexplained bone pain, it's worth mentioning to a GP regardless of how strong things feel otherwise.",
        },
        "mid": {
            "label": "Some factors to watch",
            "summary": "A few things here are worth paying attention to before they become bigger issues.",
            "why_it_matters": "Bone density and functional strength decline gradually and often silently, there's rarely a dramatic warning sign before a fracture. Catching this stage with some proactive changes is exactly when action makes the most difference, before anything's gone noticeably wrong.",
            "next_steps": [
                "Add weight-bearing activity a couple of times a week if you're not already, walking counts, it doesn't need to be intense",
                "Ask about a bone density scan if you haven't had one, particularly if you have any family history",
                "Increase calcium-rich foods in your regular diet, dairy, leafy greens, fortified alternatives",
                "Get more regular sunlight exposure or discuss a vitamin D supplement with your GP or pharmacist",
                "If you've had a fall recently, mention it to your GP even if it felt minor",
                "Build in two short strength sessions a week, bodyweight exercises are a reasonable place to start",
            ],
            "lifestyle_tips": [
                "Balance work (single-leg stands, tai chi, yoga) reduces fall risk meaningfully, even alongside strength training",
                "Protein intake supports muscle maintenance alongside strength training, worth a look if your diet's light on it",
                "Reduce smoking and alcohol where you can, both directly affect bone density over time",
            ],
            "when_to_seek_help": "If you notice ongoing joint pain, balance issues, or you've had more than one fall, it's worth raising with a GP rather than waiting for the next review point.",
        },
        "high": {
            "label": "Worth prioritising",
            "summary": "Several factors here suggest your bone health and physical resilience deserve real attention now.",
            "why_it_matters": "The combination of factors here, low activity, limited weight-bearing exercise, fall history, and limited calcium or vitamin D, adds up to a real, addressable risk picture, not just individually minor points. The encouraging part is that bone and strength health responds well to targeted action, even starting later than you'd like still makes a genuine difference.",
            "next_steps": [
                "Book a consultation to discuss a bone density scan, this is the clearest way to know where things actually stand",
                "Start a structured strength routine, ideally with guidance from a practitioner or physiotherapist rather than going it alone",
                "Ask your GP about vitamin D and calcium levels specifically, supplementation may be worth discussing",
                "If you've had more than one fall, ask specifically about a falls risk assessment",
                "Prioritise balance work alongside strength, tai chi and similar low-impact options are genuinely effective and low-risk to start",
                "Review any medications with your GP or pharmacist, some can affect bone density or balance",
                "Build activity in gradually and consistently rather than trying to fix everything at once",
            ],
            "lifestyle_tips": [
                "Start smaller than feels necessary, consistency beats intensity when rebuilding strength and confidence",
                "Address home fall hazards (loose rugs, poor lighting, trailing cables) while you build strength back up",
                "Calcium and vitamin D matter here specifically, worth discussing actual levels with your GP rather than guessing",
            ],
            "when_to_seek_help": "This is worth treating as a genuine priority rather than something to revisit later, book that consultation, it's the clearest way to turn this from a risk picture into an actual plan.",
        },
    },
    "preconception": {
        "low": {
            "label": "Well positioned",
            "summary": "Your cycle, supplements, and lifestyle factors all point in a good direction right now.",
            "why_it_matters": "Most healthy couples conceive within a year of trying, and the groundwork you're already doing, tracking your cycle, taking folic acid, limiting the factors known to affect fertility, genuinely supports that. This stage is as much about patience and consistency as anything else.",
            "next_steps": [
                "Keep taking folic acid daily, it's one of the most well-evidenced steps for a healthy pregnancy",
                "Continue tracking your cycle, it helps you understand your fertile window and is useful information either way",
                "Maintain a balanced diet and regular moderate exercise, both support fertility and a healthy pregnancy",
                "If you haven't already, this is a good time for a general health check, including any relevant vaccinations",
                "Revisit this if it's been six months without success, that's a normal point to check in, not a cause for concern yet",
                "If either partner smokes, this is genuinely one of the highest-impact changes for fertility, worth prioritising even here",
            ],
            "lifestyle_tips": [
                "Limit alcohol and avoid smoking, both measurably affect fertility for both partners",
                "Moderate caffeine intake, current general guidance suggests keeping it reasonably low",
                "Maintain a healthy weight range where possible, it supports both conception and pregnancy",
                "Keep track of any medications or supplements you take, some affect fertility and are worth reviewing with a pharmacist",
            ],
            "when_to_seek_help": "Most people don't need to see a GP about fertility until they've been trying for a year, or six months if you're over 35, but you're welcome to check in earlier if anything's on your mind.",
        },
        "mid": {
            "label": "A few things worth adjusting",
            "summary": "There are some factors here worth addressing while you're trying to conceive.",
            "why_it_matters": "None of what's come up here is unusual, irregular cycles, inconsistent supplement use, or a lifestyle factor or two are common and very often addressable. Making a few adjustments now genuinely improves the picture, and it also makes any future conversation with a GP more useful if you do need one.",
            "next_steps": [
                "Start taking a folic acid supplement daily if you're not already, it's a simple, well-evidenced step",
                "If your cycle is irregular, tracking it for a couple of months gives you (and a GP, if needed) much clearer information",
                "Reduce or cut out the lifestyle factors that came up, smoking, regular alcohol, or high caffeine intake all measurably affect fertility",
                "Book a general preconception check with your GP, they can review your overall health and any relevant vaccinations",
                "Give it a few months with these changes in place before assuming anything's wrong",
                "If you or your partner have any known health conditions, mention them at your GP check, some affect fertility and are manageable",
            ],
            "lifestyle_tips": [
                "Small, sustained changes (cutting back rather than quitting overnight) are often more sustainable and still effective",
                "A partner's health and lifestyle matter here too, fertility isn't only about one person",
                "Regular moderate exercise and consistent sleep both support hormonal regularity",
                "Stress reduction genuinely helps here too, both directly and indirectly through sleep and cycle regularity",
            ],
            "when_to_seek_help": "If you're still trying after a year, or six months if you're over 35, that's the standard point to talk to a GP, but there's no harm in checking in sooner given what's come up here.",
        },
        "high": {
            "label": "Worth a GP conversation",
            "summary": "A combination of factors here suggests it's worth talking to a GP sooner rather than later.",
            "why_it_matters": "The combination of how long you've been trying, your cycle pattern, and the lifestyle factors involved is exactly the kind of picture worth a proper conversation with a GP, not because something is necessarily wrong, but because they can actually investigate and rule things in or out, which guessing can't do.",
            "next_steps": [
                "Book an appointment with your GP to discuss fertility, bring details of how long you've been trying and your cycle pattern",
                "Start folic acid daily now if you haven't already",
                "Address the lifestyle factors that came up as a genuine priority, smoking and regular alcohol have a real, evidenced effect",
                "Ask your GP about initial fertility investigations, for both partners, this is standard and nothing to be anxious about raising",
                "If irregular cycles are a factor, mention this specifically, it's often the most useful clue for a GP to start with",
                "Ask whether a referral to a fertility specialist is appropriate at this stage, GPs can usually advise on typical timelines",
            ],
            "lifestyle_tips": [
                "Track your cycle in the meantime, even basic tracking gives a GP much more to work with",
                "Involve your partner in this conversation and any lifestyle changes, fertility investigations usually consider both partners",
                "Try not to let this become the only focus of your relationship day to day, it's a genuinely hard balance but worth naming",
                "This process can be genuinely stressful, it's worth naming that directly rather than pushing through it silently",
            ],
            "when_to_seek_help": "This is the point where speaking to a GP is genuinely the right next step, they can properly investigate rather than you having to guess, and most causes of delayed conception are identifiable and treatable.",
        },
    },
    "periods": {
        "low": {
            "label": "Nothing concerning",
            "summary": "Your periods sound broadly typical, with nothing here that stands out as needing attention.",
            "why_it_matters": "Periods vary a lot between people and even cycle to cycle, so 'normal' covers a wide range. Knowing your own baseline, pain level, flow, and how premenstrual symptoms affect you, is useful in itself, since it's what makes it easier to notice if something genuinely changes later.",
            "next_steps": [
                "Keep a rough note of your cycle if you don't already, it's genuinely useful context if anything changes later",
                "If you're using contraception, revisit whether it's still the right fit for you every so often, needs change over time",
                "Get familiar with what counts as a genuinely heavy period, changing protection every one to two hours, so you'd notice if things shifted",
                "Revisit this check if anything changes noticeably",
                "If you're not using contraception and don't want to conceive, it's worth reviewing your options with a GP or pharmacist",
                "Cervical screening (the smear test) is offered from age 25 in the UK, worth knowing when you're next due",
            ],
            "lifestyle_tips": [
                "Regular exercise and consistent sleep both genuinely help with PMS symptoms for many people",
                "Track symptoms alongside your cycle if you're curious, patterns are often clearer than they feel day to day",
                "Reduce caffeine and salt in the days before your period if bloating or breast tenderness bothers you, it helps some people",
            ],
            "when_to_seek_help": "If your periods change noticeably in pain, flow, or pattern, or you notice bleeding between periods or after sex, it's always worth mentioning to a GP.",
        },
        "mid": {
            "label": "Worth a conversation",
            "summary": "There are some period-related symptoms here worth discussing with a GP, even though nothing sounds urgent.",
            "why_it_matters": "Pain, heavy flow, or significant PMS that affects your daily life isn't just something to manage quietly, conditions like endometriosis, adenomyosis, and PMDD are common, genuinely under-diagnosed, and treatable, but only if they're raised. Many people wait years before mentioning symptoms like this, and it's rarely necessary.",
            "next_steps": [
                "Book a GP appointment to talk through your symptoms, bring specifics on pain, flow, and timing if you can",
                "Track your cycle and symptoms for two to three months beforehand, it makes the conversation far more useful",
                "Ask specifically about conditions like endometriosis or adenomyosis if pain is a significant factor, they're often missed without asking directly",
                "If contraception might help manage symptoms, ask your GP what options exist beyond what you've already tried",
                "Don't downplay the impact when describing it, 'affects some days' is worth raising properly, not minimising",
                "If PMS is the main issue, ask specifically about PMDD (premenstrual dysphoric disorder), it's a recognised and treatable condition",
            ],
            "lifestyle_tips": [
                "A symptom diary (pain, flow, mood) across a full cycle is one of the most useful things you can bring to a GP appointment",
                "Heat, gentle movement, and anti-inflammatory pain relief genuinely help period pain for many people, worth trying if you haven't",
                "If heavy flow is a factor, keep an eye on tiredness and breathlessness too, it can be linked to low iron",
            ],
            "when_to_seek_help": "If pain or flow is significantly affecting your daily life, work, or plans, that's already a reason to see a GP, you don't need to wait for it to get worse.",
        },
        "high": {
            "label": "Worth prioritising",
            "summary": "What you've described suggests your periods are significantly affecting your daily life, and that's worth addressing properly.",
            "why_it_matters": "Severe period pain, heavy bleeding, or significant premenstrual symptoms are not something you should have to just get through every month. These are genuine, common, and treatable, conditions like endometriosis and adenomyosis are frequently missed for years, and getting the right diagnosis often changes things considerably.",
            "next_steps": [
                "Book a GP appointment as a priority to discuss your symptoms in detail",
                "Ask directly about endometriosis, adenomyosis, and PMDD, name them specifically rather than waiting to be asked",
                "Bring a symptom diary if you can, pain severity, flow, and how many days are affected each cycle",
                "If a previous GP visit didn't lead anywhere, it's worth going back or seeking a second opinion, this is a common experience and not a sign you did anything wrong",
                "Ask about referral to gynaecology if your GP's initial options don't help",
                "If heavy bleeding is part of the picture, ask about checking your iron levels too",
            ],
            "lifestyle_tips": [
                "Keep a detailed symptom diary, it's the single most useful tool for getting the right diagnosis faster",
                "Don't minimise the description when you're asked, 'severe' and 'affects daily life' are the words worth using",
                "If pain relief that's worked before has stopped helping, mention that specifically, it's a useful clue",
            ],
            "when_to_seek_help": "Please treat this as worth addressing now. Severe period symptoms at this level are exactly what a GP appointment, and likely a gynaecology referral, are for.",
        },
    },
    "pelvic": {
        "low": {
            "label": "No current concerns",
            "summary": "Your pelvic and bladder health sounds in a good place right now.",
            "why_it_matters": "Pelvic floor strength and bladder control naturally come under more pressure at different life stages, pregnancy, childbirth, and menopause all play a part, so what feels fine now is still worth protecting deliberately rather than assumed to stay that way on its own.",
            "next_steps": [
                "Keep up pelvic floor exercises if you're already doing them, consistency matters more than intensity",
                "If you're not doing them regularly, this is a good time to start, it's a genuinely low-effort, high-value habit",
                "Get familiar with what's normal for you so you'd notice a change",
                "If you're pregnant or planning pregnancy, ask your midwife or GP about pelvic floor preparation specifically",
                "Stay hydrated, concentrated urine can irritate the bladder and increase UTI risk",
                "Revisit this if anything changes, especially after childbirth or around menopause",
            ],
            "lifestyle_tips": [
                "Pelvic floor exercises take a few minutes a day and can be done almost anywhere, worth building into a routine",
                "Avoid habitually 'just in case' toilet trips, it can retrain your bladder to signal more often than needed",
                "Wiping front to back and urinating after sex both genuinely reduce UTI risk",
            ],
            "when_to_seek_help": "If you ever notice leaking, pelvic pain, or a change in urinary habits, it's worth mentioning to a GP even if it feels minor.",
        },
        "mid": {
            "label": "Some factors to watch",
            "summary": "A few things here, whether that's occasional leaking, pelvic symptoms, or recurring UTIs, are worth a conversation.",
            "why_it_matters": "Symptoms like this are extremely common, and also very treatable, but they tend to get quietly managed around rather than raised, often for years. Pelvic floor physiotherapy in particular has strong evidence behind it and is widely underused simply because people don't know it's an option.",
            "next_steps": [
                "Ask your GP about referral to a pelvic health physiotherapist, it's a genuinely effective, specific treatment, not just general advice",
                "Mention any leaking directly, even if it only happens occasionally, it's more common to raise than you'd think",
                "If UTIs are recurring, ask your GP about why, and whether further investigation or prevention strategies are appropriate",
                "Note any pelvic pain pattern, when it happens and what seems to trigger it, before your appointment",
                "Ask about vaginal or vulval symptoms directly if you've noticed any, they're a normal, common thing to raise",
                "Build in daily pelvic floor exercises if you're not already, ideally guided properly rather than guessed at",
            ],
            "lifestyle_tips": [
                "Many people do pelvic floor exercises incorrectly without guidance, a pelvic health physio can check your technique properly",
                "Reduce bladder irritants like caffeine and fizzy drinks if leaking or urgency is a factor, it helps some people meaningfully",
                "Constipation puts extra pressure on the pelvic floor, worth addressing if it's a regular issue for you",
            ],
            "when_to_seek_help": "If leaking, pain, or recurring UTIs are affecting your day-to-day life, it's worth raising with a GP now rather than managing around it indefinitely.",
        },
        "high": {
            "label": "Worth prioritising",
            "summary": "What you've described suggests your pelvic and bladder health deserves proper attention now, not just management around the edges.",
            "why_it_matters": "Regular leaking, ongoing pelvic pain, or frequent UTIs are genuinely treatable, but they don't tend to resolve on their own, and going without proper support for a long time is more common than it should be. There's real, effective help available here, particularly pelvic health physiotherapy and, where relevant, gynaecology.",
            "next_steps": [
                "Book a GP appointment to discuss this properly, be specific about frequency and impact",
                "Ask directly for a referral to a pelvic health physiotherapist, this is a standard, effective referral, not an escalation",
                "If pelvic pain or vulval/vaginal symptoms are part of the picture, mention them explicitly, they're relevant even alongside bladder symptoms",
                "If UTIs are frequent, ask about further investigation, recurring infections are worth understanding properly",
                "Don't wait for symptoms to become embarrassing to mention, this is one of the most common reasons people delay seeking help unnecessarily",
                "If a previous GP visit didn't lead anywhere, ask again or seek a second opinion",
            ],
            "lifestyle_tips": [
                "Pelvic health physiotherapy has strong evidence for exactly this combination of symptoms, it's worth asking for by name",
                "Avoid heavy lifting or high-impact exercise until you've had things assessed, if leaking is significant",
                "Keep a brief log of symptoms and triggers, it helps a specialist get to the right plan faster",
            ],
            "when_to_seek_help": "This is worth treating as a genuine priority. Book that GP appointment and ask specifically about a pelvic health physiotherapy referral, it's the clearest path from managing this to actually resolving it.",
        },
    },
    "breast": {
        "low": {
            "label": "No current concerns",
            "summary": "Nothing here stands out as needing attention right now.",
            "why_it_matters": "Getting familiar with how your breasts normally look and feel is the single most useful thing for noticing a genuine change early, and breast screening, where you're in the age range for it, is one of the most effective tools available for catching things early.",
            "next_steps": [
                "Get into a light habit of checking, there's no need for a strict schedule, just regular familiarity",
                "Know what's normal for you, breast tissue naturally changes with your cycle, so familiarity matters more than a single check",
                "If you're in the age range for breast screening (typically 50 to 71 in the UK), make sure you're registered and attending when invited",
                "Know the signs to watch for: new lumps, changes in shape or size, skin changes, or nipple changes or discharge",
                "If you have a family history of breast or ovarian cancer, mention it to your GP, it may affect your screening timeline",
                "Revisit this if anything changes, there's no need to wait for a scheduled check",
            ],
            "lifestyle_tips": [
                "Checking in the shower or when getting dressed is an easy way to build familiarity without it becoming a big task",
                "Regular exercise and limiting alcohol both genuinely support long-term breast health",
                "If breast screening invitations go to an old address, it's worth updating your details with your GP",
            ],
            "when_to_seek_help": "Any new lump, change in shape or size, skin change, or nipple change or discharge is worth getting checked promptly, regardless of age or how minor it seems.",
        },
        "mid": {
            "label": "Worth a closer look",
            "summary": "Something here, whether that's a change you've noticed or screening you're not sure about, is worth following up.",
            "why_it_matters": "Most breast changes turn out not to be cancer, but the only way to know that with confidence is to get them checked, not to wait and see. Getting screening up to date, if you're overdue, is equally worth prioritising, it's one of the clearest, most effective tools for catching things early.",
            "next_steps": [
                "If you've noticed a change, book a GP appointment specifically to have it checked, don't fold it into an unrelated appointment",
                "If you're overdue for breast screening, contact your GP or the national screening service to get it rebooked",
                "Describe any change clearly and specifically when you see a GP, when you noticed it and whether it's changed since",
                "Don't wait to see if a change resolves on its own before getting it checked",
                "If you're not sure whether something's a genuine change or normal cyclical variation, get it checked anyway, that's exactly what appointments like this are for",
                "Build in a regular, light self-check habit going forward regardless of the outcome here",
            ],
            "lifestyle_tips": [
                "Note down when you first noticed any change and anything that's shifted since, it helps a GP assess it properly",
                "There's no need to wait for a routine appointment, breast changes are seen promptly, this isn't something to sit on",
                "Most referrals for breast changes are precautionary rather than urgent, it's a normal, common pathway",
            ],
            "when_to_seek_help": "Please get any noticed change checked soon rather than monitoring it yourself, and if screening is overdue, get that rebooked at the same time.",
        },
        "high": {
            "label": "Get this checked now",
            "summary": "You've noticed a change that hasn't been checked yet, and that's worth acting on promptly.",
            "why_it_matters": "Most breast changes are not cancer, but getting anything new properly checked quickly is exactly the right response, not an overreaction. Early assessment is what makes breast health outcomes as good as they are, waiting is the only genuinely unhelpful option here.",
            "next_steps": [
                "Book a GP appointment specifically to have this checked, ideally in the next few days",
                "Describe the change clearly, what it is, when you noticed it, and whether it's changed since",
                "Ask directly about referral to a breast clinic if your GP doesn't raise it themselves, referrals for this are usually seen quickly",
                "Don't wait to see if it resolves on its own before getting it checked",
                "If you're also overdue for breast screening, mention that at the same appointment",
                "Bring someone with you if that would help, it's completely reasonable to want support for this kind of appointment",
            ],
            "lifestyle_tips": [
                "Most urgent breast referrals in the UK are seen within two weeks, this pathway exists specifically so things are checked quickly",
                "Try not to search extensively online in the meantime, it tends to raise anxiety without adding useful information",
                "It's completely normal to feel anxious about this, that doesn't mean something is seriously wrong, it means it's worth checking properly",
            ],
            "when_to_seek_help": "Please book that GP appointment now rather than monitoring this yourself. This is precisely the kind of change that's worth getting checked promptly, most of the time it turns out to be nothing serious, but it's always worth confirming.",
        },
    },
    "heart": {
        "low": {
            "label": "Steady",
            "summary": "Nothing here points to an immediate concern for your heart health.",
            "why_it_matters": "Heart disease is often thought of as a men's health issue, but it's the leading cause of death for women too, and symptoms can present differently, which means it's sometimes recognised later than it should be. Building good habits and knowing your numbers now genuinely protects you long-term, especially through and after menopause, when risk naturally rises.",
            "next_steps": [
                "Get your blood pressure checked if it's been a while, most pharmacies offer this for free, no appointment needed",
                "Get familiar with your family history of heart disease and stroke if you don't know it already",
                "Keep up regular activity, it's one of the most protective things you can do for long-term heart health",
                "If you smoke, know that quitting is the single highest-impact change available for heart health specifically",
                "Revisit this if anything changes, palpitations, breathlessness, or chest discomfort are always worth mentioning",
                "Know that menopause raises cardiovascular risk somewhat due to the drop in oestrogen, worth keeping in mind going forward",
            ],
            "lifestyle_tips": [
                "Regular moderate exercise, even brisk walking, measurably supports heart health",
                "A diet with plenty of vegetables, fibre, and healthy fats, and lower in processed food, is genuinely protective",
                "Managing stress and prioritising sleep both have a real, if less obvious, effect on cardiovascular health",
            ],
            "when_to_seek_help": "Chest pain, breathlessness that's new or worse than usual, or palpitations are always worth mentioning to a GP, regardless of how fit or healthy you otherwise feel.",
        },
        "mid": {
            "label": "Worth a check-in",
            "summary": "A few factors here are worth getting properly checked, even though nothing sounds urgent.",
            "why_it_matters": "Things like unchecked blood pressure, occasional palpitations, or a family history combined with smoking are exactly the kind of picture worth a GP conversation, not because something is necessarily wrong, but because these are precisely the factors that are both measurable and manageable once they're known.",
            "next_steps": [
                "Book a blood pressure check if you haven't had one recently, a pharmacy or GP can both do this",
                "Mention any palpitations to your GP, even if they're occasional, they're worth a baseline check",
                "If you smoke, ask your GP about support to stop, it's the single most effective change available here",
                "Ask your GP for a general cardiovascular risk check if it's been a while, it usually includes cholesterol and blood pressure",
                "If your family history includes early heart disease or stroke, mention it specifically, it affects how risk is assessed",
                "Build in regular activity if it's not already part of your routine, even modest increases measurably help",
            ],
            "lifestyle_tips": [
                "Home blood pressure monitors are inexpensive and useful if you want to track this between GP visits",
                "Reducing salt intake has a genuine, measurable effect on blood pressure for many people",
                "If stopping smoking feels daunting, NHS stop smoking services significantly improve success rates, worth using rather than going it alone",
            ],
            "when_to_seek_help": "If palpitations become more frequent, or you notice breathlessness or chest discomfort with activity, raise it with a GP soon rather than waiting for a routine check.",
        },
        "high": {
            "label": "Worth prioritising",
            "summary": "The combination of factors here suggests your heart health deserves proper attention now.",
            "why_it_matters": "Regular palpitations, raised blood pressure, smoking, and family history don't need to all be present to matter, but together they form a genuine risk picture worth investigating properly rather than monitoring informally. The reassuring part is that cardiovascular risk responds well to both medical support and lifestyle change, even starting now makes a real difference.",
            "next_steps": [
                "Book a GP appointment to discuss your heart health specifically, bring the details of what's come up here",
                "Ask for a full cardiovascular risk assessment, including blood pressure and cholesterol",
                "If palpitations are regular, ask specifically about further investigation, such as an ECG",
                "If you smoke, ask about stop smoking support as a priority, it's the highest-impact change available",
                "Mention your family history clearly, it changes how your overall risk is assessed",
                "Don't wait for a symptom to feel dramatic before raising it, the combined picture matters here, not just one factor",
            ],
            "lifestyle_tips": [
                "Small, sustained changes (reducing salt, increasing activity, quitting smoking) genuinely add up meaningfully here",
                "Keep a note of when palpitations happen and what you were doing, it's useful information for a GP",
                "NHS stop smoking services and structured support significantly improve success rates versus stopping alone",
            ],
            "when_to_seek_help": "Please treat this as worth addressing now. Book that GP appointment for a proper cardiovascular check, and if you ever have chest pain, severe breathlessness, or a palpitation episode that feels different or frightening, treat that as urgent and contact 999 or NHS 111.",
        },
    },
    "mental_health": {
        "low": {
            "label": "Doing okay",
            "summary": "Your mood sounds broadly stable right now, without strong signs of ongoing difficulty.",
            "why_it_matters": "Mental health is worth checking in on even when things feel fine, and traits linked to ADHD or autism, when they exist, are often only clearly noticed once you deliberately reflect on them, particularly for women, who are more likely to be missed or diagnosed later than men. Checking in now costs nothing and helps you notice change later.",
            "next_steps": [
                "Keep checking in with yourself regularly, mood can shift gradually enough that it's easy to miss",
                "If anything here made you pause, even a little, it's worth exploring further, this check is a starting point, not a full picture",
                "Know that ADHD and autism in women often present differently than the stereotypes suggest, worth reading into if you're curious",
                "Maintain the things that support your mental health, sleep, connection, movement, they matter even when things are going well",
                "Revisit this check if anything changes",
                "If you ever want a proper assessment for ADHD or autism, your GP is the right starting point for a referral, whenever that feels right for you",
            ],
            "lifestyle_tips": [
                "Regular sleep, movement, and social connection are all genuinely protective for mental health, worth maintaining deliberately",
                "Journalling or a mood-tracking app can help you notice patterns you might otherwise miss",
                "Limiting doom-scrolling or comparison on social media measurably helps mood for many people",
            ],
            "when_to_seek_help": "If your mood dips, or if you find yourself increasingly curious about ADHD or autism traits you recognise in yourself, it's always worth a GP conversation, whenever that feels right.",
        },
        "mid": {
            "label": "Worth exploring further",
            "summary": "There's a mix here, whether that's low mood, anxiety, or traits linked to ADHD or autism, worth taking seriously and following up on.",
            "why_it_matters": "None of what's come up here is unusual, and it's genuinely common for women to reach adulthood without mental health support or a neurodivergence diagnosis that would have helped explain things much earlier. Following up on this properly, whichever direction it points, tends to make a real, practical difference.",
            "next_steps": [
                "Book a GP appointment to talk through your mood, be specific about how it's affecting daily life",
                "If ADHD or autism traits resonated, mention that too, GPs can refer for assessment even without a childhood diagnosis",
                "Look into NHS talking therapies (IAPT/NHS Talking Therapies), you can often self-refer without needing to see a GP first",
                "Track your mood for a couple of weeks if you can, patterns make the conversation more useful",
                "If ADHD or autism traits are the bigger factor, look into validated self-report screeners (like the ASRS or AQ-10) as a starting point, they're not a diagnosis but can help structure the conversation",
                "Talk to someone close to you about how you're doing, this stage is easier with support",
            ],
            "lifestyle_tips": [
                "Structure and routine genuinely help manage ADHD-linked traits day to day, even before any formal assessment",
                "If sensory sensitivity is a factor, small adjustments (noise-cancelling headphones, lighting) can meaningfully help",
                "Regular movement and consistent sleep timing both measurably support mood",
            ],
            "when_to_seek_help": "If your mood is affecting work, relationships, or daily functioning, or if ADHD or autism traits are significantly affecting your life, that's already reason enough to seek support, you don't need to wait until it feels unmanageable.",
        },
        "high": {
            "label": "Worth prioritising",
            "summary": "What you've shared suggests you're finding things genuinely hard right now, and this deserves real support.",
            "why_it_matters": "Significant, ongoing low mood or anxiety is common and very treatable, and strong, longstanding traits linked to ADHD or autism are worth a proper assessment, not something to keep managing alone. Women are disproportionately likely to be missed or diagnosed later in life for both mental health difficulties and neurodivergence, this is a genuine gap in how these are recognised, not a reflection of how significant what you're experiencing is.",
            "next_steps": [
                "Speak with your GP soon, this week if you can, about how you're feeling",
                "Ask directly about referral for an ADHD or autism assessment if those traits felt significant and longstanding",
                "Self-refer to NHS Talking Therapies if you'd like to start support while waiting for any further referral",
                "Let someone close to you know how you're actually doing",
                "If low mood or anxiety is significantly affecting your ability to function day to day, say that clearly and specifically to your GP",
                "If you ever feel unable to cope or unsafe, treat that as urgent and contact your GP or NHS 111 immediately",
            ],
            "lifestyle_tips": [
                "Focus on the essentials while you get support in place, everything else can wait",
                "Accept help without qualifying it, you don't need to earn support right now",
                "Assessment waiting lists can be long, it's worth starting the referral process now even while exploring other support in parallel",
            ],
            "when_to_seek_help": "Please don't sit with this alone. Speaking to your GP this week is the right next step, and if things ever feel urgent or unsafe, contact your GP or NHS 111 immediately rather than waiting.",
        },
    },
    "sexual_health": {
        "low": {
            "label": "No current concerns",
            "summary": "Nothing here stands out as needing attention right now.",
            "why_it_matters": "Sexual health is a normal, ongoing part of overall health, not something that only matters when there's a problem. Regular check-ups where relevant, and knowing what's normal for you, make it much easier to notice and address anything that does come up.",
            "next_steps": [
                "If you're sexually active with new or multiple partners, regular STI screening (roughly annually, or after a new partner) is worth keeping up",
                "Sexual health clinics offer free, confidential testing and don't require a GP referral",
                "Get familiar with what's normal for you so you'd notice a change",
                "If you use contraception, revisit whether it's still the right fit periodically",
                "Know that most STIs are symptomless, testing is the only reliable way to know, not waiting for symptoms",
                "Revisit this check if anything changes",
            ],
            "lifestyle_tips": [
                "Condoms remain the most effective protection against STIs alongside other contraception for pregnancy prevention",
                "Free, confidential testing is available at sexual health clinics and, for many STIs, by post via NHS-linked services",
                "Open communication with partners about testing and sexual health genuinely reduces risk and awkwardness over time",
            ],
            "when_to_seek_help": "Any unusual discharge, pain, itching, or bleeding between periods or after sex is worth getting checked, regardless of when your last test was.",
        },
        "mid": {
            "label": "Worth a check-up",
            "summary": "Something here, whether that's a symptom, a while since your last check-up, or a concern about your sex life, is worth following up.",
            "why_it_matters": "Sexual health concerns are common and sexual health clinics see this constantly, without judgement. Most issues, whether an infection, discomfort, or a change in desire, are straightforward to check and often straightforward to treat once they're actually looked at.",
            "next_steps": [
                "Book a sexual health check-up, at a clinic or via a postal testing kit if that's easier for you",
                "If you've noticed symptoms, get them checked specifically rather than waiting to see if they resolve",
                "If pain during sex or low desire is a concern, mention it to a GP or sexual health clinic, it's a common and treatable issue, not something to just live with",
                "Sexual health clinics don't require a GP referral and testing is free and confidential",
                "If it's been a while since your last test and you've had new partners since, that's worth prioritising",
                "Consider whether your current contraception, if any, is still the right fit given anything that's come up",
            ],
            "lifestyle_tips": [
                "Postal STI testing kits are a private, straightforward option if visiting a clinic feels like a barrier",
                "Pain during sex has many treatable causes, from infections to hormonal changes to pelvic floor tension, it's worth investigating rather than assuming it's just something to manage",
                "Bring specifics to any appointment, when symptoms started, what they are, helps things move faster",
            ],
            "when_to_seek_help": "If you have symptoms, or it's been a while since your last check with a new partner since, book a sexual health appointment soon rather than waiting.",
        },
        "high": {
            "label": "Get this checked soon",
            "summary": "What you've described is worth getting checked properly and fairly soon.",
            "why_it_matters": "Symptoms like unusual discharge, bleeding between periods or after sex, or significant pain deserve a prompt check, not because something is necessarily seriously wrong, but because these are exactly the signs sexual health and GP services exist to investigate, and most causes are very treatable once identified.",
            "next_steps": [
                "Book a sexual health clinic appointment or GP appointment promptly to get this checked",
                "Sexual health clinics often offer same-day or short-notice appointments specifically for symptoms like this",
                "Avoid sex until you've been checked, if infection is a possibility, to avoid passing anything on",
                "Be specific and direct about your symptoms when you're seen, there's no need to feel awkward, clinicians see this constantly",
                "If bleeding between periods or after sex is part of the picture, mention that specifically, it's an important detail",
                "If pain during sex is significant, ask about referral to a specialist if the initial appointment doesn't resolve it",
            ],
            "lifestyle_tips": [
                "Sexual health clinics are judgement-free by design, most people who work there see symptoms like this every day",
                "Avoid self-diagnosing from search results, get it properly checked instead, similar-sounding symptoms often have different causes",
                "Bring a partner into the conversation if relevant, testing and treatment often need to include both of you",
            ],
            "when_to_seek_help": "Please book that appointment soon rather than waiting to see if things settle. Bleeding between periods or after sex, or significant pain, are always worth checking properly.",
        },
    },
    "brain": {
        "low": {
            "label": "No current concerns",
            "summary": "Nothing here points to a current concern for your memory or brain health.",
            "why_it_matters": "Brain health is genuinely influenced by everyday habits, exercise, sleep, social connection, and mental stimulation all measurably support it, and building these in now is protective for decades ahead. Dementia risk isn't fixed, a significant proportion of cases are linked to modifiable factors.",
            "next_steps": [
                "Keep up the habits that support brain health, they're worth maintaining deliberately rather than assuming they'll continue",
                "Get familiar with your family history of dementia if you don't know it already",
                "Stay socially connected, isolation is a genuine, under-recognised risk factor for cognitive decline",
                "Keep challenging your brain, learning something new has more evidence behind it than puzzles alone",
                "Protect your sleep, it plays a real role in long-term brain health, not just next-day energy",
                "Revisit this check if you notice any change in memory or focus",
            ],
            "lifestyle_tips": [
                "Regular physical activity is one of the most well-evidenced protective factors for long-term brain health",
                "Managing blood pressure and cardiovascular health protects brain health too, the two are closely linked",
                "Limiting alcohol and not smoking both measurably support long-term cognitive health",
            ],
            "when_to_seek_help": "If you or people close to you notice a genuine change in memory, thinking, or personality, it's worth mentioning to a GP, regardless of age.",
        },
        "mid": {
            "label": "Worth watching",
            "summary": "You've noticed some change in memory or focus, and a few other factors here are worth paying attention to.",
            "why_it_matters": "Some change in memory or focus has many possible causes, stress, sleep, hormonal changes (perimenopause in particular can affect this significantly), or thyroid issues are often behind it, and it's frequently reversible once identified. It's genuinely worth checking rather than assuming the worst or dismissing it.",
            "next_steps": [
                "Mention the change to your GP, it's a common, reasonable thing to raise and there are straightforward things to check first",
                "Ask about simple checks that can rule out common causes, thyroid function and vitamin levels among them",
                "If you're perimenopausal, mention that specifically, brain fog is a genuine, common symptom of hormonal fluctuation at this stage",
                "Build in more of the protective habits, exercise, sleep, social connection, mental stimulation, if they're currently missing",
                "If you have a family history of dementia, mention it, it's relevant context even if the current change has another cause",
                "Keep a light note of what you've noticed, it helps a GP get a clearer picture",
            ],
            "lifestyle_tips": [
                "Poor sleep has a bigger effect on memory and focus than most people realise, worth prioritising while you look into other causes",
                "Stress and anxiety genuinely affect memory and concentration, it's worth considering alongside other explanations",
                "Regular exercise measurably improves cognitive function, even starting now makes a difference",
            ],
            "when_to_seek_help": "If the change is ongoing, getting more noticeable, or others close to you have mentioned it too, it's worth a GP conversation rather than waiting to see if it passes.",
        },
        "high": {
            "label": "Worth a proper check",
            "summary": "The change you've described, combined with other factors here, is worth a proper conversation with a GP.",
            "why_it_matters": "A significant, ongoing change in memory or thinking deserves a proper assessment, not because it necessarily means something serious, many causes are reversible, but because getting it checked is the only way to know, and earlier assessment generally leads to better outcomes whatever the cause turns out to be.",
            "next_steps": [
                "Book a GP appointment specifically to discuss this, rather than mentioning it in passing at an unrelated appointment",
                "Ask for the standard initial checks, bloods, thyroid function, and a cognitive assessment if appropriate",
                "If someone close to you has also noticed the change, ask them to describe specific examples, it's genuinely useful information for a GP",
                "Mention your family history of dementia clearly if relevant",
                "If you're perimenopausal, raise that too, it's relevant context alongside anything else being checked",
                "Ask about referral to a memory clinic if initial checks don't explain things",
            ],
            "lifestyle_tips": [
                "Write down specific examples of what's changed, it's more useful to a GP than a general sense that something's different",
                "Bring someone with you to the appointment if that would help, a second perspective is often useful here",
                "Try not to jump to conclusions in the meantime, many causes of this kind of change are treatable or reversible",
            ],
            "when_to_seek_help": "Please book that GP appointment now rather than waiting. A proper check is the right next step, whatever it turns out to show, and earlier assessment tends to lead to better outcomes.",
        },
    },
    "blood_energy": {
        "low": {
            "label": "No current concerns",
            "summary": "Your energy levels and any symptoms here don't point to a current concern.",
            "why_it_matters": "Iron deficiency anaemia is common, particularly alongside heavy periods, pregnancy, and some diets, and it's easily checked and treated once identified. Knowing your baseline energy level makes it easier to notice if something genuinely shifts.",
            "next_steps": [
                "If you have heavy periods, keep half an eye on your energy levels, the two are often linked",
                "Include iron-rich foods in your diet where you can, red meat, leafy greens, and fortified cereals among them",
                "Vitamin C alongside iron-rich meals helps absorption, worth knowing if you want to be deliberate about it",
                "If you're vegetarian or vegan, it's worth being a little more deliberate about iron intake, it's still very manageable",
                "Revisit this if your energy levels or any of these symptoms change",
                "If you're planning pregnancy, ask your GP about checking your iron levels beforehand",
            ],
            "lifestyle_tips": [
                "Tea and coffee can reduce iron absorption if had right alongside iron-rich meals, worth spacing out if relevant to you",
                "Consistent sleep and regular meals both support stable energy levels day to day",
                "If tiredness feels disproportionate to your sleep and activity, it's always worth a second look rather than assuming it's just busyness",
            ],
            "when_to_seek_help": "Persistent exhaustion, breathlessness with normal activity, or looking noticeably pale are always worth checking with a GP, regardless of how busy life is right now.",
        },
        "mid": {
            "label": "Worth checking",
            "summary": "A few things here, tiredness, some symptoms, or heavy periods, are worth a simple blood test to check.",
            "why_it_matters": "Persistent tiredness with symptoms like this is common and often comes down to something straightforward and treatable, low iron being one of the most common causes, particularly alongside heavy periods. A simple blood test settles the question rather than guessing.",
            "next_steps": [
                "Book a GP appointment and ask for a blood test to check your iron levels and full blood count",
                "Mention your energy levels specifically and how long they've been affected",
                "If heavy periods are part of the picture, mention that too, it's relevant context for a GP",
                "Note down any of the symptoms you've noticed, they're useful detail for the appointment",
                "In the meantime, include more iron-rich foods in your diet, it won't hurt and may help",
                "If a blood test confirms low iron, ask about the right supplement and dose rather than guessing at over-the-counter options",
            ],
            "lifestyle_tips": [
                "Iron supplements can cause stomach upset for some people, if that happens it's worth discussing alternatives with a GP or pharmacist rather than stopping altogether",
                "Vitamin C alongside iron-rich meals or supplements genuinely improves absorption",
                "If heavy periods are a contributing factor, it's worth addressing both together rather than just the tiredness on its own",
            ],
            "when_to_seek_help": "If tiredness is significantly affecting your daily life, or you notice breathlessness with normal activity, book that GP appointment soon rather than pushing through it.",
        },
        "high": {
            "label": "Worth prioritising",
            "summary": "What you've described, persistent exhaustion alongside other symptoms, is worth checking properly and fairly soon.",
            "why_it_matters": "This level of fatigue, combined with symptoms like breathlessness, dizziness, or noticeable paleness, is exactly the picture worth a prompt blood test. Anaemia at this level is genuinely treatable, but it's also worth ruling out other causes properly rather than assuming it's just tiredness.",
            "next_steps": [
                "Book a GP appointment soon and ask for a blood test, including iron levels and a full blood count",
                "Describe the impact clearly, exhausted to the point it affects daily life is exactly the detail worth saying plainly",
                "If heavy periods are part of the picture, mention that specifically, it's directly relevant",
                "If dizziness is significant or you've had any fainting episodes, mention that too, it's worth flagging clearly",
                "Don't push through this while waiting for an appointment, rest where you can",
                "If a supplement is prescribed, take it as directed, it can take a few months to fully rebuild iron stores",
            ],
            "lifestyle_tips": [
                "Prioritise rest while you get this checked, pushing through significant fatigue doesn't resolve the underlying cause",
                "Keep a note of your symptoms and how they're affecting daily life, it helps a GP assess urgency properly",
                "If dizziness is a factor, be cautious with activities like driving until it's been checked",
            ],
            "when_to_seek_help": "Please book that GP appointment soon. Exhaustion at this level combined with these symptoms is worth a proper check now, not something to keep managing around.",
        },
    },
    "pregnancy_choices": {
        "low": {
            "label": "Not needed right now",
            "summary": "This isn't something you need more information on right now.",
            "why_it_matters": "It's still worth knowing that if this ever becomes relevant, whether that's this month or years from now, support and clear information are available whenever you need them, with no judgement attached.",
            "next_steps": [
                "Know that if this ever becomes relevant, your GP or a sexual health clinic are both starting points for confidential advice",
                "If you're not currently trying to conceive and aren't using contraception, it's worth reviewing your options with a GP or pharmacist",
                "Revisit this if your circumstances change",
            ],
            "lifestyle_tips": [
                "NHS information on pregnancy choices is available any time, without needing a referral",
                "Confidential advice is available regardless of your circumstances, whenever it's relevant to you",
            ],
            "when_to_seek_help": "If this becomes relevant at any point, your GP or a sexual health clinic can point you to confidential, judgement-free support.",
        },
        "mid": {
            "label": "General information",
            "summary": "You've said general information here would be helpful, so here's a starting point.",
            "why_it_matters": "Having clear, factual information available, without pressure either way, makes it easier to think things through on your own terms and timeline, whatever you decide.",
            "next_steps": [
                "NHS.uk has clear, factual, judgement-free information on all pregnancy options, including abortion care, worth reading through at your own pace",
                "Your GP can talk through your options confidentially, they're not there to persuade you in any direction",
                "BPAS and MSI Reproductive Choices (searchable online) provide confidential advice and care directly, without needing a GP referral first",
                "Take the time you need, there's rarely a rush to decide immediately, though timing can matter for some options, worth checking early",
                "If you'd find it helpful, talk it through with someone you trust, though the decision is entirely yours",
            ],
            "lifestyle_tips": [
                "You don't need a GP referral to contact BPAS or MSI Reproductive Choices directly, both offer confidential advice",
                "Whatever you decide, support is available, this isn't something you need to navigate without help if you don't want to",
            ],
            "when_to_seek_help": "If you'd like to talk it through properly, your GP or a service like BPAS or MSI Reproductive Choices can offer confidential, judgement-free support whenever suits you.",
        },
        "high": {
            "label": "Support available now",
            "summary": "You've said you'd like details on accessing support now, so here's how to move quickly if that's what you need.",
            "why_it_matters": "If timing matters to you, it's worth knowing that abortion care in the UK is free through the NHS, confidential, and accessible without a GP referral if that's easier, so there's no need to wait or navigate this alone.",
            "next_steps": [
                "You can self-refer directly to BPAS or MSI Reproductive Choices (searchable online), no GP referral is needed",
                "Your GP can also refer you and talk through your options confidentially, whichever route feels easier for you",
                "NHS abortion care is free and available up to the legal time limit, earlier access generally means more options, so it's worth acting promptly if you've decided",
                "Confidential support is available throughout, you don't need to make any part of this decision alone unless you want to",
                "If cost, travel, or privacy are concerns, mention this when you contact a service, they deal with this regularly and can help",
            ],
            "lifestyle_tips": [
                "Both BPAS and MSI Reproductive Choices offer confidential telephone consultations as a first step, which can happen quickly",
                "Whatever you decide, this is your decision to make, and support is there to help you carry it out, not to influence which way you go",
            ],
            "when_to_seek_help": "If timing matters to you, please reach out now, either directly to BPAS or MSI Reproductive Choices, or via your GP. Support is confidential and available without delay.",
        },
    },
}

SPECIALIST_MAP = {
    "menopause": {
        "name": "Menopause specialist",
        "expect": "A menopause specialist will typically review your full symptom picture, discuss hormone testing if relevant, and talk through the full range of options, HRT and non-hormonal, so you can choose what's right for you.",
    },
    "maternal": {
        "name": "GP or health visitor",
        "expect": "A GP or health visitor will talk through how you're doing without judgement, and can connect you with local support, from practical help to talking therapies, depending on what would actually help.",
    },
    "strength": {
        "name": "Practitioner or strength coach",
        "expect": "A practitioner can arrange a bone density scan or bloodwork if relevant, while a strength coach can build you a safe, structured programme rather than leaving you to guess where to start.",
    },
    "preconception": {
        "name": "GP",
        "expect": "A GP can review your cycle, general health, and (if it's been a while) arrange initial fertility investigations for both partners, which is the standard, unremarkable first step.",
    },
    "periods": {
        "name": "GP",
        "expect": "A GP will talk through your period symptoms, can investigate common causes like endometriosis or adenomyosis, and can discuss options including contraception if that would help manage symptoms.",
    },
    "pelvic": {
        "name": "Pelvic health physiotherapist",
        "expect": "A pelvic health physiotherapist assesses pelvic floor strength and function directly and builds a specific, guided plan, usually accessed via a GP referral.",
    },
    "breast": {
        "name": "GP or breast clinic",
        "expect": "A GP examines any change and, where appropriate, refers to a breast clinic, most referrals for this are precautionary and seen quickly.",
    },
    "heart": {
        "name": "GP",
        "expect": "A GP can check your blood pressure and cholesterol, review your family history, and arrange further investigation like an ECG if needed.",
    },
    "mental_health": {
        "name": "GP",
        "expect": "A GP can talk through your mood, refer you for talking therapies, and discuss referral for an ADHD or autism assessment if that feels relevant.",
    },
    "sexual_health": {
        "name": "Sexual health clinic or GP",
        "expect": "A sexual health clinic offers free, confidential testing and treatment without needing a GP referral, and sees these concerns every day without judgement.",
    },
    "brain": {
        "name": "GP",
        "expect": "A GP can run initial checks (bloods, thyroid function) to rule out common, often reversible causes, and refer on for further assessment if needed.",
    },
    "blood_energy": {
        "name": "GP",
        "expect": "A GP can arrange a simple blood test to check your iron levels and full blood count, and advise on supplementation if needed.",
    },
    "pregnancy_choices": {
        "name": "GP, BPAS, or MSI Reproductive Choices",
        "expect": "All three offer confidential, judgement-free advice on your options. BPAS and MSI Reproductive Choices can be contacted directly without a GP referral.",
    },
}

TRACK_EDUCATION = {
    "menopause": "Menopause is defined as twelve months without a period, usually happening between 45 and 55, though it can happen earlier. Perimenopause, the years leading up to it, is when oestrogen and progesterone levels start to fluctuate, and it's this fluctuation, not just the eventual drop, that drives most symptoms. It typically lasts four to eight years, though this varies widely. Around 80% of women experience some symptoms, and for roughly a quarter, those symptoms are severe enough to significantly affect daily life. Despite how common it is, menopause care has historically been under-discussed and under-treated, which is changing, but it means many people reach this stage without a clear sense of what's normal or what help is available.",
    "maternal": "Pregnancy and the first two years postnatal involve some of the most significant physical and hormonal change the body goes through. Around one in five women experience a mental health difficulty during pregnancy or in the year after birth, ranging from mild low mood to more significant anxiety or depression, making it one of the most common complications of this stage, not a rare or unusual one. Physical recovery also varies enormously and isn't limited to the first few weeks, many people are still adjusting physically and emotionally well beyond that. Screening and support at this stage are standard parts of NHS maternity and postnatal care, not an escalation or a sign that something has gone wrong.",
    "strength": "Bone density peaks around age 30 and gradually declines afterward, with the rate of loss accelerating for several years around menopause due to the drop in oestrogen, which plays a protective role in bone maintenance. Roughly one in two women over 50 will experience a fracture related to bone density at some point. The encouraging part is that bone health responds well to modifiable factors, weight-bearing exercise, resistance training, calcium and vitamin D intake, and avoiding smoking and excess alcohol all measurably affect long-term bone density, at any age. Falls risk and balance are equally important, since most fractures happen as a result of a fall, not spontaneously.",
    "preconception": "Fertility is influenced by a wide range of factors, cycle regularity, general health, age, and lifestyle among them. For couples with no known fertility issues, roughly 80 to 85% conceive within a year of regularly trying, and most of the remainder conceive within a further year. Folic acid supplementation before and during early pregnancy is one of the most well-evidenced preventative health measures available, meaningfully reducing the risk of certain birth defects. Lifestyle factors, smoking, regular alcohol, and high caffeine intake, have a real, measurable effect on fertility for both partners, which is why addressing them is one of the most useful things either partner can do while trying to conceive.",
    "periods": "Periods vary widely between people in pain, flow, and pattern, but severe pain, very heavy bleeding, or premenstrual symptoms that disrupt daily life are not simply things to tolerate. Conditions like endometriosis and adenomyosis affect roughly one in ten women of reproductive age yet take an average of around eight years to diagnose in the UK, largely because symptoms are dismissed or normalised for years before being properly investigated. PMDD, a severe form of premenstrual symptoms affecting mood significantly, is a recognised, treatable condition, not simply 'bad PMS'. Raising period symptoms directly and specifically with a GP is often what finally moves things forward.",
    "pelvic": "Pelvic floor and bladder health are affected by pregnancy, childbirth, and menopause, but also age and general health more broadly, and issues here are extremely common, current estimates suggest around one in three women experience some degree of urinary incontinence at some point. Despite this, pelvic health physiotherapy, one of the most effective treatments available, remains widely underused simply because many people don't know it's an option or feel embarrassed to raise symptoms. These are medical, treatable issues, not something to just manage around indefinitely.",
    "breast": "Breast cancer is the most common cancer in women in the UK, and both regular self-awareness and attending screening when invited are among the most effective tools for catching changes early, when treatment tends to be most effective. The NHS breast screening programme currently invites women for a mammogram every three years from age 50 to 71. The large majority of breast changes turn out not to be cancer, but getting anything new checked promptly, rather than waiting, is what makes early detection actually work.",
    "heart": "Cardiovascular disease is the leading cause of death for women globally, despite being widely perceived as a predominantly male health issue, and women's symptoms can present differently, which contributes to later recognition and treatment. Risk rises after menopause, linked to the protective role oestrogen plays beforehand, which makes this a particularly relevant time to check in on blood pressure, cholesterol, and lifestyle factors like smoking. The encouraging part is that cardiovascular risk responds well to both medical management and lifestyle change at any age.",
    "mental_health": "Around one in five women experience a common mental health difficulty like anxiety or depression at some point, and both ADHD and autism are significantly under-diagnosed in women and girls, who are more likely to mask traits or be missed entirely due to diagnostic criteria historically based on how these conditions present in boys and men. Many women reach adulthood, sometimes well into their thirties or forties, before recognising ADHD or autistic traits in themselves, often after a family member's diagnosis prompts them to look closer. None of this reflects how significant or 'real' any of it is, it reflects a genuine, well-documented gap in recognition.",
    "sexual_health": "Sexual health is a normal, ongoing part of overall wellbeing, and most STIs are symptomless, which is why regular testing, not waiting for symptoms, is the reliable way to stay on top of it. Sexual health clinics in the UK offer free, confidential testing and treatment without requiring a GP referral, and see the full range of symptoms and concerns every day without judgement. Pain during sex and changes in desire are also common and have a wide range of treatable causes, and are worth raising rather than accepted as just how things are.",
    "brain": "Around 45% of dementia cases globally are linked to modifiable risk factors, including physical inactivity, smoking, social isolation, and untreated hearing loss, which means everyday habits genuinely matter for long-term brain health. Perimenopause and menopause commonly cause noticeable brain fog and memory changes due to hormonal fluctuation, which is a real, well-documented symptom, not something to dismiss or assume is more serious than it is. Any genuine, ongoing change in memory or thinking is still always worth checking, since many causes, from thyroid issues to vitamin deficiencies to stress, are straightforward and reversible once identified.",
    "blood_energy": "Iron deficiency anaemia is one of the most common nutritional deficiencies among women, largely linked to menstrual blood loss, and is a frequently overlooked explanation for persistent tiredness. It's diagnosed with a simple, widely available blood test and is generally straightforward to treat with dietary changes and, where needed, supplementation. Left unaddressed, it can meaningfully affect quality of life, energy, concentration, and overall wellbeing, which is why persistent, disproportionate tiredness is always worth checking rather than dismissing as just being busy.",
    "pregnancy_choices": "In the UK, abortion is legal, free through the NHS, and available up to the legal time limit (24 weeks in most circumstances, though earlier access generally means more options are available). Around one in three women in the UK will have an abortion in their lifetime, making it a common experience, not a rare or unusual one. Confidential advice and care are available through the NHS, a GP, or directly through providers like BPAS or MSI Reproductive Choices, with no requirement to justify the decision to anyone.",
}


TRACK_TITLES = {
    "menopause": "Menopause and Hormones",
    "maternal": "Maternal Wellbeing",
    "strength": "Bone, Brain and Strength",
    "preconception": "Preconception and Fertility",
    "periods": "Periods and Contraception",
    "pelvic": "Pelvic, Bladder and Reproductive Health",
    "breast": "Breast Health and Screening",
    "heart": "Heart Health",
    "mental_health": "Mental Health and Neurodivergence",
    "sexual_health": "Sexual Health",
    "brain": "Memory and Brain Health",
    "blood_energy": "Blood and Energy Health",
    "pregnancy_choices": "Pregnancy Options and Support",
}

OVERVIEW_BY_STAGE = {
    "Perimenopause": "You're in perimenopause, the transition phase before periods stop completely, which can last several years and bring a wide range of symptoms as hormone levels fluctuate.",
    "Menopause": "You're at menopause, defined as twelve months without a period, a natural transition that affects everyone differently.",
    "Postmenopause": "You're postmenopausal, past the transition itself, with the focus now on long-term health, particularly bone and heart health.",
    "Pregnant": "You're currently pregnant, a stage with real physical and emotional change, where checking in on how you're coping matters as much as the physical side.",
    "Postnatal (within 2 years)": "You're in the postnatal period, still very much a time of adjustment and recovery, even well beyond the earliest weeks.",
    "Trying to conceive": "You're trying to conceive, a stage where small, well-evidenced habits can genuinely support the process, alongside patience.",
}


def build_report(life_stage: str, answers: dict) -> dict:
    """Returns the full per-track report as a plain dict, ready to store as JSON."""
    tracks = {}

    if life_stage in MENOPAUSE_STAGES:
        band = score_menopause(answers)
        tracks["menopause"] = {
            "title": TRACK_TITLES["menopause"],
            "band": band,
            **BAND_COPY["menopause"][band],
            "specialist": SPECIALIST_MAP["menopause"]["name"],
            "specialist_expect": SPECIALIST_MAP["menopause"]["expect"],
            "education": TRACK_EDUCATION["menopause"],
        }

    if life_stage in MATERNAL_STAGES:
        band = score_maternal(answers)
        tracks["maternal"] = {
            "title": TRACK_TITLES["maternal"],
            "band": band,
            **BAND_COPY["maternal"][band],
            "specialist": SPECIALIST_MAP["maternal"]["name"],
            "specialist_expect": SPECIALIST_MAP["maternal"]["expect"],
            "education": TRACK_EDUCATION["maternal"],
        }

    if life_stage in PRECONCEPTION_STAGES:
        band = score_preconception(answers)
        tracks["preconception"] = {
            "title": TRACK_TITLES["preconception"],
            "band": band,
            **BAND_COPY["preconception"][band],
            "specialist": SPECIALIST_MAP["preconception"]["name"],
            "specialist_expect": SPECIALIST_MAP["preconception"]["expect"],
            "education": TRACK_EDUCATION["preconception"],
        }

    band = score_strength(answers)
    tracks["strength"] = {
        "title": TRACK_TITLES["strength"],
        "band": band,
        **BAND_COPY["strength"][band],
        "specialist": SPECIALIST_MAP["strength"]["name"],
        "specialist_expect": SPECIALIST_MAP["strength"]["expect"],
        "education": TRACK_EDUCATION["strength"],
    }

    def _add_track(key: str, band: str):
        tracks[key] = {
            "title": TRACK_TITLES[key],
            "band": band,
            **BAND_COPY[key][band],
            "specialist": SPECIALIST_MAP[key]["name"],
            "specialist_expect": SPECIALIST_MAP[key]["expect"],
            "education": TRACK_EDUCATION[key],
        }

    # These 9 tracks are opt-in: the quiz shows a symptom picker right after
    # the life-stage question, listing every topic (by its TRACK_TITLES
    # label) relevant to that life stage, and only asks about, and includes,
    # the ones the client actually selects. Menopause/Maternal/Preconception
    # (life-stage driven) and Strength (always-on) are unaffected by this.
    selected_topics = set(answers.get("topicsOfInterest", []))

    if life_stage in PERIODS_STAGES and TRACK_TITLES["periods"] in selected_topics:
        _add_track("periods", score_periods(answers))

    if TRACK_TITLES["pelvic"] in selected_topics:
        _add_track("pelvic", score_pelvic(answers))

    if TRACK_TITLES["breast"] in selected_topics:
        _add_track("breast", score_breast(answers))

    if TRACK_TITLES["heart"] in selected_topics:
        _add_track("heart", score_heart(answers))

    if life_stage not in MENTAL_HEALTH_STAGES_EXCLUDE and TRACK_TITLES["mental_health"] in selected_topics:
        _add_track("mental_health", score_mental_health(answers))

    if TRACK_TITLES["sexual_health"] in selected_topics:
        _add_track("sexual_health", score_sexual_health(answers))

    if TRACK_TITLES["brain"] in selected_topics:
        _add_track("brain", score_brain(answers))

    if TRACK_TITLES["blood_energy"] in selected_topics:
        _add_track("blood_energy", score_blood_energy(answers))

    if life_stage in PREGNANCY_CHOICE_STAGES and TRACK_TITLES["pregnancy_choices"] in selected_topics:
        _add_track("pregnancy_choices", score_pregnancy_choices(answers))

    overview = OVERVIEW_BY_STAGE.get(life_stage, "")

    return {"overview": overview, "tracks": tracks}

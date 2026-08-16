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
    balance_map = {"No": 0, "A little": 1, "Yes, significantly": 2}
    wb_map = {"Rarely": 2, "Sometimes": 1, "Regularly": 0}
    supplements_taken = len([s for s in answers.get("supplements", []) if s != "Neither"])
    supplement_score = 2 - supplements_taken
    sun_map = {"Regularly": 0, "Sometimes": 1, "Rarely": 2}
    calcium_map = {"Rarely": 1, "Sometimes": 0, "Regularly": 0}
    score = (
        strength_map.get(answers.get("strength"), 0)
        + falls_map.get(answers.get("falls"), 0)
        + balance_map.get(answers.get("balance"), 0)
        + wb_map.get(answers.get("weightBearing"), 0)
        + supplement_score
        + sun_map.get(answers.get("sunlightExposure"), 0)
        + calcium_map.get(answers.get("dietCalcium"), 0)
    )
    return _band(score, 2, 7)


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
                "Keep alcohol intake moderate, it's a common under-recognised factor in sleep and hormonal symptoms",
                "Stay on top of calcium and vitamin D intake for bone health",
            ],
            "when_to_seek_help": "If anything changes noticeably, heavier or more frequent symptoms, new symptoms, or anything that worries you, it's always worth a conversation rather than waiting.",
        },
        "mid": {
            "label": "Worth a closer look",
            "summary": "You're noticing a real mix of symptoms that are starting to affect daily life.",
            "why_it_matters": "A cluster of symptoms like this usually reflects genuine hormonal fluctuation rather than something to just push through. The good news is this stage responds well to both lifestyle changes and medical options, most people who address it properly see real improvement.",
            "next_steps": [
                "Book a consultation to talk through symptom relief options, including but not limited to HRT",
                "Ask about hormone testing if you haven't had it done, it helps build a fuller picture",
                "Track your symptoms for two to three weeks before your appointment, patterns make the conversation much more useful",
                "Ask specifically about non-hormonal options too, if HRT isn't right for you there are still genuine choices",
                "Review your sleep environment, temperature regulation issues often start there",
                "Talk to people close to you about what you're experiencing, this stage is easier with support and often still under-discussed",
            ],
            "lifestyle_tips": [
                "Layer clothing and keep your bedroom cool at night, small changes here reduce sleep disruption meaningfully",
                "Reduce caffeine and alcohol in the evening, both are common sleep and symptom triggers at this stage",
                "Regular moderate exercise measurably reduces symptom frequency for many people",
                "Mindfulness or breathing techniques have real evidence behind them for symptom and mood management",
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
            "label": "Worth prioritising",
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
}

SPECIALIST_MAP = {
    "menopause": {
        "name": "Practitioner",
        "expect": "A practitioner will typically review your full symptom picture, discuss hormone testing if relevant, and talk through the full range of options, HRT and non-hormonal, so you can choose what's right for you.",
    },
    "maternal": {
        "name": "Practitioner",
        "expect": "A practitioner will talk through how you're doing without judgement, help you understand what's typical for this stage, and guide you toward the right support, whether that's practical help, talking therapies, or something else.",
    },
    "strength": {
        "name": "Practitioner",
        "expect": "A practitioner can arrange a bone density scan or bloodwork if relevant, and help build you a safe, structured plan rather than leaving you to guess where to start.",
    },
    "preconception": {
        "name": "Practitioner",
        "expect": "A practitioner will review your cycle and lifestyle answers with you, and help you understand whether, and when, it's worth pursuing further investigations.",
    },
}

TRACK_EDUCATION = {
    "menopause": "Menopause is defined as twelve months without a period, usually happening between 45 and 55, though it can happen earlier. Perimenopause, the years leading up to it, is when oestrogen and progesterone levels start to fluctuate, and it's this fluctuation, not just the eventual drop, that drives most symptoms. It typically lasts four to eight years, though this varies widely. Around 80% of women experience some symptoms, and for roughly a quarter, those symptoms are severe enough to significantly affect daily life. Despite how common it is, menopause care has historically been under-discussed and under-treated, which is changing, but it means many people reach this stage without a clear sense of what's normal or what help is available.",
    "maternal": "Pregnancy and the first two years postnatal involve some of the most significant physical and hormonal change the body goes through. Around one in five women experience a mental health difficulty during pregnancy or in the year after birth, ranging from mild low mood to more significant anxiety or depression, making it one of the most common complications of this stage, not a rare or unusual one. Physical recovery also varies enormously and isn't limited to the first few weeks, many people are still adjusting physically and emotionally well beyond that. Screening and support at this stage are standard parts of NHS maternity and postnatal care, not an escalation or a sign that something has gone wrong.",
    "strength": "Bone density peaks around age 30 and gradually declines afterward, with the rate of loss accelerating for several years around menopause due to the drop in oestrogen, which plays a protective role in bone maintenance. Roughly one in two women over 50 will experience a fracture related to bone density at some point. The encouraging part is that bone health responds well to modifiable factors, weight-bearing exercise, resistance training, calcium and vitamin D intake, and avoiding smoking and excess alcohol all measurably affect long-term bone density, at any age. Falls risk and balance are equally important, since most fractures happen as a result of a fall, not spontaneously.",
    "preconception": "Fertility is influenced by a wide range of factors, cycle regularity, general health, age, and lifestyle among them. For couples with no known fertility issues, roughly 80 to 85% conceive within a year of regularly trying, and most of the remainder conceive within a further year. Folic acid supplementation before and during early pregnancy is one of the most well-evidenced preventative health measures available, meaningfully reducing the risk of certain birth defects. Lifestyle factors, smoking, regular alcohol, and high caffeine intake, have a real, measurable effect on fertility for both partners, which is why addressing them is one of the most useful things either partner can do while trying to conceive.",
}


TRACK_TITLES = {
    "menopause": "Menopause and Hormones",
    "maternal": "Maternal Wellbeing",
    "strength": "Bone, Brain and Strength",
    "preconception": "Preconception and Fertility",
}

OVERVIEW_BY_STAGE = {
    "Perimenopause": "You're in perimenopause, the transition phase before periods stop completely, which can last several years and bring a wide range of symptoms as hormone levels fluctuate.",
    "Menopause": "You're at menopause, defined as twelve months without a period, a natural transition that affects everyone differently.",
    "Postmenopause": "You're postmenopausal, past the transition itself, with the focus now on long-term health, particularly bone and heart health.",
    "Pregnant": "You're currently pregnant, a stage with real physical and emotional change, where checking in on how you're coping matters as much as the physical side.",
    "Postnatal (within 2 years)": "You're in the postnatal period, still very much a time of adjustment and recovery, even well beyond the earliest weeks.",
    "Trying to conceive": "You're trying to conceive, a stage where small, well-evidenced habits can genuinely support the process, alongside patience.",
    "None of these currently apply": "None of the specific life stages apply to you right now, so this report focuses on the areas relevant to everyone, longer-term strength and resilience.",
}


def build_report(life_stage: str, answers: dict) -> dict:
    """Returns the full per-track report as a plain dict, ready to store as JSON."""
    tracks = {}

    if life_stage in MENOPAUSE_STAGES:
        band = score_menopause(answers)
        reported_symptoms = [s for s in answers.get("symptoms", []) if s != "None of these"]
        tracks["menopause"] = {
            "title": TRACK_TITLES["menopause"],
            "band": band,
            **BAND_COPY["menopause"][band],
            "specialist": SPECIALIST_MAP["menopause"]["name"],
            "specialist_expect": SPECIALIST_MAP["menopause"]["expect"],
            "education": TRACK_EDUCATION["menopause"],
            "reported_symptoms": reported_symptoms,
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
        reported_factors = [f for f in answers.get("lifestyleFactors", []) if f != "None of these"]
        tracks["preconception"] = {
            "title": TRACK_TITLES["preconception"],
            "band": band,
            **BAND_COPY["preconception"][band],
            "specialist": SPECIALIST_MAP["preconception"]["name"],
            "specialist_expect": SPECIALIST_MAP["preconception"]["expect"],
            "education": TRACK_EDUCATION["preconception"],
            "reported_factors": reported_factors,
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

    overview = OVERVIEW_BY_STAGE.get(life_stage, "")

    return {"overview": overview, "tracks": tracks}

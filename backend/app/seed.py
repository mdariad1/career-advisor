"""Question-bank seeder for the surveys collection.

Run once to populate the DB, or call seed_surveys() in tests.
Questions are idempotent: seeding skips any that already exist (matched by question text).
"""
from __future__ import annotations

import logging
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)

# ── Likert scale shared across all personality questions ──────────────────────
_LIKERT = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]

# ── Aptitude MCQs (science / engineering / maths, grade 7+) ──────────────────
APTITUDE_QUESTIONS: list[dict] = [
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 8,
        "question": "What is the powerhouse of the cell?",
        "choices": ["Nucleus", "Mitochondria", "Ribosome", "Golgi apparatus"],
        "answer_index": 1,
        "lecture": "The mitochondria produce ATP via cellular respiration.",
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 7,
        "question": "What is the SI unit of electric current?",
        "choices": ["Volt", "Watt", "Ampere", "Ohm"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 8,
        "question": "Which type of bond holds water molecules to each other?",
        "choices": ["Ionic bond", "Covalent bond", "Hydrogen bond", "Metallic bond"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "engineering_aptitude_sample", "grade": 9,
        "question": "A train travels at 80 km/h for 2.5 hours. How far does it travel?",
        "choices": ["160 km", "180 km", "200 km", "220 km"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 9,
        "question": "What is the derivative of f(x) = x²?",
        "choices": ["x", "2x", "x²", "2"],
        "answer_index": 1,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 8,
        "question": "Which force keeps planets in orbit around the Sun?",
        "choices": ["Electromagnetism", "Nuclear force", "Gravity", "Friction"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "engineering_aptitude_sample", "grade": 8,
        "question": "Which material is the best electrical conductor?",
        "choices": ["Iron", "Copper", "Aluminium", "Silicon"],
        "answer_index": 1,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 7,
        "question": "What is the chemical formula for water?",
        "choices": ["H₂O₂", "HO", "H₂O", "OH₂"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "engineering_aptitude_sample", "grade": 9,
        "question": "In a series circuit, the total resistance is:",
        "choices": [
            "Less than the smallest resistor",
            "The sum of all resistors",
            "The product of all resistors",
            "Equal to the largest resistor",
        ],
        "answer_index": 1,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 9,
        "question": "Newton's second law states that Force equals:",
        "choices": ["mass × velocity", "mass × acceleration", "mass / acceleration", "velocity / time"],
        "answer_index": 1,
        "lecture": "F = ma",
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 7,
        "question": "What gas do plants absorb during photosynthesis?",
        "choices": ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 7,
        "question": "At what temperature does water boil at standard atmospheric pressure?",
        "choices": ["90 °C", "95 °C", "100 °C", "105 °C"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 8,
        "question": "What is the pH of a neutral solution at 25 °C?",
        "choices": ["0", "7", "10", "14"],
        "answer_index": 1,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 8,
        "question": "A moving object possesses which type of energy?",
        "choices": ["Potential", "Chemical", "Kinetic", "Nuclear"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 9,
        "question": "What is the process where a solid converts directly to a gas without passing through the liquid phase?",
        "choices": ["Evaporation", "Condensation", "Sublimation", "Melting"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "engineering_aptitude_sample", "grade": 9,
        "question": "In a right-angled triangle, sin(90°) equals:",
        "choices": ["0", "0.5", "√2/2", "1"],
        "answer_index": 3,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 10,
        "question": "DNA stands for:",
        "choices": [
            "Deoxyribonucleic acid",
            "Diribonucleic acid",
            "Deoxyribose nucleotide acid",
            "Dinuclear acid",
        ],
        "answer_index": 0,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 10,
        "question": "Which instrument measures electric current directly?",
        "choices": ["Voltmeter", "Ohmmeter", "Ammeter", "Galvanometer"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "engineering_aptitude_sample", "grade": 8,
        "question": "What is 2⁸?",
        "choices": ["64", "128", "256", "512"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 9,
        "question": "In which organ is the hormone insulin produced?",
        "choices": ["Liver", "Kidney", "Pancreas", "Thyroid"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 9,
        "question": "Sound waves are classified as which type of wave?",
        "choices": ["Transverse", "Longitudinal", "Electromagnetic", "Surface"],
        "answer_index": 1,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 7,
        "question": "What is the chemical symbol for iron?",
        "choices": ["Ir", "Fe", "In", "Fr"],
        "answer_index": 1,
    },
    {
        "survey_type": "aptitude", "source": "engineering_aptitude_sample", "grade": 9,
        "question": "Ohm's law defines the relationship between voltage (V), current (I), and resistance (R) as:",
        "choices": ["V = I / R", "V = I + R", "V = I × R", "V = I − R"],
        "answer_index": 2,
        "lecture": "V = IR",
    },
    {
        "survey_type": "aptitude", "source": "engineering_aptitude_sample", "grade": 10,
        "question": "Which sorting algorithm has an average time complexity of O(n log n)?",
        "choices": ["Bubble sort", "Insertion sort", "Merge sort", "Selection sort"],
        "answer_index": 2,
    },
    {
        "survey_type": "aptitude", "source": "scienceqa_sample", "grade": 10,
        "question": "What is the approximate speed of light in a vacuum?",
        "choices": ["3 × 10⁶ m/s", "3 × 10⁸ m/s", "3 × 10¹⁰ m/s", "3 × 10¹² m/s"],
        "answer_index": 1,
    },
]

# ── OCEAN Big Five personality questions (5 per dimension) ────────────────────
_LIKERT_SENTINEL = -1  # no single correct answer

PERSONALITY_QUESTIONS: list[dict] = [
    # ── Openness ──────────────────────────────────────────────────────────────
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I enjoy exploring new and unfamiliar ideas.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "openness", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I have little interest in art or creative work.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "openness", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I enjoy thinking about abstract concepts and theories.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "openness", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I strongly prefer familiar routines over novelty.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "openness", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I find philosophical discussions genuinely stimulating.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "openness", "polarity": 1},
    },
    # ── Conscientiousness ─────────────────────────────────────────────────────
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I always complete tasks fully before moving on to new ones.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "conscientiousness", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I often forget to put things back in their proper place.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "conscientiousness", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I like to plan tasks carefully before beginning them.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "conscientiousness", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I find it hard to stick to a schedule or structured routine.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "conscientiousness", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I pay very close attention to detail in everything I do.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "conscientiousness", "polarity": 1},
    },
    # ── Extraversion ──────────────────────────────────────────────────────────
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I feel energised after spending time with a large group of people.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "extraversion", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I prefer working alone rather than collaborating in a team.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "extraversion", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I enjoy being the centre of attention in social situations.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "extraversion", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I find making small talk at social events draining.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "extraversion", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I actively seek out opportunities to meet new people.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "extraversion", "polarity": 1},
    },
    # ── Agreeableness ─────────────────────────────────────────────────────────
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I try to be kind and considerate to everyone I meet.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "agreeableness", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I sometimes take advantage of others to get what I want.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "agreeableness", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I enjoy cooperating with others to reach a shared goal.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "agreeableness", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I tend to be overly critical of other people's efforts.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "agreeableness", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I feel genuine empathy when someone shares their problems with me.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "agreeableness", "polarity": 1},
    },
    # ── Neuroticism ───────────────────────────────────────────────────────────
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I often feel anxious or worried without a clear reason.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "neuroticism", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I stay calm and composed even under significant pressure.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "neuroticism", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "My mood can shift rapidly without an obvious trigger.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "neuroticism", "polarity": 1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I rarely feel down, depressed, or hopeless.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "neuroticism", "polarity": -1},
    },
    {
        "survey_type": "personality", "source": "ocean_big5_sample", "grade": None,
        "question": "I tend to dwell on negative experiences long after they have passed.",
        "choices": _LIKERT, "answer_index": _LIKERT_SENTINEL,
        "metadata": {"ocean_dimension": "neuroticism", "polarity": 1},
    },
]

ALL_QUESTIONS = APTITUDE_QUESTIONS + PERSONALITY_QUESTIONS

# ── Career archetype reference vectors ───────────────────────────────────────
# OCEAN vector: [Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism]
# nlp_centroid: placeholder zeros (replaced by trained MiniLM centroids in production)
# thematic_labels: subset of {analytical, creative, interpersonal, technical, leadership, structured}

_ZERO_CENTROID: list[float] = [0.0] * 384

CAREER_ARCHETYPES: list[dict] = [
    {
        "career_id": "software_engineer",
        "career_title": "Software Engineer",
        "ocean_vector": [0.65, 0.72, 0.45, 0.55, 0.30],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["technical", "analytical", "structured"],
        "market_demand_seed": 0.88,
        "sample_size": 450,
        "source": "theoretical_fallback",
    },
    {
        "career_id": "data_scientist",
        "career_title": "Data Scientist",
        "ocean_vector": [0.75, 0.68, 0.38, 0.50, 0.28],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["analytical", "technical", "structured"],
        "market_demand_seed": 0.85,
        "sample_size": 320,
        "source": "theoretical_fallback",
    },
    {
        "career_id": "ux_designer",
        "career_title": "UX Designer",
        "ocean_vector": [0.82, 0.60, 0.62, 0.72, 0.40],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["creative", "interpersonal", "analytical"],
        "market_demand_seed": 0.74,
        "sample_size": 210,
        "source": "theoretical_fallback",
    },
    {
        "career_id": "product_manager",
        "career_title": "Product Manager",
        "ocean_vector": [0.70, 0.65, 0.75, 0.68, 0.35],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["leadership", "interpersonal", "analytical"],
        "market_demand_seed": 0.80,
        "sample_size": 280,
        "source": "theoretical_fallback",
    },
    {
        "career_id": "mechanical_engineer",
        "career_title": "Mechanical Engineer",
        "ocean_vector": [0.55, 0.78, 0.48, 0.52, 0.30],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["technical", "structured", "analytical"],
        "market_demand_seed": 0.70,
        "sample_size": 360,
        "source": "theoretical_fallback",
    },
    {
        "career_id": "financial_analyst",
        "career_title": "Financial Analyst",
        "ocean_vector": [0.52, 0.80, 0.45, 0.50, 0.38],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["analytical", "structured"],
        "market_demand_seed": 0.72,
        "sample_size": 290,
        "source": "theoretical_fallback",
    },
    {
        "career_id": "biomedical_researcher",
        "career_title": "Biomedical Researcher",
        "ocean_vector": [0.78, 0.75, 0.40, 0.58, 0.35],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["analytical", "technical"],
        "market_demand_seed": 0.62,
        "sample_size": 180,
        "source": "theoretical_fallback",
    },
    {
        "career_id": "educator",
        "career_title": "Educator",
        "ocean_vector": [0.65, 0.68, 0.72, 0.82, 0.45],
        "nlp_centroid": _ZERO_CENTROID,
        "thematic_labels": ["interpersonal", "leadership", "structured"],
        "market_demand_seed": 0.58,
        "sample_size": 400,
        "source": "theoretical_fallback",
    },
]


async def seed_archetypes(col: AsyncIOMotorCollection) -> int:
    """Insert career archetypes that don't already exist (matched by career_id).

    Returns the number of newly inserted documents.
    """
    from datetime import datetime, UTC
    inserted = 0
    for arch in CAREER_ARCHETYPES:
        existing = await col.find_one({"career_id": arch["career_id"]})
        if existing is None:
            await col.insert_one({**arch, "updated_at": datetime.now(UTC)})
            inserted += 1
    if inserted:
        logger.info("Seeded %d career archetypes", inserted)
    return inserted


async def seed_surveys(col: AsyncIOMotorCollection) -> int:
    """Insert questions that don't already exist (matched by question text).

    Returns the number of newly inserted documents.
    """
    inserted = 0
    for q in ALL_QUESTIONS:
        existing = await col.find_one({"question": q["question"]})
        if existing is None:
            doc = {k: v for k, v in q.items() if v is not None}
            doc.setdefault("metadata", {})
            await col.insert_one(doc)
            inserted += 1
    if inserted:
        logger.info("Seeded %d survey questions", inserted)
    return inserted

"""SVM thematic classifier training script.

Trains a OneVsRestClassifier(SVC) on hand-crafted labeled sentences,
then saves the model bundle to models/svm_classifier.joblib.

Usage:
    python -m app.train
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import SVC

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

LABELS = ["analytical", "creative", "interpersonal", "technical", "leadership", "structured"]

# ── Training corpus ───────────────────────────────────────────────────────────
# Each entry: (text, [labels])  — multi-label, ~15 examples per primary label

TRAINING_DATA: list[tuple[str, list[str]]] = [
    # analytical
    ("I love breaking down complex problems into manageable components", ["analytical"]),
    ("Data analysis is at the heart of everything I do at work", ["analytical", "technical"]),
    ("I approach every task by first gathering evidence and evaluating options", ["analytical"]),
    ("Statistical modelling and hypothesis testing excite me", ["analytical", "technical"]),
    ("I enjoy finding patterns in large datasets", ["analytical"]),
    ("I think critically before drawing any conclusion", ["analytical"]),
    ("Research and evidence-based decisions drive my work", ["analytical"]),
    ("I like to compare multiple solutions before choosing the best approach", ["analytical", "structured"]),
    ("Logical reasoning and deductive thinking come naturally to me", ["analytical"]),
    ("I often build spreadsheets and models to understand trends", ["analytical", "technical"]),
    ("Evaluating trade-offs and risks is my favourite part of planning", ["analytical", "structured"]),
    ("I enjoy reading research papers and translating findings into action", ["analytical"]),
    ("My colleagues come to me when they need a rigorous analysis", ["analytical"]),
    ("I rely on facts and figures rather than gut feeling", ["analytical"]),
    ("Quantitative methods are my primary tool for decision-making", ["analytical", "technical"]),

    # creative
    ("I love brainstorming entirely new concepts and ideas", ["creative"]),
    ("Designing beautiful, intuitive user interfaces is my passion", ["creative"]),
    ("I find inspiration everywhere and constantly generate novel solutions", ["creative"]),
    ("Art, music, and visual design deeply influence my work", ["creative"]),
    ("I enjoy crafting compelling stories and visual narratives", ["creative"]),
    ("My best work happens when I have complete creative freedom", ["creative"]),
    ("I thrive on innovation and love challenging conventional thinking", ["creative"]),
    ("Ideation workshops and design sprints are where I shine", ["creative"]),
    ("I often sketch prototypes and mockups before writing any code", ["creative", "technical"]),
    ("I am drawn to projects that require an artistic or imaginative approach", ["creative"]),
    ("Exploring colour, typography, and layout energises me", ["creative"]),
    ("I like experimenting with new mediums and methods", ["creative"]),
    ("I find rigid processes stifling — I need room to innovate", ["creative"]),
    ("Coming up with a unique angle on a familiar problem is what I do best", ["creative"]),
    ("I see every constraint as an opportunity to get creative", ["creative"]),

    # interpersonal
    ("I genuinely enjoy working with and helping other people", ["interpersonal"]),
    ("Mentoring junior colleagues and watching them grow is deeply rewarding", ["interpersonal", "leadership"]),
    ("I communicate complex ideas clearly and empathetically", ["interpersonal"]),
    ("Team collaboration is where I produce my best results", ["interpersonal"]),
    ("I am highly attuned to the emotions and needs of those around me", ["interpersonal"]),
    ("Conflict resolution and facilitating productive conversations are my strengths", ["interpersonal", "leadership"]),
    ("I build trust quickly and maintain strong working relationships", ["interpersonal"]),
    ("Customer-facing roles energise me because I love connecting with people", ["interpersonal"]),
    ("I volunteer to run workshops and present to stakeholders", ["interpersonal", "leadership"]),
    ("Listening actively and giving useful feedback come naturally to me", ["interpersonal"]),
    ("I thrive in environments where collaboration is the norm", ["interpersonal"]),
    ("Human-centred design and user research align with my empathy for users", ["interpersonal", "creative"]),
    ("I enjoy team-building activities and social events at work", ["interpersonal"]),
    ("Coaching others to reach their potential is something I find deeply fulfilling", ["interpersonal", "leadership"]),
    ("I value diverse perspectives and make sure every voice is heard", ["interpersonal"]),

    # technical
    ("Writing clean, well-tested code is something I take great pride in", ["technical"]),
    ("I enjoy working close to the hardware and understanding system internals", ["technical"]),
    ("Debugging a tricky performance bottleneck is genuinely fun for me", ["technical", "analytical"]),
    ("I keep up with the latest developments in software engineering and cloud infrastructure", ["technical"]),
    ("Automating repetitive tasks with scripts saves me hours every week", ["technical"]),
    ("I love diving deep into documentation to understand how things work under the hood", ["technical"]),
    ("Building and deploying machine learning pipelines excites me", ["technical", "analytical"]),
    ("I prefer working with concrete implementations rather than abstract concepts", ["technical"]),
    ("Open source contributions and side projects keep my skills sharp", ["technical"]),
    ("Networking protocols, operating systems, and compilers fascinate me", ["technical"]),
    ("I enjoy setting up CI/CD pipelines and infrastructure as code", ["technical", "structured"]),
    ("Algorithm design and computational complexity are subjects I return to often", ["technical", "analytical"]),
    ("I can pick up a new programming language or framework quickly", ["technical"]),
    ("I appreciate elegant engineering solutions that solve hard problems efficiently", ["technical"]),
    ("I find satisfaction in making systems faster, more reliable, and more secure", ["technical", "structured"]),

    # leadership
    ("I naturally step up to lead when a project lacks direction", ["leadership"]),
    ("Setting a vision and rallying a team around it is where I excel", ["leadership"]),
    ("I am comfortable making difficult decisions under uncertainty", ["leadership"]),
    ("Strategic planning and aligning people with organisational goals energise me", ["leadership"]),
    ("I have led cross-functional teams through complex organisational change", ["leadership"]),
    ("I take responsibility for outcomes, including when things go wrong", ["leadership"]),
    ("People management and career development conversations are among my strengths", ["leadership", "interpersonal"]),
    ("I advocate for my team's needs when dealing with senior stakeholders", ["leadership"]),
    ("I enjoy identifying high-leverage opportunities and prioritising ruthlessly", ["leadership", "analytical"]),
    ("Inspiring others through my own commitment and example is a core value for me", ["leadership"]),
    ("I have experience building teams from scratch and defining their culture", ["leadership"]),
    ("Running effective meetings and keeping projects on track comes naturally to me", ["leadership", "structured"]),
    ("I can translate business strategy into actionable engineering or design work", ["leadership"]),
    ("Negotiating with stakeholders and managing conflicting priorities is part of my daily work", ["leadership"]),
    ("I see failure as a learning opportunity and encourage my team to take calculated risks", ["leadership"]),

    # structured
    ("I love creating detailed project plans with clear milestones and owners", ["structured"]),
    ("Processes, checklists, and standard operating procedures give me peace of mind", ["structured"]),
    ("I thrive when expectations are clear and deliverables are well-defined", ["structured"]),
    ("I meticulously document my work so others can follow and maintain it", ["structured"]),
    ("I use project management tools religiously to track every task and deadline", ["structured"]),
    ("I appreciate environments where priorities are stable and communication is formal", ["structured"]),
    ("Systematic testing and quality assurance are non-negotiable for me", ["structured", "technical"]),
    ("I break large goals into small, trackable sub-tasks", ["structured"]),
    ("Budgeting, forecasting, and financial modelling require the precision I value", ["structured", "analytical"]),
    ("I believe consistent processes are the foundation of scalable organisations", ["structured"]),
    ("Compliance, governance, and risk management align well with my attention to detail", ["structured"]),
    ("I keep my workspace and files meticulously organised", ["structured"]),
    ("I follow through on every commitment and dislike leaving things unfinished", ["structured"]),
    ("I prefer incremental, well-validated improvements over rapid chaotic change", ["structured"]),
    ("Regular retrospectives and process reviews are opportunities I look forward to", ["structured"]),
]


def train(output_path: str | None = None) -> Path:
    """Train the SVM classifier and save the bundle; return the saved path."""
    from .config import settings
    from .models import get_embedder

    save_path = Path(output_path or settings.classifier_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    texts = [t for t, _ in TRAINING_DATA]
    label_sets = [ls for _, ls in TRAINING_DATA]

    logger.info("Encoding %d training examples …", len(texts))
    embedder = get_embedder()
    X = embedder.encode(texts, show_progress_bar=False, batch_size=32)

    mlb = MultiLabelBinarizer(classes=LABELS)
    Y = mlb.fit_transform(label_sets)

    logger.info("Training OneVsRest SVM …")
    clf = OneVsRestClassifier(SVC(kernel="rbf", C=1.0, probability=True))
    clf.fit(X, Y)

    bundle = {"classifier": clf, "mlb": mlb, "labels": LABELS}
    joblib.dump(bundle, save_path)
    logger.info("Saved classifier bundle to %s", save_path)
    return save_path


if __name__ == "__main__":
    train()

// MongoDB initialisation script — runs once when the container is first created.
// Creates all collections and indexes defined in chapter3.tex Section 3.7.

db = db.getSiblingDB("career_db");

// ── Collections & indexes ────────────────────────────────────────────────────

db.createCollection("users");
db.users.createIndex({ email: 1 }, { unique: true });

db.createCollection("user_demographics");
// Kept separate from users; joined only in bias_audit pipeline (admin only)
db.user_demographics.createIndex({ user_id: 1 }, { unique: true });

db.createCollection("results");
db.results.createIndex({ user_id: 1 });
db.results.createIndex({ user_id: 1, survey_type: 1 });

db.createCollection("nlp_analysis");
db.nlp_analysis.createIndex({ user_id: 1 });
db.nlp_analysis.createIndex({ user_id: 1, session_id: 1 });

db.createCollection("weights");
// One document per user storing their current weight vector
db.weights.createIndex({ user_id: 1 }, { unique: true });

db.createCollection("recommendations");
db.recommendations.createIndex({ user_id: 1 });
db.recommendations.createIndex({ user_id: 1, created_at: -1 });

db.createCollection("jobs_snapshot");
db.jobs_snapshot.createIndex({ job_id: 1 }, { unique: true });
db.jobs_snapshot.createIndex({ industry: 1, country_code: 1 });
db.jobs_snapshot.createIndex({ synced_at: 1 });  // for stale-record pruning

db.createCollection("feedback");
db.feedback.createIndex({ user_id: 1 });
db.feedback.createIndex({ recommendation_id: 1 });

db.createCollection("sessions");
// Refresh-token revocation list
db.sessions.createIndex({ user_id: 1 });
db.sessions.createIndex({ token_hash: 1 }, { unique: true });
db.sessions.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

db.createCollection("career_archetypes");
db.career_archetypes.createIndex({ career_id: 1 }, { unique: true });

db.createCollection("surveys");
// Pre-loaded MCQ question bank (ScienceQA + Engineering Aptitude)
db.surveys.createIndex({ survey_type: 1 });
db.surveys.createIndex({ survey_type: 1, grade: 1 });

db.createCollection("bias_audit");
db.bias_audit.createIndex({ created_at: -1 });

print("career_db: all collections and indexes created.");

# Setup
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "q-hurl", "label": "Questions Hurl"}

HTTP 201

# Add question
POST http://localhost:8080/api/v1/quizzes/q-hurl/questions
Content-Type: application/json
{
  "question": "What is a Pod?",
  "choices": ["A. A node", "B. A container group", "C. A service", "D. A volume"],
  "answer": "B. A container group",
  "category": "Workloads"
}

HTTP 201
[Captures]
qid: jsonpath "$.id"
[Asserts]
jsonpath "$.question" == "What is a Pod?"
jsonpath "$.answer" == "B. A container group"

# Answer not in choices → 422
POST http://localhost:8080/api/v1/quizzes/q-hurl/questions
Content-Type: application/json
{
  "question": "Bad?",
  "choices": ["A. a", "B. b"],
  "answer": "C. not in list"
}

HTTP 422

# List
GET http://localhost:8080/api/v1/quizzes/q-hurl/questions

HTTP 200
[Asserts]
jsonpath "$" count == 1

# Filter by category
GET http://localhost:8080/api/v1/quizzes/q-hurl/questions?category=Workloads

HTTP 200
[Asserts]
jsonpath "$" count == 1

GET http://localhost:8080/api/v1/quizzes/q-hurl/questions?category=Storage

HTTP 200
[Asserts]
jsonpath "$" count == 0

# Update
PUT http://localhost:8080/api/v1/quizzes/q-hurl/questions/{{qid}}
Content-Type: application/json
{"category": "Core"}

HTTP 200
[Asserts]
jsonpath "$.category" == "Core"

# Delete single
DELETE http://localhost:8080/api/v1/quizzes/q-hurl/questions/{{qid}}

HTTP 200

# Bulk delete (empty set)
POST http://localhost:8080/api/v1/quizzes/q-hurl/questions
Content-Type: application/json
{"question": "Q?", "choices": ["A. a", "B. b"], "answer": "A. a"}

HTTP 201

DELETE http://localhost:8080/api/v1/quizzes/q-hurl/questions

HTTP 200
[Asserts]
jsonpath "$.deleted_count" == 1

# Teardown
DELETE http://localhost:8080/api/v1/quizzes/q-hurl

HTTP 200

# ── Deduplication: re-importing the same file must not create duplicate questions or categories ──
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-dedup", "label": "Dedup Test"}

HTTP 201

POST http://localhost:8080/api/v1/quizzes/hurl-dedup/import
[Multipart]
file: file,tests/fixtures/cka.yaml;text/yaml

HTTP 201
[Asserts]
jsonpath "$.imported" == 10
jsonpath "$.skipped" == 0

# Re-import same file — all must be skipped
POST http://localhost:8080/api/v1/quizzes/hurl-dedup/import
[Multipart]
file: file,tests/fixtures/cka.yaml;text/yaml

HTTP 201
[Asserts]
jsonpath "$.imported" == 0
jsonpath "$.skipped" == 10

# Question count must not be doubled (use show=all — cka.yaml has 1 disabled question)
GET http://localhost:8080/api/v1/quizzes/hurl-dedup/questions?show=all

HTTP 200
[Asserts]
jsonpath "$" count == 10

# Category filter must return a consistent subset (not doubled)
GET http://localhost:8080/api/v1/quizzes/hurl-dedup/questions?category=Workloads

HTTP 200
[Asserts]
jsonpath "$[*].category" contains "Workloads"

DELETE http://localhost:8080/api/v1/quizzes/hurl-dedup

HTTP 200

# ── disabled flag: filtering and toggle ──
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-disabled", "label": "Disabled Test"}

HTTP 201

# Add an enabled question
POST http://localhost:8080/api/v1/quizzes/hurl-disabled/questions
Content-Type: application/json
{"question": "Enabled Q?", "choices": ["A. yes", "B. no"], "answer": "A. yes"}

HTTP 201
[Captures]
qid_enabled: jsonpath "$.id"
[Asserts]
jsonpath "$.disabled" == false

# Add a disabled question
POST http://localhost:8080/api/v1/quizzes/hurl-disabled/questions
Content-Type: application/json
{"question": "Disabled Q?", "choices": ["A. yes", "B. no"], "answer": "B. no", "disabled": true}

HTTP 201
[Captures]
qid_disabled: jsonpath "$.id"
[Asserts]
jsonpath "$.disabled" == true

# Default (show=enabled): only the enabled question
GET http://localhost:8080/api/v1/quizzes/hurl-disabled/questions

HTTP 200
[Asserts]
jsonpath "$" count == 1
jsonpath "$[0].disabled" == false

# show=disabled: only the disabled question
GET http://localhost:8080/api/v1/quizzes/hurl-disabled/questions?show=disabled

HTTP 200
[Asserts]
jsonpath "$" count == 1
jsonpath "$[0].disabled" == true

# show=all: both
GET http://localhost:8080/api/v1/quizzes/hurl-disabled/questions?show=all

HTTP 200
[Asserts]
jsonpath "$" count == 2

# Toggle: re-enable the disabled question
PUT http://localhost:8080/api/v1/quizzes/hurl-disabled/questions/{{qid_disabled}}
Content-Type: application/json
{"disabled": false}

HTTP 200
[Asserts]
jsonpath "$.disabled" == false

# Now both should appear with default filter
GET http://localhost:8080/api/v1/quizzes/hurl-disabled/questions

HTTP 200
[Asserts]
jsonpath "$" count == 2

# Disable an enabled question via update
PUT http://localhost:8080/api/v1/quizzes/hurl-disabled/questions/{{qid_enabled}}
Content-Type: application/json
{"disabled": true}

HTTP 200
[Asserts]
jsonpath "$.disabled" == true

# Invalid show value → 422
GET http://localhost:8080/api/v1/quizzes/hurl-disabled/questions?show=invalid

HTTP 422

# Teardown
DELETE http://localhost:8080/api/v1/quizzes/hurl-disabled

HTTP 200

# ── disable persists immediately — regardless of quiz completion ──
# Simulates: user disables mid-quiz then exits without finishing
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-persist", "label": "Persist Test"}

HTTP 201

POST http://localhost:8080/api/v1/quizzes/hurl-persist/questions
Content-Type: application/json
{"question": "Mid-quiz Q?", "choices": ["A. yes", "B. no"], "answer": "A. yes"}

HTTP 201
[Captures]
persist_qid: jsonpath "$.id"

# Disable the question mid-quiz (simulate clicking "Never show again")
PUT http://localhost:8080/api/v1/quizzes/hurl-persist/questions/{{persist_qid}}
Content-Type: application/json
{"disabled": true}

HTTP 200
[Asserts]
jsonpath "$.disabled" == true

# Exit without finishing — just re-fetch (no score POST)
# Verify disabled flag persisted
GET http://localhost:8080/api/v1/quizzes/hurl-persist/questions?show=all

HTTP 200
[Asserts]
jsonpath "$[0].disabled" == true

# Default filter excludes it
GET http://localhost:8080/api/v1/quizzes/hurl-persist/questions

HTTP 200
[Asserts]
jsonpath "$" count == 0

DELETE http://localhost:8080/api/v1/quizzes/hurl-persist

HTTP 200

# ── important flag: filtering, toggle, and bulk unmark ──
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-important", "label": "Important Test"}

HTTP 201

# Add a normal question
POST http://localhost:8080/api/v1/quizzes/hurl-important/questions
Content-Type: application/json
{"question": "Normal Q?", "choices": ["A. yes", "B. no"], "answer": "A. yes"}

HTTP 201
[Captures]
qid_normal: jsonpath "$.id"
[Asserts]
jsonpath "$.important" == false

# Add an important question
POST http://localhost:8080/api/v1/quizzes/hurl-important/questions
Content-Type: application/json
{"question": "Important Q?", "choices": ["A. yes", "B. no"], "answer": "B. no", "important": true}

HTTP 201
[Captures]
qid_important: jsonpath "$.id"
[Asserts]
jsonpath "$.important" == true

# show=important: only the important question
GET http://localhost:8080/api/v1/quizzes/hurl-important/questions?show=important

HTTP 200
[Asserts]
jsonpath "$" count == 1
jsonpath "$[0].important" == true

# Default (show=enabled): both appear (important does not affect enabled filter)
GET http://localhost:8080/api/v1/quizzes/hurl-important/questions

HTTP 200
[Asserts]
jsonpath "$" count == 2

# Toggle: star the normal question
PUT http://localhost:8080/api/v1/quizzes/hurl-important/questions/{{qid_normal}}
Content-Type: application/json
{"important": true}

HTTP 200
[Asserts]
jsonpath "$.important" == true

# Now both are important
GET http://localhost:8080/api/v1/quizzes/hurl-important/questions?show=important

HTTP 200
[Asserts]
jsonpath "$" count == 2

# Bulk unmark
POST http://localhost:8080/api/v1/quizzes/hurl-important/questions/unmark-all-important

HTTP 200
[Asserts]
jsonpath "$.unmarked_count" == 2

# None important after bulk unmark
GET http://localhost:8080/api/v1/quizzes/hurl-important/questions?show=important

HTTP 200
[Asserts]
jsonpath "$" count == 0

# Invalid show value still 422
GET http://localhost:8080/api/v1/quizzes/hurl-important/questions?show=invalid

HTTP 422

# Teardown
DELETE http://localhost:8080/api/v1/quizzes/hurl-important

HTTP 200

# ── offset/range: slice questions by position ──
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-offset", "label": "Offset Test"}

HTTP 201

# Seed 5 questions in insertion order
POST http://localhost:8080/api/v1/quizzes/hurl-offset/questions
Content-Type: application/json
{"question": "Q1?", "choices": ["A. a", "B. b"], "answer": "A. a"}
HTTP 201

POST http://localhost:8080/api/v1/quizzes/hurl-offset/questions
Content-Type: application/json
{"question": "Q2?", "choices": ["A. a", "B. b"], "answer": "A. a"}
HTTP 201

POST http://localhost:8080/api/v1/quizzes/hurl-offset/questions
Content-Type: application/json
{"question": "Q3?", "choices": ["A. a", "B. b"], "answer": "A. a"}
HTTP 201

POST http://localhost:8080/api/v1/quizzes/hurl-offset/questions
Content-Type: application/json
{"question": "Q4?", "choices": ["A. a", "B. b"], "answer": "A. a"}
HTTP 201

POST http://localhost:8080/api/v1/quizzes/hurl-offset/questions
Content-Type: application/json
{"question": "Q5?", "choices": ["A. a", "B. b"], "answer": "A. a"}
HTTP 201

# Range 1-3: first 3 questions (offset=0, limit=3)
GET http://localhost:8080/api/v1/quizzes/hurl-offset/questions?limit=3&offset=0&show=all

HTTP 200
[Asserts]
jsonpath "$" count == 3
jsonpath "$[0].question" == "Q1?"
jsonpath "$[2].question" == "Q3?"

# Range 2-4: middle slice (offset=1, limit=3)
GET http://localhost:8080/api/v1/quizzes/hurl-offset/questions?limit=3&offset=1&show=all

HTTP 200
[Asserts]
jsonpath "$" count == 3
jsonpath "$[0].question" == "Q2?"
jsonpath "$[2].question" == "Q4?"

# Range 4-5: last 2 (offset=3, limit=2)
GET http://localhost:8080/api/v1/quizzes/hurl-offset/questions?limit=2&offset=3&show=all

HTTP 200
[Asserts]
jsonpath "$" count == 2
jsonpath "$[0].question" == "Q4?"
jsonpath "$[1].question" == "Q5?"

# Offset past end → empty
GET http://localhost:8080/api/v1/quizzes/hurl-offset/questions?limit=5&offset=10&show=all

HTTP 200
[Asserts]
jsonpath "$" count == 0

# Teardown
DELETE http://localhost:8080/api/v1/quizzes/hurl-offset

HTTP 200

# ── choice_explanations: stored, returned, and partially updated correctly ──
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-expl", "label": "Explanations Test"}

HTTP 201

# Add question with choice_explanations for all 4 choices
POST http://localhost:8080/api/v1/quizzes/hurl-expl/questions
Content-Type: application/json
{
  "question": "Which colour is the sky?",
  "choices": ["A. Red", "B. Blue", "C. Green", "D. Yellow"],
  "answer": "B. Blue",
  "choice_explanations": {
    "A": "Red is for sunsets, not the daytime sky.",
    "B": "Correct — Rayleigh scattering makes the sky appear blue.",
    "C": "Green skies indicate severe storms.",
    "D": "Yellow appears near the horizon at dusk."
  }
}

HTTP 201
[Captures]
expl_qid: jsonpath "$.id"
[Asserts]
jsonpath "$.choice_explanations.A" == "Red is for sunsets, not the daytime sky."
jsonpath "$.choice_explanations.B" == "Correct — Rayleigh scattering makes the sky appear blue."
jsonpath "$.choice_explanations.C" == "Green skies indicate severe storms."
jsonpath "$.choice_explanations.D" == "Yellow appears near the horizon at dusk."

# Fetch list — choice_explanations must be persisted
GET http://localhost:8080/api/v1/quizzes/hurl-expl/questions

HTTP 200
[Asserts]
jsonpath "$[0].choice_explanations.A" == "Red is for sunsets, not the daytime sky."
jsonpath "$[0].choice_explanations.B" == "Correct — Rayleigh scattering makes the sky appear blue."

# Add question without choice_explanations — field must be null
POST http://localhost:8080/api/v1/quizzes/hurl-expl/questions
Content-Type: application/json
{"question": "No explanations?", "choices": ["A. yes", "B. no"], "answer": "A. yes"}

HTTP 201
[Asserts]
jsonpath "$.choice_explanations" == null

# Update: add partial choice_explanations to the first question
PUT http://localhost:8080/api/v1/quizzes/hurl-expl/questions/{{expl_qid}}
Content-Type: application/json
{"choice_explanations": {"A": "Updated A.", "B": "Updated B."}}

HTTP 200
[Asserts]
jsonpath "$.choice_explanations.A" == "Updated A."
jsonpath "$.choice_explanations.B" == "Updated B."

# Teardown
DELETE http://localhost:8080/api/v1/quizzes/hurl-expl

HTTP 200

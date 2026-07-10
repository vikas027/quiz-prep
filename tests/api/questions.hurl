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

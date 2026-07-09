# Setup
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "score-hurl", "label": "Score Hurl"}

HTTP 201

# Record score
POST http://localhost:8080/api/v1/quizzes/score-hurl/scores
Content-Type: application/json
{"score": 8, "total": 10}

HTTP 201
[Asserts]
jsonpath "$.pct" == 80
jsonpath "$.score" == 8

# Record another
POST http://localhost:8080/api/v1/quizzes/score-hurl/scores
Content-Type: application/json
{"score": 9, "total": 10}

HTTP 201

# List — newest first
GET http://localhost:8080/api/v1/quizzes/score-hurl/scores

HTTP 200
[Asserts]
jsonpath "$[0].score" == 9
jsonpath "$[1].score" == 8
jsonpath "$" count == 2

# Limit
GET http://localhost:8080/api/v1/quizzes/score-hurl/scores?limit=1

HTTP 200
[Asserts]
jsonpath "$" count == 1

# Score for non-existent quiz -> 404
POST http://localhost:8080/api/v1/quizzes/ghost/scores
Content-Type: application/json
{"score": 5, "total": 10}

HTTP 404

# Teardown
DELETE http://localhost:8080/api/v1/quizzes/score-hurl

HTTP 200

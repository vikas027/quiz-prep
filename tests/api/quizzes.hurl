# Create a quiz set
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-test", "label": "Hurl Test"}

HTTP 201
[Asserts]
jsonpath "$.name" == "hurl-test"
jsonpath "$.label" == "Hurl Test"
jsonpath "$.id" isInteger

# Duplicate create → 409
POST http://localhost:8080/api/v1/quizzes
Content-Type: application/json
{"name": "hurl-test", "label": "Hurl Test"}

HTTP 409

# List — set appears
GET http://localhost:8080/api/v1/quizzes

HTTP 200
[Asserts]
jsonpath "$[*].name" contains "hurl-test"

# Import YAML
POST http://localhost:8080/api/v1/quizzes/hurl-test/import
[MultipartFormData]
file: file,tests/fixtures/claude.yaml; text/yaml

HTTP 201
[Asserts]
jsonpath "$.imported" > 0
jsonpath "$.skipped" == 0

# Export YAML
GET http://localhost:8080/api/v1/quizzes/hurl-test/export

HTTP 200
[Asserts]
header "content-type" contains "text/yaml"

# Delete
DELETE http://localhost:8080/api/v1/quizzes/hurl-test

HTTP 200
[Asserts]
jsonpath "$.deleted" == "hurl-test"

# Delete non-existent → 404
DELETE http://localhost:8080/api/v1/quizzes/hurl-test

HTTP 404

# Swagger UI is accessible at /swagger
GET http://localhost:8080/swagger

HTTP 200
[Asserts]
header "content-type" contains "text/html"

# OpenAPI schema is accessible
GET http://localhost:8080/openapi.json

HTTP 200
[Asserts]
jsonpath "$.info.title" == "Quiz API"

# /docs redirects to /docs/
GET http://localhost:8080/docs

HTTP 307

# MkDocs site is accessible at /docs/
GET http://localhost:8080/docs/

HTTP 200
[Asserts]
header "content-type" contains "text/html"

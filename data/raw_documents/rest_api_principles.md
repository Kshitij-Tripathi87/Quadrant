# REST API Design Principles and HTTP Semantics

A well-designed RESTful API adheres to standard HTTP status codes, uniform resource identifiers (URIs), and idempotent method semantics.

## 1. HTTP Methods and Idempotency
- **GET**: Safe and idempotent. Retrieves a representation of a resource without modifying server state.
- **POST**: Neither safe nor idempotent. Creates a new sub-resource or triggers an arbitrary operation. Repeated calls produce distinct resources or actions.
- **PUT**: Idempotent. Completely replaces the target resource at the given URI.
- **PATCH**: Partially updates a resource. May or may not be idempotent depending on the operation.
- **DELETE**: Idempotent. Deletes the target resource.

## 2. Standard HTTP Status Codes

### 2xx Success
- `200 OK`: Request succeeded, response entity included.
- `201 Created`: Resource successfully created, typically returned on `POST`.
- `204 No Content`: Action succeeded, no response body returned (e.g. after `DELETE`).

### 4xx Client Errors
- `400 Bad Request`: General malformed request or validation failure.
- `401 Unauthorized`: Request lacks valid authentication credentials.
- `403 Forbidden`: Authenticated user lacks permission for the resource.
- `404 Not Found`: Target resource URI does not exist.
- `422 Unprocessable Entity`: The request format was correct (e.g. valid JSON), but semantic validation failed (e.g. Pydantic validation error).
- `429 Too Many Requests`: Rate limit exceeded.

### 5xx Server Errors
- `500 Internal Server Error`: Unhandled exception on the server.
- `502 Bad Gateway`: Upstream service or LLM provider returned invalid response.
- `503 Service Unavailable`: Server or dependent service temporarily overloaded.

## 3. Feedback and Asynchronous Ingestion Patterns
In AI and RAG architectures:
- Feedback submission (`POST /feedback`) should return `200 OK` or `201 Created` with a structured confirmation.
- Document ingestion (`POST /ingest`) can accept file payloads or URLs, processing synchronously for small files or returning `202 Accepted` with a job tracking ID for large batch operations.

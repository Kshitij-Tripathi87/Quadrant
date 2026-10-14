# FastAPI Dependencies and Dependency Injection

FastAPI features an extremely powerful and intuitive **Dependency Injection** system. It allows developers to declare dependencies in path operation functions using `fastapi.Depends`.

## 1. What is Dependency Injection?
Dependency injection in software engineering means that your code declares what it needs (the dependencies) to work, and the framework takes care of providing them to your functions or classes at runtime.

### Key Benefits
- **Code Reuse**: Share database sessions, security logic, and authentication checks across endpoints.
- **Testability**: Easily override dependencies during automated testing with mock objects.
- **Modularity & Clean Code**: Keep endpoint functions lightweight and focused solely on request-response logic.

## 2. Basic Dependency Usage
To create a dependency, define a standard Python function and pass it to `Depends`:

```python
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

FastAPI automatically parses query parameters `q`, `skip`, and `limit`, executes `common_parameters`, and injects the returned dictionary into `read_items`.

## 3. Sub-dependencies and Dependency Trees
Dependencies can have their own dependencies, forming a hierarchical Directed Acyclic Graph (DAG) of dependencies:

```python
def query_extractor(q: str | None = None):
    return q

def query_or_cookie_extractor(
    q: Annotated[str, Depends(query_extractor)],
    last_query: Annotated[str | None, Cookie()] = None,
):
    if not q:
        return last_query
    return q
```

FastAPI resolves this tree in the correct topological order. If multiple sub-dependencies share a common dependency, FastAPI evaluates it only once per request by default (`use_cache=True`).

## 4. Dependencies with `yield` (Context Managers)
For resources requiring teardown or cleanup (such as database sessions, thread pools, or open files), FastAPI supports dependencies with `yield`:

```python
from sqlalchemy.orm import Session
from my_database import SessionLocal

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create(db, user_in)
    return db_user
```

### Execution Flow:
1. Code before `yield` runs before the path operation executes.
2. The yielded value is injected into the route function.
3. Code in the `finally` block runs after the response is sent to the client, guaranteeing resource cleanup even if an exception occurs during request processing.

## 5. Security & Authentication with Dependencies
FastAPI integrates security schemes (OAuth2 with Password flow, Bearer JWT, API Keys, HTTP Basic) directly via dependencies:

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user
```

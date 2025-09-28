from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from .schemas import Entry, Source, Score, EntryCreate
from .scoring_engine import calculate_trust_score, calculate_ai_slop_score
from services.security import auth
import datetime

app = FastAPI(title="Xikizpedia API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# In-memory database (for initial scaffolding)
db = {
    "entries": {},
    "sources": {},
    "scores": {},
    "users": {
        "testuser": {
            "username": "testuser",
            "full_name": "Test User",
            "email": "test@example.com",
            "hashed_password": "fakehashedpassword", # In a real app, use passlib
            "disabled": False,
        }
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Placeholder user authentication
    user = db['users'].get(form_data.username)
    if not user or user['hashed_password'] != "fakehashedpassword": # Placeholder check
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user['username']}
    )
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current user from a token.
    Validates token and returns user, or raises HTTPException.
    """
    payload = auth.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db['users'].get(username)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class ScoringRequest(BaseModel):
    content: str

@app.post("/internal/score-content/", response_model=Score)
def score_content(request: ScoringRequest):
    """
    Internal endpoint to calculate scores for a given block of text.
    """
    trust_score = calculate_trust_score(request.content)
    ai_slop_score = calculate_ai_slop_score(request.content)
    return Score(trust=trust_score, ai_slop=ai_slop_score)

@app.post("/entries/", response_model=Entry)
def create_entry(entry: EntryCreate, current_user: dict = Depends(get_current_user)):
    """
    Creates a new Xikizpedia entry. (Protected)
    Note: This is a placeholder. The full ingestion logic will be handled by the agent.
    """
    slug = entry.title.lower().replace(" ", "-")
    if slug in db["entries"]:
        raise HTTPException(status_code=400, detail="Entry with this title already exists.")

    # Use the scoring engine
    trust = calculate_trust_score(entry.content)
    ai_slop = calculate_ai_slop_score(entry.content)
    score = Score(trust=trust, ai_slop=ai_slop)

    source_id = len(db["sources"]) + 1
    source = Source(id=source_id, url=entry.url, analyzed_at=datetime.datetime.now(), score=score)
    db["sources"][source_id] = source

    entry_id = len(db["entries"]) + 1
    new_entry = Entry(
        id=entry_id,
        title=entry.title,
        slug=slug,
        abstract=entry.abstract,
        content=entry.content,
        source=source,
        created_at=datetime.datetime.now()
    )
    db["entries"][slug] = new_entry
    return new_entry

@app.get("/entries/{slug}", response_model=Entry)
def get_entry(slug: str):
    """
    Retrieves a Xikizpedia entry by its slug.
    """
    if slug not in db["entries"]:
        raise HTTPException(status_code=404, detail="Entry not found.")
    return db["entries"][slug]

@app.get("/leaderboard/", response_model=list[Source])
def get_leaderboard(current_user: dict = Depends(get_current_user)):
    """
    Retrieves a list of sources, ranked by trust score. (Protected)
    """
    sorted_sources = sorted(db["sources"].values(), key=lambda s: s.score.trust, reverse=True)
    return sorted_sources
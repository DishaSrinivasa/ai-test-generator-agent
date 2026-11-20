"""Human-review FastAPI server — approve or reject generated tests before CI."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="AI Test Generator — Review Gate")

APPROVED_TESTS_DIR = Path("approved_tests")
APPROVED_TESTS_DIR.mkdir(exist_ok=True)

_pending: dict[str, str] = {}  # name -> code


class SubmitRequest(BaseModel):
    name: str
    code: str


class ReviewDecision(BaseModel):
    approved: bool
    comment: str = ""


@app.post("/submit", status_code=202, summary="Submit generated tests for review")
def submit(req: SubmitRequest):
    _pending[req.name] = req.code
    return {"message": f"Tests '{req.name}' queued for review.", "pending_count": len(_pending)}


@app.get("/pending", summary="List tests awaiting review")
def list_pending():
    return {"pending": list(_pending.keys())}


@app.get("/pending/{name}", summary="View a pending test file")
def view_pending(name: str):
    if name not in _pending:
        raise HTTPException(404, "Not found")
    return {"name": name, "code": _pending[name]}


@app.post("/pending/{name}/decision", summary="Approve or reject a test file")
def decide(name: str, decision: ReviewDecision):
    if name not in _pending:
        raise HTTPException(404, "Not found")
    code = _pending.pop(name)
    if decision.approved:
        out = APPROVED_TESTS_DIR / f"{name}.py"
        out.write_text(code)
        return {"status": "approved", "saved_to": str(out)}
    return {"status": "rejected", "comment": decision.comment}

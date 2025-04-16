from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore
from typing import Annotated
import datetime

app = FastAPI()

# mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
templates = Jinja2Templates(directory="/app/template")

# init firestore client
db = firestore.Client()
votes_collection = db.collection("votes")

@app.get("/")
async def read_root(request: Request):
    tabs_counter = 0
    spaces_counter = 0
    recent_votes = []
    try:
        votes = votes_collection.stream()

        for v in votes:
            vote = v.to_dict()
            team = vote.get("team")
            time_cast = vote.get("time_cast")

            # Skip if no team or time_cast
            if not team or not time_cast:
                continue

            recent_votes.append({
                "team": team,
                "time_cast": time_cast
            })

            if team == "TABS":
                tabs_counter += 1
            elif team == "SPACES":
                spaces_counter += 1

        # sort by most recent safely
        recent_votes.sort(key=lambda x: x.get("time_cast", ""), reverse=True)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "tabs_count": tabs_counter,
            "spaces_count": spaces_counter,
            "recent_votes": recent_votes
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/")
async def create_vote(team: Annotated[str, Form()]):
    if team not in ["TABS", "SPACES"]:
        raise HTTPException(status_code=400, detail="Invalid vote")
    
    try:
        vote = {
            "team": team,
            "time_cast": datetime.datetime.utcnow().isoformat()
        }
        votes_collection.add(vote)
        return {"detail": "Created a new vote!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

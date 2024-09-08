from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from starlette.responses import RedirectResponse

# Initialize the FastAPI app
app = FastAPI()

# Mount static files (for CSS, JavaScript, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates directory
templates = Jinja2Templates(directory="static")

# Dummy database for storing client and case data (replace with actual database logic)
clients = []
cases = []

# Data models
class Client(BaseModel):
    id: int
    name: str
    email: str

class Case(BaseModel):
    id: int
    client_id: int
    description: str
    status: str = "New"

# Routes
@app.get("/")
async def index(request: Request):
    """Landing page with options to sign up or log in."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
async def dashboard(request: Request):
    """Dashboard displaying active cases and client information."""
    return templates.TemplateResponse("dashboard.html", {"request": request, "cases": cases})

@app.post("/create_case")
async def create_case(request: Request, description: str = Form(...)):
    """Route for creating a new case from the client side."""
    case_id = len(cases) + 1
    new_case = Case(id=case_id, client_id=1, description=description)  # Dummy client_id, use actual logic here
    cases.append(new_case)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/case/{case_id}")
async def view_case(request: Request, case_id: int):
    """View case details with AI insights and suggestions."""
    case = next((c for c in cases if c.id == case_id), None)
    if not case:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return templates.TemplateResponse("case_detail.html", {"request": request, "case": case})

@app.post("/client_signup")
async def client_signup(request: Request, name: str = Form(...), email: str = Form(...)):
    """Client sign-up page."""
    client_id = len(clients) + 1
    new_client = Client(id=client_id, name=name, email=email)
    clients.append(new_client)
    return RedirectResponse(url="/dashboard", status_code=303)

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

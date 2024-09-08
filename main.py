from http.client import HTTPException
import logging
from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from starlette.responses import RedirectResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os
import logging
from fastapi.responses import JSONResponse

load_dotenv()
# Initialize the FastAPI app
app = FastAPI()

print(os.getenv("API_KEY"))
client = Groq(api_key=os.getenv("API_KEY"))


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

# @app.get("/dashboard")
# async def dashboard(request: Request):
#     """Dashboard displaying active cases and client information."""
#     return templates.TemplateResponse("dashboard.html", {"request": request, "cases": cases})

@app.get("/client_dashboard")
async def client_dashboard(request: Request):
    """Dashboard displaying active cases and client information."""
    return templates.TemplateResponse("client_dashboard.html", {"request": request, "cases": cases})

@app.get("/lawyer_dashboard")
async def lawyer_dashboard(request: Request):
    """Dashboard displaying active cases and client information."""
    return templates.TemplateResponse("lawyer_dashboard.html", {"request": request, "cases": cases})

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



# Logger setup for monitoring API requests and responses
logging.basicConfig(level=logging.INFO)
# Function to communicate with the Groq LLM
async def call_groq_llm(user_input: str):
    """
    Function to send formatted client data to Groq LLM and stream the response.
    """
    try:
        # Create the LLM completion request
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a legal assistant AI designed to help parse and organize information about legal cases "
                        "provided by clients. Your task is to extract and summarize the key details of the case, including "
                        "relevant facts, requirements, and any specific requests made by the client. Ignore any irrelevant "
                        "or non-informative input that does not pertain to the case. Focus on identifying the key elements:\n\n"
                        "1. **Client Details:**\n   - Name: (If provided)\n   - Contact Information: Email, phone number, etc. (if provided)\n\n"
                        "2. **Case Description:**\n   - A concise summary of the incident or issue the client is facing.\n"
                        "   - Key facts related to the case (e.g., dates, locations, involved parties).\n\n"
                        "3. **Requirements:**\n   - What the client is seeking (e.g., legal representation, advice on next steps, compensation claims).\n"
                        "   - Any specific requests or instructions related to the case.\n\n"
                        "4. **Important Context or Background:**\n   - Any additional context that helps in understanding the case better.\n\n"
                        "5. **Ignore and exclude:**\n   - Unrelated or off-topic information.\n   - Repetitive or irrelevant text that does not contribute to understanding the case.\n"
                    )
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        message_content = completion.choices[0].message.content

        # Iterate over the response stream
        return message_content

    except Exception as e:
        # logging.error(f"Error communicating with LLM: {e}")
        # Correct way to raise HTTPException with appropriate message
        raise HTTPException("some error")


# API endpoint to process client information and send to Groq LLM
@app.post("/process-client-info")
async def process_client(request: Request, description: str = Form(...)):
    """
    API endpoint that accepts client data, formats it, and sends it to the LLM.
    """
    # Extract form data from the request
    form = await request.form()
    name = form.get('name', 'Unknown')  # Default to 'Unknown' if not provided
    contact = form.get('contact', 'Not provided')  # Default to 'Not provided' if not given

    # Prepare the user input for the LLM
    user_input = f"Client Name: {name}\nContact Information: {contact}\nCase Description: {description}"

    # Create a StreamingResponse to send data as it is received from LLM
    response_content = await call_groq_llm(user_input)

    # Return the response as JSON
    return JSONResponse(content={"response": response_content})

    


# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

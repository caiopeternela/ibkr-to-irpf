import uvicorn
from typing import Any
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


class StatementResponse(BaseModel):
    filename: str


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/statements", response_model=StatementResponse)
async def process_statement(statement: UploadFile) -> Any:
    return {"filename": statement.filename}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

import uvicorn
from typing import Any
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

app.mount("/static", StaticFiles(directory="src/static"), name="static")

templates = Jinja2Templates(directory="src/templates")


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

from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mangum import Mangum

from src.calculator import calculate_holdings
from src.parser import parse_statement

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
handler = Mangum(app, lifespan="off")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def format_brl(value: Decimal) -> str:
    """Format a Decimal value as Brazilian Real currency."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_usd(value: Decimal) -> str:
    """Format a Decimal value as US Dollar currency."""
    return f"US${value:,.2f}"


# Add custom filters to Jinja2
templates.env.filters["format_brl"] = format_brl
templates.env.filters["format_usd"] = format_usd


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/statements", response_class=HTMLResponse)
async def process_statement(request: Request, statement: UploadFile):
    """Process an IBKR CSV statement and return holdings data."""
    try:
        content = await statement.read()
        content_str = content.decode("utf-8-sig")  # Handle BOM if present

        # Parse the statement
        trades, instrument_info = parse_statement(content_str)

        if not trades:
            return templates.TemplateResponse(
                request=request,
                name="results.html",
                context={"error": "No buy trades found in the statement."},
            )

        # Determine the year from trades
        year = max(t.trade_date for t in trades).year

        # Filter trades up to Dec 31 of the year
        end_of_year = date(year, 12, 31)
        filtered_trades = [t for t in trades if t.trade_date <= end_of_year]

        # Calculate holdings with PTAX rates
        holdings = calculate_holdings(filtered_trades, instrument_info)

        # Prepare template context
        context = {
            "holdings": holdings,
            "year": year,
            "total_trades": len(filtered_trades),
            "total_usd": sum(h.total_acquisition_usd for h in holdings),
            "total_brl": sum(h.total_acquisition_brl for h in holdings),
        }

        return templates.TemplateResponse(
            request=request,
            name="results.html",
            context=context,
        )

    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="results.html",
            context={"error": f"Error processing statement: {str(e)}"},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

# 🦁 IBKR to IRPF

A minimalist tool to process Interactive Brokers (IBKR) statements for Brazilian Income Tax (IRPF) purposes 🦁

## What it does

This tool parses IBKR CSV statements and calculates the data needed for your IRPF declaration of foreign investments ("Bens e Direitos" section). It automatically:

- Extracts all buy operations from your statement
- Fetches the PTAX sell rate from Banco Central do Brasil for each transaction date
- Calculates total acquisition values in both USD and BRL
- Computes average acquisition costs

## Output

For each holding, the tool provides:

- **Quantidade** - Total shares held
- **Total (USD)** - Total acquisition value in USD
- **Total (BRL)** - Total acquisition value in BRL (using PTAX rate at each purchase date)
- **Custo Médio (USD/BRL)** - Average cost per share

You can also expand each holding to see all individual trades with their respective PTAX rates.

## Installation

```bash
git clone https://github.com/caiopeternela/ibkr-to-irpf.git
cd ibkr-to-irpf
uv sync
```

## Usage

```bash
uv run uvicorn src.main:app --reload
```

Then open http://localhost:8000 and upload your IBKR CSV statement.

### Getting your IBKR Statement

1. Log in to **Client Portal** at IBKR
2. Go to **Performance & Reports** → **Statements**
3. Select **Activity** statement type
4. Choose period: **Annual** for the tax year
5. Select format: **CSV**

## How PTAX Works

For each buy operation, the tool fetches the PTAX sell rate (taxa de venda) from BCB's SGS API. This is the official exchange rate used for tax purposes in Brazil.

If a transaction occurs on a weekend or holiday, the tool uses the most recent available business day's rate.

## Project Structure

```
src/
├── main.py        # FastAPI application
├── models.py      # Data classes (Trade, Holding)
├── parser.py      # IBKR CSV statement parser
├── ptax.py        # BCB PTAX rate fetcher
├── calculator.py  # BRL conversion and aggregation logic
├── tests.py       # Test suite
├── templates/     # Jinja2 HTML templates
└── static/        # CSS styles
```

## Running Tests

```bash
uv run pytest src/tests.py
```

## Limitations

- Currently only supports **buy operations** (no sell operations or capital gains calculation)
- Only processes **stocks/ETFs** (no options, futures, etc.)
- Assumes all transactions are in **USD**

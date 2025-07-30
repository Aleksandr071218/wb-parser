from fastapi import FastAPI, Query
from selenium_parser.parsers.wildberries_price_range_parser import run_price_range_parser

app = FastAPI(title="Wildberries Price Range Parser API")

@app.get("/parse/")
def parse(
    url: str = Query(..., description="Link to Wildberries category"),
    step: float = Query(5000, description="Price step"),
    max_products: int = Query(6000, description="Maximum number of products in one block"),
):
    try:
        run_price_range_parser(url=url, step=step, max_products=max_products)
        return {
            "status": "Parsing completed successfully",
            "url": url,
            "step": step,
            "max_products": max_products
        }
    except Exception as e:
        return {"error": str(e)}

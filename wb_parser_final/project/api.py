from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from selenium_parser.parsers.wildberries_price_range_parser import run_price_range_parser
from db import client

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
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/products/")
def get_products():
    try:
        # Fetch data and column descriptions
        result = client.query("SELECT * FROM wildberries_products_parsed")

        # Manually construct JSON to handle potential data type issues
        column_names = [desc[0] for desc in result.column_descriptions]
        products = [dict(zip(column_names, row)) for row in result.result_rows]

        return JSONResponse(content=products)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

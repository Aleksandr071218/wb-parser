from fastapi import FastAPI, Query
from selenium_parser.parsers.wildberries_price_range_parser import run_price_range_parser

app = FastAPI(title="API для парсера ценовых диапазонов Wildberries")

@app.get("/parse/")
def parse(
    url: str = Query(..., description="Ссылка на категорию Wildberries"),
    step: float = Query(5000, description="Шаг цены"),
    max_products: int = Query(6000, description="Максимальное количество товаров в одном блоке"),
):
    try:
        run_price_range_parser(url=url, step=step, max_products=max_products)
        return {
            "status": "Парсинг успешно завершен",
            "url": url,
            "step": step,
            "max_products": max_products
        }
    except Exception as e:
        return {"error": str(e)}

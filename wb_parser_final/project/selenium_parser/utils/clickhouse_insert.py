from clickhouse_connect import get_client

client = get_client(
    host='',        # 🔁 Замените, если не localhost
    port=0000,
    username='',      # 🔁 Ваше имя пользователя
    password='',             # 🔁 Ваш пароль
    database=''
)

def parse_category_levels(category_raw: str):
    parts = category_raw.split('_')
    category = parts[-1]  # последняя часть как основная категория

    # L1 = последняя часть, L2 = предпоследняя и т.д.
    levels = [None, None, None, None]  # L1, L2, L3, L4

    # Заполняем уровни в обратном порядке
    for i, part in enumerate(reversed(parts)):
        if i < 4:
            levels[i] = part

    return category, levels

def insert_product_if_new(data: dict):
    # Получаем данные с запасными значениями
    article = data.get("article", "")
    product_url = data.get("link", "")
    category_raw = data.get("category", "")

    # Пропускаем, только если нет артикула (основной идентификатор)
    if not article:
        print("⚠️ Пропущено: нет артикула", data)
        return

    try:
        result = client.query(
            "SELECT count() FROM wildberries_products_parsed WHERE article = %(article)s",
            parameters={'article': article}
        )
        existing = result.result_rows[0][0] if result.result_rows else 0

        if existing > 0:
            print(f"⏭ Уже существует: {article}")
            return
    except Exception as check_e:
        print(f"⚠️ Ошибка при проверке существования {article}: {check_e}")
        # Продолжаем вставку, если не удалось проверить

    # Обрабатываем категорию (даже если она пустая)
    if category_raw:
        category, (category_l1, category_l2, category_l3, category_l4) = parse_category_levels(category_raw)
    else:
        category = ""
        category_l1 = ""
        category_l2 = ""
        category_l3 = ""
        category_l4 = ""

    # Сопоставляем с фактической структурой таблицы (8 столбцов)
    insert_data = (
        article or "",           # article
        product_url or "",      # product_url
        category_raw or "",     # category_raw
        category or "",         # category
        category_l1 or "",      # category_l1
        category_l2 or "",      # category_l2
        category_l3 or "",      # category_l3
        category_l4 or ""       # category_l4
    )

    try:
        result = client.insert(
            table='wildberries_products_parsed',
            data=[insert_data],
            column_names=['article', 'product_url', 'category_raw', 'category', 'category_l1', 'category_l2', 'category_l3', 'category_l4']
        )
        print(f"✅ Добавлено: {article}")
    except Exception as e:
        error_msg = str(e) if str(e) != '0' else 'Неизвестная ошибка ClickHouse'
        print(f"❌ Ошибка при вставке товара {article}: {error_msg}")
        print(f"🧾 Тип ошибки: {type(e).__name__}")
        print(f"🧾 Данные: {insert_data}")

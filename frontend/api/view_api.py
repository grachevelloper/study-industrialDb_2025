# Создание API
from db_manager import DBManager
db_manager = DBManager("database.db")
view_api = ViewAPI(db_manager)

# 1. Получение списка представлений
views = view_api.get_all_views()
for view in views:
    print(f"{view['name']} - {view['type']}")

# 2. Создание представления
success, message = view_api.create_view(
    view_name="attack_summary",
    query="SELECT attack_type, COUNT(*) FROM attacks GROUP BY attack_type"
)

# 3. Получение данных из представления
data = view_api.get_view_data("attack_summary", limit=10)

# 4. Обновление материализованного представления
if view_api._is_materialized_view("attack_stats"):
    success, message = view_api.refresh_materialized_view("attack_stats")

# 5. Экспорт определения
success, message, sql = view_api.export_view_definition(
    view_name="attack_summary",
    format="sql"
)
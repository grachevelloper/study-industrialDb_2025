# Создание построителя запросов
qb = QueryBuilder("sqlite")

# Группировка с ROLLUP
grouping_query = qb.build_grouping_query(
    table_name="attacks",
    group_columns=["attack_type", "severity"],
    aggregate_functions=[
        {"column": "*", "function": "COUNT", "alias": "count"},
        {"column": "danger", "function": "AVG", "alias": "avg_danger"}
    ],
    grouping_type="ROLLUP"
)

# Создание материализованного представления
mv_query = qb.build_view_query(
    view_name="attack_stats",
    select_query="SELECT attack_type, COUNT(*) FROM attacks GROUP BY attack_type",
    is_materialized=True
)

# CTE с рекурсией
cte_query = qb.build_cte_query(
    cte_definitions=[...],
    main_query="SELECT * FROM hierarchy",
    recursive=True
)
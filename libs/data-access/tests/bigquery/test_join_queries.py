from unittest.mock import Mock

import pytest
from aiohttp import ClientSession
from gcloud.aio.auth import Token

import data_access.bigquery.schema as schema
from data_access.bigquery.service import BigqueryService


class TestBigqueryJoin:

    # Join two queries with INNER JOIN on a single column
    @pytest.mark.asyncio
    async def test_inner_join_single_column(self):
        async with ClientSession() as session:
            auth_token = Token()
            left_query = schema.BigqueryQuery(
                table_name=schema.BigqueryIdentifier("table1"),
                columns=(schema.BigqueryIdentifier("column1"), schema.BigqueryIdentifier("column2")),
                filters=(schema.BigqueryFilter(query_str="column1 = 10"),),
            )
            right_query = schema.BigqueryQuery(
                table_name=schema.BigqueryIdentifier("table2"),
                columns=(schema.BigqueryIdentifier("column3"), schema.BigqueryIdentifier("column4")),
                filters=(schema.BigqueryFilter(query_str="column3 > 10"),),
            )

            join_type = schema.JoinType.INNER
            on = ["column1"]
            bigquery_service = BigqueryService(project_id="my_project", session=session, token=auth_token)

            result_query = await bigquery_service.join_queries(left_query, right_query, join_type, on)
            query_postprocessed = " ".join(result_query.query.split())
            expected_query = (
                "WITH table_0 as ( SELECT column1, column2 FROM table1 WHERE column1 = 10 ), "
                "table_1 as ( SELECT column3, column4 FROM table2 WHERE column3 > 10 ) "
                "SELECT * FROM table_0 INNER JOIN table_1 USING (column1)"
            )

            assert query_postprocessed == expected_query

    @pytest.mark.asyncio
    async def test_inner_join_multiple_columns(self):
        async with ClientSession() as session:
            auth_token = Token()
            left_query = schema.BigqueryQuery(
                table_name=schema.BigqueryIdentifier("table1"),
                columns=(schema.BigqueryIdentifier("column1"), schema.BigqueryIdentifier("column2")),
                filters=(schema.BigqueryFilter(query_str="column1 = 10"),),
            )
            right_query = schema.BigqueryQuery(
                table_name=schema.BigqueryIdentifier("table2"),
                columns=(schema.BigqueryIdentifier("column1"), schema.BigqueryIdentifier("column2")),
                filters=(schema.BigqueryFilter(query_str="column2 > 10"),),
            )

            join_type = schema.JoinType.INNER
            on = ["column1", "column2"]
            bigquery_service = BigqueryService(project_id="my_project", session=session, token=auth_token)

            result_query = await bigquery_service.join_queries(left_query, right_query, join_type, on)
            query_postprocessed = " ".join(result_query.query.split())
            expected_query = (
                "WITH table_0 as ( SELECT column1, column2 FROM table1 WHERE column1 = 10 ), "
                "table_1 as ( SELECT column1, column2 FROM table2 WHERE column2 > 10 ) "
                "SELECT * FROM table_0 INNER JOIN table_1 USING (column1,column2)"
            )

            assert query_postprocessed == expected_query
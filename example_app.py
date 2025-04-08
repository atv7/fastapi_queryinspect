from fastapi import FastAPI
from fastapi_queryinspect import QueryInspect

app = FastAPI()
query_inspect = QueryInspect(app)

query_inspect = QueryInspect()
query_inspect.configure(QUERYINSPECT_LOG=False)
query_inspect.init_app(app)

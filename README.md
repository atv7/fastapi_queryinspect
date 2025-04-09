# fastapi_queryinspect

FastAPI-QueryInspect is a FastAPI extension that provides SQL query metrics and analysis
per request, inspired by Flask-QueryInspect (https://github.com/noise/flask-queryinspect) and
Django-QueryInspect (https://github.com/dobarkod/django-queryinspect).
It tracks query performance, identifies slow queries and duplicate table access,
and works with SQLAlchemy to offer detailed timing stats and request-level SQL insights

# Installation #

```
pip install fastapi-queryinspect
```

## Usage ##

```python
app = FastAPI()
query_inspect = QueryInspect(app)
```

## Configuration ##

QueryInspect has the following optional config vars that can be set in
Flask's app.config:

Variable | Default | Description
------------- | ------------- | -------------
QUERYINSPECT_ENABLED | True | False to completely disable QueryInspect
QUERYINSPECT_HEADERS | True | Enable response header injection
QUERYINSPECT_LOG | True | Enable logging
QUERYINSPECT_SLOW_THRESHOLD | 0.5 | Show queries >= 0.5s
QUERYINSPECT_DUPLICATE_LIMIT | 5 | Show queries after 5 duplicates


## Log Format ##

```
[SQL] %d queries (%d duplicates), %d ms SQL time, %d ms total request time
```

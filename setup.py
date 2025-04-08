from setuptools import setup, find_packages


"""
FastAPI-QueryInspect is a FastAPI extension that provides SQL query metrics and analysis
per request, inspired by Flask-QueryInspect (https://github.com/noise/flask-queryinspect) and
Django-QueryInspect (https://github.com/dobarkod/django-queryinspect).
It tracks query performance, identifies slow queries and duplicate table access,
and works with SQLAlchemy to offer detailed timing stats and request-level SQL insights.
Source: https://github.com/atv7/fastapi_queryinspect
"""

setup(
    name="fastapi-queryinspect",
    version="0.1.0",
    url="https://github.com/atv7/fastapi_queryinspect",
    license="MIT",
    author="Artem",
    author_email="ateter17@gmail.com",
    description="FastAPI middleware to provide metrics on SQL queries per request.",
    long_description=__doc__,
    py_modules=["fastapi_queryinspect"],
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    install_requires=[
        "fastapi",
        "sqlalchemy",
    ],
    extras_require={
        "test": [
            "httpx",
            "pytest",
            "pytest-asyncio",
            "uvicorn",
        ],
    },
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: FastAPI",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
)

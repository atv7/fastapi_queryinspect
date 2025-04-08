import logging
import time
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Integer, Unicode
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from fastapi_queryinspect import QueryInspect

log = logging.getLogger(__name__)

Base = declarative_base()


class TestModel(Base):
    __tablename__ = "test_model"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    foo: Mapped[Unicode] = mapped_column(Unicode(10))

    def __init__(self, foo):
        self.foo = foo


class TestQueryInspect(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(format="%(asctime)-15s %(levelname)s %(message)s")
        logging.getLogger("fastapi_queryinspect").setLevel(logging.DEBUG)
        logging.getLogger("test_queryinspect").setLevel(logging.DEBUG)

        cls.app = FastAPI()
        cls.queryinspect = QueryInspect(cls.app)
        cls.queryinspect.configure(
            QUERYINSPECT_HEADERS=True,
            QUERYINSPECT_HEADERS_COMBINED=True,
        )

        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

        with cls.Session() as session:
            for i in range(10):
                session.add(TestModel(f"test_{i}"))
            session.commit()

        @cls.app.get("/")
        async def index():
            return "No Queries"

        @cls.app.get("/mix")
        async def mix():
            with cls.Session() as session:
                t = session.query(TestModel).first()
                t.foo = "bar"
                session.commit()

                return "Reads and writes"

        cls.client = TestClient(cls.app)

    def test_noqueries(self):
        res = self.client.get("/")
        log.debug(res.headers)
        header = res.headers.get("x-queryinspect-combined")
        self.assertIsNotNone(header)
        self.assertTrue(header.startswith("reads=0,writes=0,conns=0"))

    def test_mix(self):
        res = self.client.get("/mix")
        log.debug(res.headers)
        header = res.headers.get("x-queryinspect-combined")
        self.assertIsNotNone(header)
        self.assertTrue(header.startswith("reads=1,writes=1"))


if __name__ == "__main__":
    unittest.main()

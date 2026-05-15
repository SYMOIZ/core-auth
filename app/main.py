from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import create_all_tables, dispose_engine
from app.db.redis import init_redis, close_redis
from app.api.routes import auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_all_tables()
    await init_redis()
    print("[OK] Database tables ready")
    print("[OK] Redis connection established")
    yield
    # Shutdown
    await close_redis()
    await dispose_engine()
    print("[DOWN] Redis connection closed")
    print("[DOWN] Database engine disposed")


app = FastAPI(
    title="Core-Auth API",
    description="High-performance async authentication & authorization engine",
    version="1.4.2",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "Core-Auth is running", "version": "1.4.2"}

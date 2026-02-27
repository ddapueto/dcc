from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dcc.config import settings
from dcc.db.database import close_db, init_db
from dcc.db.seed import seed_defaults


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_defaults()
    yield
    await close_db()


app = FastAPI(title="DCC — Dev Command Center", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from dcc.api.routes.analytics import router as analytics_router  # noqa: E402
from dcc.api.routes.config import router as config_router  # noqa: E402
from dcc.api.routes.github import router as github_router  # noqa: E402
from dcc.api.routes.health import router as health_router  # noqa: E402
from dcc.api.routes.workflows import router as workflows_router  # noqa: E402
from dcc.api.routes.sessions import router as sessions_router  # noqa: E402
from dcc.api.routes.workspaces import router as workspaces_router  # noqa: E402

app.include_router(health_router)
app.include_router(workspaces_router)
app.include_router(sessions_router)
app.include_router(config_router)
app.include_router(analytics_router)
app.include_router(github_router)
app.include_router(workflows_router)

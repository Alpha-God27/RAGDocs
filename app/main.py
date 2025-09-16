from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.routers import chat
from fastapi import Request
from fastapi.responses import HTMLResponse


def create_app() -> FastAPI:
    application = FastAPI(title="RAGDocs", version="0.1.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.mount(
        "/static", StaticFiles(directory="app/static"), name="static"
    )

    templates = Jinja2Templates(directory="app/templates")
    application.state.templates = templates

    application.include_router(chat.router)

    @application.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        templates_response = application.state.templates.TemplateResponse(
            "index.html",
            {"request": request},
        )
        return templates_response

    return application


app = create_app()

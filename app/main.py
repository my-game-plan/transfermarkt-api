from fastapi import FastAPI
from starlette.responses import RedirectResponse
from mangum import Mangum

from app.api.api import api_router

app = FastAPI(title="Transfermarkt API")
app.include_router(api_router)

@app.get("/", include_in_schema=False)
def docs_redirect():
    return RedirectResponse(url="/docs")

# Mangum handler
handler = Mangum(app)

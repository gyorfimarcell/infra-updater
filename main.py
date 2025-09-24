from fastapi import FastAPI
from update_infra import update_infra

app = FastAPI()


@app.get("/")
async def update():
    update_infra()

    return "Hello world"

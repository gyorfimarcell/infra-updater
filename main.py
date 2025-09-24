from fastapi import FastAPI, HTTPException
from update_infra import update_infra
from pydantic import BaseModel
from settings import settings

app = FastAPI()


# class UpdateBody(BaseModel):
#     secret: str


@app.post("/update")
async def update():  # body: UpdateBody):
    # if body.secret != settings.webhook_secret:
    #     raise HTTPException(status_code=403)

    update_infra()

    return "Done"

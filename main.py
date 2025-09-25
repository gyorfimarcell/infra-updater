import hashlib
import hmac

from fastapi import FastAPI, Header, HTTPException, Request, status

from settings import settings
from update_infra import update_infra

app = FastAPI()


@app.post("/update")
async def update(request: Request, x_gitea_signature: str = Header(None)):
    body = await request.body()

    if not x_gitea_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Gitea-Signature header",
        )

    computed_signature = hmac.new(
        key=settings.webhook_secret.encode(), msg=body, digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, x_gitea_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature"
        )

    update_infra()

    return "Done"

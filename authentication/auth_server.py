from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse

app = FastAPI()

VALID_TOKEN = "my-secret-token"

@app.post("/is_token_valid")
def validate_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return {"valid": False}

    token = authorization.split(" ")[1]
    return {"valid": token == VALID_TOKEN}


@app.get("/user_info")
def user_info(provider: str = Query(None), authorization: str = Header(None)):
    """
    SAM REST Gateway calls this after /is_token_valid.
    Provider can be 'azure', 'google', or None — ignore it.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse({"detail": "Invalid token"}, status_code=401)

    token = authorization.split(" ")[1]
    if token != VALID_TOKEN:
        return JSONResponse({"detail": "Invalid token"}, status_code=401)

    # Return user identity
    return {
        "user_identity": "sathwik",
        "roles": ["admin"],
        "email": "sathwik@example.com", 
        "provider": provider
    }

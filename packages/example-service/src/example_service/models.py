from pydantic import BaseModel


class GreetingResponse(BaseModel):
    message: str

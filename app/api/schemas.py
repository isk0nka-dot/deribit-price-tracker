from pydantic import BaseModel, ConfigDict


class PriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    price: float
    timestamp: int
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class LoginIn(BaseModel): username: str; password: str
class TokenOut(BaseModel): access_token: str; refresh_token: str; token_type: str="bearer"
class RefreshIn(BaseModel): refresh_token: str
class PreviewIn(BaseModel): url: str
class AlertIn(BaseModel): notify_on_drop: bool=True; notify_on_increase: bool=False; notify_on_target: bool=True; notify_on_new_low: bool=True; new_low_window: int=Field(30, ge=7, le=90); notify_on_back_in_stock: bool=True; min_drop_amount: int|None=None; min_drop_percent: int|None=None; min_increase_amount: int|None=None; min_increase_percent: int|None=None
class TrackIn(PreviewIn): selected_price_type: str; target_price: int|None=None; alerts: AlertIn=AlertIn()
class ProductOut(BaseModel): model_config=ConfigDict(from_attributes=True); id: int; marketplace: str; product_id: str; title: str; image_url: str|None; selected_price_type: str; current_price: int|None; target_price: int|None; status: str
class DeviceIn(BaseModel): token: str; name: str|None=None


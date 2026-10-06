import pytest
from types import SimpleNamespace
from app.alerts import evaluate
@pytest.mark.asyncio
async def test_target_rearms_only_after_above():
    class DB:
        async def scalars(self,*a,**k): return SimpleNamespace(all=lambda: [1000,900])
    p=SimpleNamespace(id=1,target_price=950)
    a=SimpleNamespace(notify_on_drop=False,notify_on_increase=False,notify_on_target=True,notify_on_new_low=False,notify_on_back_in_stock=False,new_low_window=30,min_drop_amount=None,min_drop_percent=None,min_increase_amount=None,min_increase_percent=None)
    assert "target" in await evaluate(DB(),p,1000,900,True,a)
    assert "target" not in await evaluate(DB(),p,900,800,True,a)


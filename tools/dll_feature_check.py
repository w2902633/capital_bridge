import sys
BASE = r"C:\Capital\SKDLLPythonTester"
if BASE not in sys.path:
    sys.path.insert(0, BASE)
from SKDLLPython import SK

names = [
    "SKCenterLib_GetSKAPIVersionAndBit",
    "RegisterEventOnNotifyStockList",
    "RegisterEventOnNotifyCommodityListWithTypeNo",
    "SKQuoteLib_RequestStocksWithMarketNo",
    "SKQuoteLib_EnterMonitorLONGByMarket",
    "SKQuoteLib_GetLiveKLineLONG",
    "SKQuoteLib_GetStockByIndexLONG",
]
for name in names:
    print(f"{name}={hasattr(SK._dll, name)}")

from typing import Optional
import requests

BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"
_cache: dict[str, float] = {}


def get_price(symbol: str) -> Optional[float]:
    try:
        r = requests.get(BINANCE_URL, params={"symbol": f"{symbol.upper()}USDT"}, timeout=5)
        if r.status_code == 200:
            price = float(r.json()["price"])
            _cache[symbol.upper()] = price
            return price
    except Exception:
        pass
    return _cache.get(symbol.upper())


def get_prices_bulk(symbols: list[str]) -> dict[str, float]:
    try:
        r = requests.get(BINANCE_URL, timeout=5)
        if r.status_code == 200:
            data = {item["symbol"]: float(item["price"]) for item in r.json()}
            result = {}
            for s in symbols:
                key = f"{s.upper()}USDT"
                if key in data:
                    _cache[s.upper()] = data[key]
                    result[s.upper()] = data[key]
            return result
    except Exception:
        pass
    return {s: _cache[s] for s in symbols if s in _cache}

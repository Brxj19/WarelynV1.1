SUPPORTED_CURRENCIES: dict[str, dict] = {
    "USD": {"name": "US Dollar", "symbol": "$", "decimal_places": 2},
    "EUR": {"name": "Euro", "symbol": "€", "decimal_places": 2},
    "GBP": {"name": "British Pound", "symbol": "£", "decimal_places": 2},
    "INR": {"name": "Indian Rupee", "symbol": "₹", "decimal_places": 2},
    "JPY": {"name": "Japanese Yen", "symbol": "¥", "decimal_places": 0},
    "CAD": {"name": "Canadian Dollar", "symbol": "CA$", "decimal_places": 2},
    "AUD": {"name": "Australian Dollar", "symbol": "A$", "decimal_places": 2},
    "CHF": {"name": "Swiss Franc", "symbol": "CHF", "decimal_places": 2},
    "CNY": {"name": "Chinese Yuan", "symbol": "¥", "decimal_places": 2},
    "AED": {"name": "UAE Dirham", "symbol": "د.إ", "decimal_places": 2},
    "SGD": {"name": "Singapore Dollar", "symbol": "S$", "decimal_places": 2},
    "BRL": {"name": "Brazilian Real", "symbol": "R$", "decimal_places": 2},
    "MXN": {"name": "Mexican Peso", "symbol": "MX$", "decimal_places": 2},
    "ZAR": {"name": "South African Rand", "symbol": "R", "decimal_places": 2},
    "NGN": {"name": "Nigerian Naira", "symbol": "₦", "decimal_places": 2},
    "KES": {"name": "Kenyan Shilling", "symbol": "KSh", "decimal_places": 2},
    "IDR": {"name": "Indonesian Rupiah", "symbol": "Rp", "decimal_places": 0},
    "MYR": {"name": "Malaysian Ringgit", "symbol": "RM", "decimal_places": 2},
    "PHP": {"name": "Philippine Peso", "symbol": "₱", "decimal_places": 2},
    "THB": {"name": "Thai Baht", "symbol": "฿", "decimal_places": 2},
    "SEK": {"name": "Swedish Krona", "symbol": "kr", "decimal_places": 2},
    "NOK": {"name": "Norwegian Krone", "symbol": "kr", "decimal_places": 2},
    "DKK": {"name": "Danish Krone", "symbol": "kr", "decimal_places": 2},
    "NZD": {"name": "New Zealand Dollar", "symbol": "NZ$", "decimal_places": 2},
    "HKD": {"name": "Hong Kong Dollar", "symbol": "HK$", "decimal_places": 2},
    "PKR": {"name": "Pakistani Rupee", "symbol": "₨", "decimal_places": 2},
    "EGP": {"name": "Egyptian Pound", "symbol": "E£", "decimal_places": 2},
    "TRY": {"name": "Turkish Lira", "symbol": "₺", "decimal_places": 2},
    "SAR": {"name": "Saudi Riyal", "symbol": "﷼", "decimal_places": 2},
    "QAR": {"name": "Qatari Riyal", "symbol": "﷼", "decimal_places": 2},
}


def validate_currency_code(code: str) -> bool:
    return code.upper() in SUPPORTED_CURRENCIES


def get_currency_info(code: str) -> dict | None:
    info = SUPPORTED_CURRENCIES.get(code.upper())
    if info is None:
        return None
    return {"code": code.upper(), **info}

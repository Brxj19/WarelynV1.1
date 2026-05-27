import re

COUNTRY_RULES: dict[str, int | tuple[int, int]] = {
    "+91": 10,
    "+1": 10,
    "+44": (7, 10),
    "+61": 9,
    "+971": 9,
}


def normalize_phone(value: str) -> str:
    """Strip spaces/dashes, ensure E.164 format."""
    if not value:
        return value
    cleaned = re.sub(r'[\s\-().]+', '', value)
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    return cleaned


def validate_phone(value: str) -> tuple[bool, str]:
    """Validate phone number. Returns (is_valid, error_message)."""
    if not value:
        return True, ""
    normalized = normalize_phone(value)
    if not re.match(r'^\+\d+$', normalized):
        return False, "Phone number must start with + followed by digits only."
    if len(normalized) < 8 or len(normalized) > 16:
        return False, "Phone number length is invalid."
    # Country-specific validation
    for prefix, length in COUNTRY_RULES.items():
        if normalized.startswith(prefix):
            local = normalized[len(prefix):]
            if isinstance(length, tuple):
                min_len, max_len = length
                if not (min_len <= len(local) <= max_len):
                    return False, f"Phone number for {prefix} must be {min_len}-{max_len} digits."
            else:
                if len(local) != length:
                    return False, f"Phone number for {prefix} must be {length} digits."
            break
    return True, ""

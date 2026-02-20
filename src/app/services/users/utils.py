import secrets


def generate_secure_otp(length: int = 6) -> str:
    """Generate a cryptographically secure, n-digit OTP."""
    # The range for a 6-digit OTP is [100000, 999999].
    # range_min = 10 ** (length - 1)
    # range_max = (10 ** length) - 1
    # We want a number between range_min and range_max inclusive.
    
    range_min = 10 ** (length - 1)
    range_max = (10 ** length) - 1
    
    # randbelow(n) returns a random int in the range [0, n).
    # We want range [range_min, range_max].
    # So we need range [0, range_max - range_min].
    # Then we add range_min.
    # range_size = range_max - range_min + 1 (because inclusive)
    
    range_size = range_max - range_min + 1
    random_number = secrets.randbelow(range_size)
    
    otp_int = random_number + range_min
    return str(otp_int)

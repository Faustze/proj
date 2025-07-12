import re
from typing import ClassVar


class EmailValidator:
    EMAIL_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    )

    @classmethod
    def is_valid(cls, email: str) -> bool:
        return bool(cls.EMAIL_REGEX.fullmatch(email.strip()))

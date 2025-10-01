from typing import Optional, Literal

from pydantic import BaseModel


class BooleanUnit(BaseModel):
    boolean: Optional[Literal['true', 'false', 'none']]

    def answer(self):
        if self.boolean in ["true", "yes", "y", "1"]:
            return True
        elif self.boolean in ["false", "no", "n", "0"]:
            return False
        else:
            return None

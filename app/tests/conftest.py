import os
from unittest.mock import patch

patch.dict(
    os.environ, {"DATABASE_URI": "sqlite+aiosqlite:///./test.db"}
).start()

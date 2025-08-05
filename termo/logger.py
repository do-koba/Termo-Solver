class _Colors:
    HEADER = '\033[95m'
    WHITE = '\033[97m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    GRAY = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger:
    def __init__(self, config: dict[str, bool]) -> None:
        """
        config: dict[str, bool]
        example: {
            "message": True,
            "success": True,
            "var": False,
            "background": False,
            "error": False,
            "warning": True,
        }
        """
        self._config: dict[str, bool] = config
        self._colors = _Colors()

    def success(self, *msg: object, end="\n") -> None:
        if self._config.get("success"):
            print(self._colors.GREEN, end="")
            print(*msg if len(msg) > 0 else "", end="",)
            print(self._colors.ENDC, end=end)

    def message(self, *msg: object, end="\n") -> None:
        if self._config.get("message"):
            print(self._colors.CYAN, end="")
            print(*msg if len(msg) > 0 else "", end="",)
            print(self._colors.ENDC, end=end)

    def var(self, *var: object, var_name: str = "", end="\n") -> None:
        if self._config.get("var"):
            print(self._colors.WHITE, end="")
            print(var_name, end="",)
            print(self._colors.GRAY, end="")
            print(*var if len(var) > 0 else "", end="",)
            print(self._colors.ENDC, end=end)

    def warning(self, *msg: object, end="\n") -> None:
        if self._config.get("warning"):
            print(self._colors.WARNING, end="")
            print(*msg if len(msg) > 0 else "", end="",)
            print(self._colors.ENDC, end=end)

    def background(self, *msg: object, end="\n") -> None:
        if self._config.get("background"):
            print(self._colors.GRAY, end="")
            print(*msg if len(msg) > 0 else "", end="",)
            print(self._colors.ENDC, end=end)

    def error(self, *msg: object, end="\n") -> None:
        if self._config.get("error"):
            print(self._colors.FAIL, end="")
            print(*msg if len(msg) > 0 else "", end="",)
            print(self._colors.ENDC, end=end)

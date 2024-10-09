import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Create a custom theme for our logs
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "critical": "bold white on red",
    }
)

# Create a Rich console with our custom theme
console = Console(theme=custom_theme)

# Configure the Rich logger
logging.basicConfig(
    level="INFO",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)

# Create a logger
logger = logging.getLogger("market_feed")


def get_logger():
    return logger

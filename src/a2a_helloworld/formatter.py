"""ANSI terminal formatter for chat-style A2A output."""

import sys

from a2a.types import Part, TextPart


class ChatFormatter:
    """Formats A2A chat messages with ANSI escape codes for terminal display."""

    BOLD = '\033[1m'
    DIM = '\033[2m'
    GREEN = '\033[32m'
    CYAN = '\033[36m'
    RED = '\033[31m'
    RESET = '\033[0m'
    CLEAR_LINE = '\033[K'

    def extract_text(self, parts: list[Part]) -> str:
        """Extract concatenated text content from a list of Part objects.

        Args:
            parts: List of A2A Part objects (may contain TextPart, FilePart, etc.).

        Returns:
            Concatenated text from all TextPart instances.
        """
        texts = []
        for part in parts:
            if isinstance(part.root, TextPart):
                texts.append(part.root.text)
        return ''.join(texts)

    def user_message(self, text: str) -> None:
        """Print a user message in cyan bold.

        Args:
            text: The user's message text.
        """
        sys.stdout.write(
            f'{self.BOLD}{self.CYAN}You:{self.RESET} {text}\n'
        )
        sys.stdout.flush()

    def agent_response(self, text: str) -> None:
        """Print an agent response in green bold.

        Args:
            text: The agent's response text.
        """
        sys.stdout.write(
            f'{self.BOLD}{self.GREEN}Agent:{self.RESET} {text}\n'
        )
        sys.stdout.flush()

    def streaming_typing(self) -> None:
        """Print an overwritable typing indicator (no newline)."""
        sys.stdout.write(
            f'\r{self.BOLD}{self.GREEN}Agent:{self.RESET} '
            f'{self.DIM}\u25cf typing...{self.RESET}{self.CLEAR_LINE}'
        )
        sys.stdout.flush()

    def streaming_response(self, text: str) -> None:
        """Overwrite the typing indicator with the actual response.

        Args:
            text: The agent's response text.
        """
        sys.stdout.write(
            f'\r{self.BOLD}{self.GREEN}Agent:{self.RESET} '
            f'{text}{self.CLEAR_LINE}\n'
        )
        sys.stdout.flush()

    def streaming_done(self, elapsed: float) -> None:
        """Print a completion indicator with elapsed time.

        Args:
            elapsed: Time in seconds the response took.
        """
        sys.stdout.write(
            f'       {self.DIM}\u2713 done ({elapsed:.1f}s){self.RESET}\n'
        )
        sys.stdout.flush()

    def error(self, text: str) -> None:
        """Print an error message in red.

        Args:
            text: The error message.
        """
        sys.stdout.write(f'{self.RED}{text}{self.RESET}\n')
        sys.stdout.flush()

    def banner(self, agent_name: str) -> None:
        """Print the welcome banner for the chat REPL.

        Args:
            agent_name: Name of the agent from the agent card.
        """
        sys.stdout.write(
            f'\n{self.BOLD}A2A Chat{self.RESET} \u2014 '
            f'connected to {self.GREEN}{agent_name}{self.RESET}\n'
            f'Type {self.DIM}/help{self.RESET} for commands, '
            f'{self.DIM}/quit{self.RESET} to exit.\n\n'
        )
        sys.stdout.flush()

    def help(self, commands: dict[str, str]) -> None:
        """Print the command help listing.

        Args:
            commands: Mapping of command names to descriptions.
        """
        sys.stdout.write(f'\n{self.BOLD}Commands:{self.RESET}\n')
        for name, desc in commands.items():
            sys.stdout.write(f'  {self.DIM}{name}{self.RESET}  {desc}\n')
        sys.stdout.write('\n')
        sys.stdout.flush()

    def goodbye(self) -> None:
        """Print a goodbye message."""
        sys.stdout.write('Goodbye!\n')
        sys.stdout.flush()

    def prompt(self) -> str:
        """Return the formatted input prompt string.

        Returns:
            ANSI-formatted prompt string for use with input().
        """
        return f'{self.BOLD}{self.CYAN}You:{self.RESET} '

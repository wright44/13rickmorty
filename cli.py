"""
Rick and Morty Character Catalog - Command Line Interface
Консольний інтерфейс для каталогу персонажів

Автор: [Ваше ім'я]
Група: [Ваша група]
"""

import os
import sys
import json
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Callable, Any
from enum import Enum
from datetime import datetime


# ==================== ENUMS ====================

class CharacterStatus(Enum):
    ALIVE = "Alive"
    DEAD = "Dead"
    UNKNOWN = "unknown"


class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    GENDERLESS = "Genderless"
    UNKNOWN = "unknown"


# ==================== DOMAIN MODELS ====================

@dataclass
class Character:
    """Модель персонажа."""
    id: int
    name: str
    status: str
    species: str
    gender: str
    origin: str
    location: str
    image_url: str
    episode_count: int = 0
    created_by_user: bool = False
    
    @property
    def status_emoji(self) -> str:
        return {"Alive": "🟢", "Dead": "🔴", "unknown": "⚪"}.get(self.status, "⚪")
    
    def __str__(self) -> str:
        return f"{self.status_emoji} [{self.id}] {self.name} - {self.species}"


# ==================== STORAGE (Заглушка для ПР 15) ====================

class CharacterStorage:
    """Сховище персонажів (локальне + API)."""
    
    API_URL = "https://rickandmortyapi.com/api/character"
    SAVE_FILE = "user_characters.json"
    
    def __init__(self):
        self._api_characters: List[Character] = []
        self._user_characters: List[Character] = []
        self._next_id = 10000  # ID для користувацьких персонажів
        self._load_user_characters()
    
    def fetch_from_api(self, page: int = 1) -> List[Character]:
        """Завантажує персонажів з API."""
        try:
            response = requests.get(f"{self.API_URL}?page={page}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            characters = []
            for item in data.get("results", []):
                char = Character(
                    id=item["id"],
                    name=item["name"],
                    status=item.get("status", "unknown"),
                    species=item.get("species", "Unknown"),
                    gender=item.get("gender", "unknown"),
                    origin=item.get("origin", {}).get("name", "Unknown"),
                    location=item.get("location", {}).get("name", "Unknown"),
                    image_url=item.get("image", ""),
                    episode_count=len(item.get("episode", []))
                )
                characters.append(char)
            
            self._api_characters = characters
            return characters
        except requests.RequestException as e:
            print(f"❌ Помилка завантаження: {e}")
            return []
    
    def get_all(self) -> List[Character]:
        """Повертає всіх персонажів."""
        return self._api_characters + self._user_characters
    
    def get_by_id(self, char_id: int) -> Optional[Character]:
        """Знаходить персонажа за ID."""
        for char in self.get_all():
            if char.id == char_id:
                return char
        return None
    
    def search(self, query: str) -> List[Character]:
        """Пошук за ім'ям."""
        query = query.lower()
        return [c for c in self.get_all() if query in c.name.lower()]
    
    def add_user_character(self, char: Character) -> None:
        """Додає користувацького персонажа."""
        char.id = self._next_id
        char.created_by_user = True
        self._next_id += 1
        self._user_characters.append(char)
        self._save_user_characters()
    
    def get_user_characters(self) -> List[Character]:
        """Повертає користувацьких персонажів."""
        return self._user_characters
    
    def _save_user_characters(self) -> None:
        """Зберігає користувацьких персонажів у файл."""
        data = [asdict(c) for c in self._user_characters]
        with open(self.SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_user_characters(self) -> None:
        """Завантажує користувацьких персонажів з файлу."""
        if os.path.exists(self.SAVE_FILE):
            try:
                with open(self.SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._user_characters = [Character(**item) for item in data]
                    if self._user_characters:
                        self._next_id = max(c.id for c in self._user_characters) + 1
            except (json.JSONDecodeError, KeyError):
                self._user_characters = []


# ==================== RENDERER (Стратегія відображення) ====================

class IRenderer(ABC):
    """Інтерфейс для відображення даних."""
    
    @abstractmethod
    def render(self, data: Any) -> str:
        pass


class CharacterRenderer(IRenderer):
    """Рендерер для персонажа."""
    
    def render(self, char: Character) -> str:
        lines = [
            "═" * 50,
            f"  {char.status_emoji} {char.name}",
            "═" * 50,
            f"  ID:       {char.id}",
            f"  Статус:   {char.status}",
            f"  Вид:      {char.species}",
            f"  Стать:    {char.gender}",
            f"  Походж.:  {char.origin}",
            f"  Локація:  {char.location}",
            f"  Епізоди:  {char.episode_count}",
            f"  Фото:     {char.image_url}",
        ]
        if char.created_by_user:
            lines.append("  [Створено користувачем]")
        lines.append("═" * 50)
        return "\n".join(lines)


class CharacterListRenderer(IRenderer):
    """Рендерер для списку персонажів."""
    
    def render(self, characters: List[Character]) -> str:
        if not characters:
            return "  Персонажів не знайдено."
        
        lines = ["", "┌" + "─" * 48 + "┐"]
        lines.append("│" + " СПИСОК ПЕРСОНАЖІВ".ljust(48) + "│")
        lines.append("├" + "─" * 48 + "┤")
        
        for char in characters:
            emoji = char.status_emoji
            user_mark = " *" if char.created_by_user else ""
            line = f"│ {emoji} [{char.id:>4}] {char.name[:30]:<30}{user_mark:>3} │"
            lines.append(line)
        
        lines.append("└" + "─" * 48 + "┘")
        lines.append(f"  Всього: {len(characters)} персонажів")
        lines.append("  (* - створено користувачем)")
        return "\n".join(lines)


class TableRenderer(IRenderer):
    """Рендерер для таблиць."""
    
    def render(self, data: Dict[str, Any]) -> str:
        lines = [""]
        max_key_len = max(len(str(k)) for k in data.keys()) if data else 10
        
        for key, value in data.items():
            lines.append(f"  {str(key):<{max_key_len}} : {value}")
        
        return "\n".join(lines)


# ==================== COMMANDS (Патерн Command) ====================

@dataclass
class CommandResult:
    """Результат виконання команди."""
    success: bool
    message: str = ""
    data: Any = None


class ICommand(ABC):
    """Інтерфейс команди."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def execute(self, args: List[str]) -> CommandResult:
        pass


# ==================== COMMAND STRATEGIES ====================

class ICommandStrategy(ABC):
    """Інтерфейс стратегії команд."""
    
    @abstractmethod
    def get_commands(self) -> List[ICommand]:
        pass


class InfoCommandStrategy(ICommandStrategy):
    """Стратегія інформаційних команд."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    def get_commands(self) -> List[ICommand]:
        return [
            ListCommand(self.storage, self.cli),
            ShowCommand(self.storage, self.cli),
            SearchCommand(self.storage, self.cli),
            StatsCommand(self.storage, self.cli),
        ]


class DataCommandStrategy(ICommandStrategy):
    """Стратегія команд роботи з даними."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    def get_commands(self) -> List[ICommand]:
        return [
            FetchCommand(self.storage, self.cli),
            CreateCommand(self.storage, self.cli),
            MyCharsCommand(self.storage, self.cli),
        ]


class SystemCommandStrategy(ICommandStrategy):
    """Стратегія системних команд."""
    
    def __init__(self, cli: 'CLI'):
        self.cli = cli
    
    def get_commands(self) -> List[ICommand]:
        return [
            HelpCommand(self.cli),
            ClearCommand(),
            ExitCommand(),
        ]


# ==================== CONCRETE COMMANDS ====================

class ListCommand(ICommand):
    """Показати список персонажів."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "list"
    
    @property
    def description(self) -> str:
        return "Показати список всіх персонажів"
    
    def execute(self, args: List[str]) -> CommandResult:
        characters = self.storage.get_all()
        if not characters:
            return CommandResult(False, "Список порожній. Використайте 'fetch' для завантаження.")
        
        output = self.cli.render(characters, CharacterListRenderer())
        return CommandResult(True, output)


class ShowCommand(ICommand):
    """Показати деталі персонажа."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "show"
    
    @property
    def description(self) -> str:
        return "Показати персонажа за ID. Приклад: show 1"
    
    def execute(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(False, "Вкажіть ID персонажа. Приклад: show 1")
        
        try:
            char_id = int(args[0])
        except ValueError:
            return CommandResult(False, "ID повинен бути числом.")
        
        char = self.storage.get_by_id(char_id)
        if not char:
            return CommandResult(False, f"Персонажа з ID {char_id} не знайдено.")
        
        output = self.cli.render(char, CharacterRenderer())
        return CommandResult(True, output)


class SearchCommand(ICommand):
    """Пошук персонажів."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def description(self) -> str:
        return "Пошук за ім'ям. Приклад: search Rick"
    
    def execute(self, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(False, "Вкажіть ім'я для пошуку.")
        
        query = " ".join(args)
        results = self.storage.search(query)
        
        if not results:
            return CommandResult(False, f"За запитом '{query}' нічого не знайдено.")
        
        output = self.cli.render(results, CharacterListRenderer())
        return CommandResult(True, f"Знайдено за запитом '{query}':\n{output}")


class StatsCommand(ICommand):
    """Статистика каталогу."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "stats"
    
    @property
    def description(self) -> str:
        return "Показати статистику каталогу"
    
    def execute(self, args: List[str]) -> CommandResult:
        chars = self.storage.get_all()
        
        if not chars:
            return CommandResult(False, "Каталог порожній.")
        
        alive = sum(1 for c in chars if c.status == "Alive")
        dead = sum(1 for c in chars if c.status == "Dead")
        unknown = len(chars) - alive - dead
        user_created = sum(1 for c in chars if c.created_by_user)
        
        stats = {
            "Всього персонажів": len(chars),
            "🟢 Живих": alive,
            "🔴 Мертвих": dead,
            "⚪ Невідомо": unknown,
            "👤 Створено вами": user_created,
        }
        
        output = self.cli.render(stats, TableRenderer())
        return CommandResult(True, f"\n📊 СТАТИСТИКА КАТАЛОГУ{output}")


class FetchCommand(ICommand):
    """Завантажити персонажів з API."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "fetch"
    
    @property
    def description(self) -> str:
        return "Завантажити персонажів з API. Приклад: fetch 1"
    
    def execute(self, args: List[str]) -> CommandResult:
        page = 1
        if args:
            try:
                page = int(args[0])
            except ValueError:
                pass
        
        self.cli.display("⏳ Завантаження даних...")
        characters = self.storage.fetch_from_api(page)
        
        if characters:
            return CommandResult(True, f"✅ Завантажено {len(characters)} персонажів (сторінка {page})")
        else:
            return CommandResult(False, "❌ Не вдалося завантажити дані.")


class CreateCommand(ICommand):
    """Створити нового персонажа."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "create"
    
    @property
    def description(self) -> str:
        return "Створити нового персонажа через діалог"
    
    def execute(self, args: List[str]) -> CommandResult:
        self.cli.display("\n🆕 СТВОРЕННЯ НОВОГО ПЕРСОНАЖА")
        self.cli.display("─" * 40)
        
        # Діалог створення
        name = self.cli.prompt("Ім'я персонажа")
        if not name:
            return CommandResult(False, "Ім'я не може бути порожнім.")
        
        self.cli.display("\nСтатус (1-Alive, 2-Dead, 3-unknown):")
        status_choice = self.cli.prompt("Виберіть [1-3]", "1")
        status_map = {"1": "Alive", "2": "Dead", "3": "unknown"}
        status = status_map.get(status_choice, "unknown")
        
        species = self.cli.prompt("Вид", "Human")
        
        self.cli.display("\nСтать (1-Male, 2-Female, 3-Genderless, 4-unknown):")
        gender_choice = self.cli.prompt("Виберіть [1-4]", "1")
        gender_map = {"1": "Male", "2": "Female", "3": "Genderless", "4": "unknown"}
        gender = gender_map.get(gender_choice, "unknown")
        
        origin = self.cli.prompt("Походження", "Unknown")
        location = self.cli.prompt("Локація", "Unknown")
        
        # Створення персонажа
        char = Character(
            id=0,  # Буде призначено автоматично
            name=name,
            status=status,
            species=species,
            gender=gender,
            origin=origin,
            location=location,
            image_url="",
            episode_count=0,
            created_by_user=True
        )
        
        self.storage.add_user_character(char)
        
        output = self.cli.render(char, CharacterRenderer())
        return CommandResult(True, f"\n✅ Персонаж створено!\n{output}")


class MyCharsCommand(ICommand):
    """Показати створених користувачем персонажів."""
    
    def __init__(self, storage: CharacterStorage, cli: 'CLI'):
        self.storage = storage
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "my"
    
    @property
    def description(self) -> str:
        return "Показати персонажів, створених вами"
    
    def execute(self, args: List[str]) -> CommandResult:
        chars = self.storage.get_user_characters()
        
        if not chars:
            return CommandResult(False, "Ви ще не створили жодного персонажа. Використайте 'create'.")
        
        output = self.cli.render(chars, CharacterListRenderer())
        return CommandResult(True, f"\n👤 ВАШІ ПЕРСОНАЖІ{output}")


class HelpCommand(ICommand):
    """Показати довідку."""
    
    def __init__(self, cli: 'CLI'):
        self.cli = cli
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "Показати список команд"
    
    def execute(self, args: List[str]) -> CommandResult:
        lines = [
            "",
            "╔" + "═" * 58 + "╗",
            "║" + " ДОСТУПНІ КОМАНДИ".ljust(58) + "║",
            "╠" + "═" * 58 + "╣",
        ]
        
        for cmd in self.cli.get_all_commands():
            cmd_str = f"  {cmd.name:<12} - {cmd.description}"
            if len(cmd_str) > 56:
                cmd_str = cmd_str[:53] + "..."
            lines.append("║ " + cmd_str.ljust(57) + "║")
        
        lines.append("╚" + "═" * 58 + "╝")
        
        return CommandResult(True, "\n".join(lines))


class ClearCommand(ICommand):
    """Очистити екран."""
    
    @property
    def name(self) -> str:
        return "clear"
    
    @property
    def description(self) -> str:
        return "Очистити екран"
    
    def execute(self, args: List[str]) -> CommandResult:
        os.system('cls' if os.name == 'nt' else 'clear')
        return CommandResult(True, "")


class ExitCommand(ICommand):
    """Вихід з програми."""
    
    @property
    def name(self) -> str:
        return "exit"
    
    @property
    def description(self) -> str:
        return "Вийти з програми"
    
    def execute(self, args: List[str]) -> CommandResult:
        print("\n👋 До побачення!\n")
        sys.exit(0)


# ==================== ARGS PARSER ====================

@dataclass
class ParsedArgs:
    """Розпарсені аргументи команди."""
    command: str
    args: List[str]
    options: Dict[str, str]


class ArgsParser:
    """Парсер аргументів командного рядка."""
    
    @staticmethod
    def parse(raw_input: str) -> ParsedArgs:
        parts = raw_input.strip().split()
        
        if not parts:
            return ParsedArgs("", [], {})
        
        command = parts[0].lower()
        args = []
        options = {}
        
        i = 1
        while i < len(parts):
            part = parts[i]
            if part.startswith("--"):
                key = part[2:]
                value = ""
                if i + 1 < len(parts) and not parts[i + 1].startswith("-"):
                    value = parts[i + 1]
                    i += 1
                options[key] = value
            elif part.startswith("-"):
                key = part[1:]
                options[key] = "true"
            else:
                args.append(part)
            i += 1
        
        return ParsedArgs(command, args, options)


# ==================== CLI FACADE ====================

class CLI:
    """
    Головний фасад командного інтерфейсу.
    
    Координує роботу всіх компонентів CLI:
    - Парсинг команд
    - Виконання команд через стратегії
    - Відображення результатів
    """
    
    BANNER = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   🛸  RICK AND MORTY CHARACTER CATALOG  🛸            ║
    ║                                                       ║
    ║   Консольний інтерфейс для каталогу персонажів       ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    
    def __init__(self):
        self._commands: Dict[str, ICommand] = {}
        self._parser = ArgsParser()
    
    def use_strategy(self, strategy: ICommandStrategy) -> None:
        """Реєструє команди зі стратегії."""
        for cmd in strategy.get_commands():
            self._commands[cmd.name] = cmd
    
    def get_all_commands(self) -> List[ICommand]:
        """Повертає всі зареєстровані команди."""
        return list(self._commands.values())
    
    def exec_command(self, raw_input: str) -> CommandResult:
        """Виконує команду з сирого вводу."""
        parsed = self._parser.parse(raw_input)
        
        if not parsed.command:
            return CommandResult(False, "Введіть команду. Використайте 'help' для довідки.")
        
        cmd = self._commands.get(parsed.command)
        if not cmd:
            suggestions = [c for c in self._commands.keys() if c.startswith(parsed.command[:2])]
            msg = f"Невідома команда: '{parsed.command}'."
            if suggestions:
                msg += f" Можливо ви мали на увазі: {', '.join(suggestions)}?"
            return CommandResult(False, msg)
        
        return cmd.execute(parsed.args)
    
    def render(self, data: Any, renderer: IRenderer) -> str:
        """Рендерить дані через вказаний рендерер."""
        return renderer.render(data)
    
    def display(self, message: str) -> None:
        """Виводить повідомлення."""
        print(message)
    
    def prompt(self, message: str, default: str = "") -> str:
        """Запитує введення користувача."""
        if default:
            result = input(f"  {message} [{default}]: ").strip()
            return result if result else default
        return input(f"  {message}: ").strip()
    
    def show_banner(self) -> None:
        """Показує банер."""
        print(self.BANNER)
    
    def run(self) -> None:
        """Головний цикл CLI."""
        self.show_banner()
        self.display("  Введіть 'help' для списку команд.\n")
        
        while True:
            try:
                raw = input("  > ").strip()
                if not raw:
                    continue
                
                result = self.exec_command(raw)
                if result.message:
                    self.display(result.message)
                print()
                
            except KeyboardInterrupt:
                self.display("\n\n  Використайте 'exit' для виходу.\n")
            except EOFError:
                break


# ==================== MAIN ====================

def main():
    """Точка входу."""
    # Ініціалізація компонентів
    storage = CharacterStorage()
    cli = CLI()
    
    # Реєстрація стратегій команд
    cli.use_strategy(InfoCommandStrategy(storage, cli))
    cli.use_strategy(DataCommandStrategy(storage, cli))
    cli.use_strategy(SystemCommandStrategy(cli))
    
    # Запуск CLI
    cli.run()


if __name__ == "__main__":
    main()

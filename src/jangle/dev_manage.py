import sys
from django.core.management import execute_from_command_line
from jangle.boot_django import boot_django


def main() -> None:
    boot_django()
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

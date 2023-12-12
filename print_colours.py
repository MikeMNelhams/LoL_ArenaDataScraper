class PrintColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def colour_print_string_header(phrase: str) -> str:
    return f"{PrintColors.HEADER}{phrase}{PrintColors.ENDC}"


def main():
    print("This is a library file, do not run as main.")


if __name__ == "__main__":
    main()

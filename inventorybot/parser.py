import re

from enum import Enum
from dataclasses import dataclass


# Enum with token types
class TokenType(Enum):
    OPERATION = "OPERATION"
    VALUE = "VALUE"


@dataclass
class Token:
    type: TokenType
    value: str


# <COMMAND> = <OPERATIAON>\s<VALUE>(\s<VALUE>)*
# <INSTRUCTIONS>=<COMMAND>(\s<COMMAND>)*

OPERATIONS = set(["l", "q", "s"])


def _clean_str(value):
    # Remove duplicated spaces
    return re.sub(r"\s+", " ", value).strip()


def tokenizer(instructions_input) -> list[Token]:
    tokens = []
    splited = _clean_str(instructions_input).split()

    for instruction in splited:
        if instruction.lower() in OPERATIONS:
            tokens.append(Token(TokenType.OPERATION, instruction))
        else:
            tokens.append(Token(TokenType.VALUE, instruction))

    return tokens


def parser(value: str) -> list[list[str]]:
    tokens = tokenizer(value)
    return _parser(tokens)


def _parser(tokens: list[Token]) -> list[list[str]]:
    instructions = []
    current_instruction = []

    for token in tokens:
        if token.type == TokenType.OPERATION:
            if current_instruction:
                instructions.append(current_instruction)
                current_instruction = []
            current_instruction.append(token.value)
        elif token.type == TokenType.VALUE:
            current_instruction.append(token.value)

    if current_instruction:
        instructions.append(current_instruction)

    return instructions

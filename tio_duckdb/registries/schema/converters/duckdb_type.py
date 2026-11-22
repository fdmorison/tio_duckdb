from __future__ import annotations

from tiozin.api.metadata.schema.exceptions import SchemaError

from . import constants as const

QUOTE = '"'


class DuckdbType:
    """
    A DuckDB type as SQL writes it, such as "BIGINT", "DECIMAL(10,2)",
    "VARCHAR[]", "INTEGER[3]", "MAP(VARCHAR, BIGINT)" or
    "STRUCT(id BIGINT, tags VARCHAR[])".

    Examples:

        ```python
        DuckdbType("DECIMAL(10,2)").type_name  # "DECIMAL"
        DuckdbType("VARCHAR[]").element_type.type_name  # "VARCHAR"
        DuckdbType('STRUCT("first name" VARCHAR)').fields
        # [("first name", DuckdbType("VARCHAR"))]
        ```
    """

    def __init__(self, type_name: str) -> None:
        self.text = type_name.strip()

    def __repr__(self) -> str:
        return f"DuckdbType({self.text!r})"

    @property
    def physical_type(self) -> str:
        """
        The type exactly as the DuckDB schema writes it.
        """
        return self.text

    @property
    def type_name(self) -> str:
        """
        The name of the type without parameters, in upper case and with
        aliases resolved. A type written as `T[]` is "LIST", and one written
        as `T[n]` is "ARRAY".

        Examples:

            ```python
            DuckdbType("decimal(10,2)").type_name  # "DECIMAL"
            DuckdbType("INT").type_name  # "INTEGER"
            DuckdbType("TIMESTAMPTZ").type_name  # "TIMESTAMP WITH TIME ZONE"
            DuckdbType("INTEGER[3]").type_name  # "ARRAY"
            ```
        """
        if self.text.endswith("]"):
            return const.DUCKDB_LIST_TYPE if self.array_size is None else const.DUCKDB_ARRAY_TYPE

        name = " ".join(self.text.split("(", 1)[0].split()).upper()
        return const.DUCKDB_TYPE_ALIASES.get(name, name)

    @property
    def element_type(self) -> DuckdbType:
        """
        The type of the elements of a list or an array.

        Examples:

            ```python
            DuckdbType("INTEGER[3][]").element_type  # DuckdbType("INTEGER[3]")
            ```
        """
        return DuckdbType(self.text[: self.text.rindex("[")])

    @property
    def array_size(self) -> int | None:
        """
        The number of elements of an array, or None for a list.

        Examples:

            ```python
            DuckdbType("INTEGER[3]").array_size  # 3
            DuckdbType("INTEGER[]").array_size  # None
            ```
        """
        size = self.text[self.text.rindex("[") + 1 : -1].strip()
        return int(size) if size else None

    @property
    def arguments(self) -> list[str]:
        """
        The arguments of the type, as written between its parentheses.

        Examples:

            ```python
            DuckdbType("MAP(VARCHAR, INTEGER[])").arguments  # ["VARCHAR", "INTEGER[]"]
            DuckdbType("BIGINT").arguments  # []
            ```
        """
        if "(" not in self.text:
            return []

        inner = self.text[self.text.index("(") + 1 : self.text.rindex(")")]
        return self.split_arguments(inner)

    @property
    def precision(self) -> int:
        """
        The number of digits of a decimal, 18 when not written, as in DuckDB.
        """
        arguments = self.arguments
        return int(arguments[0]) if arguments else const.DUCKDB_DEFAULT_DECIMAL_PRECISION

    @property
    def scale(self) -> int:
        """
        The number of digits after the point of a decimal: 3 when no argument
        is written, and 0 when only the precision is, as in DuckDB.
        """
        arguments = self.arguments

        match len(arguments):
            case 0:
                return const.DUCKDB_DEFAULT_DECIMAL_SCALE
            case 1:
                return 0
            case _:
                return int(arguments[1])

    @property
    def key_type(self) -> DuckdbType:
        """
        The type of the keys of a map.
        """
        return DuckdbType(self.arguments[0])

    @property
    def value_type(self) -> DuckdbType:
        """
        The type of the values of a map.
        """
        return DuckdbType(self.arguments[1])

    @property
    def fields(self) -> list[tuple[str, DuckdbType]]:
        """
        The name and the type of each field of a struct.

        Examples:

            ```python
            DuckdbType('STRUCT(id BIGINT, "first name" VARCHAR)').fields
            # [("id", DuckdbType("BIGINT")), ("first name", DuckdbType("VARCHAR"))]
            ```
        """
        return [self.split_field(argument) for argument in self.arguments]

    @staticmethod
    def split_arguments(text: str) -> list[str]:
        """
        Splits the arguments of a type at the commas outside parentheses and
        quotes.

        Examples:

            ```python
            DuckdbType.split_arguments("a DECIMAL(10,2), b VARCHAR")
            # ["a DECIMAL(10,2)", "b VARCHAR"]
            ```
        """
        arguments = []
        depth = 0
        quoted = False
        start = 0

        for index, char in enumerate(text):
            match char:
                case '"':
                    quoted = not quoted
                case "(" if not quoted:
                    depth += 1
                case ")" if not quoted:
                    depth -= 1
                case "," if not quoted and depth == 0:
                    arguments.append(text[start:index].strip())
                    start = index + 1

        arguments.append(text[start:].strip())
        return [argument for argument in arguments if argument]

    @staticmethod
    def split_field(argument: str) -> tuple[str, DuckdbType]:
        """
        Splits a struct field into its name, unquoted, and its type.

        Raises SchemaError when the field has no type.

        Examples:

            ```python
            DuckdbType.split_field('"first name" VARCHAR')  # ("first name", DuckdbType("VARCHAR"))
            ```
        """
        if argument.startswith(QUOTE):
            end = 1
            while end < len(argument):
                if argument[end] == QUOTE and argument[end + 1 : end + 2] != QUOTE:
                    break
                end += 2 if argument[end] == QUOTE else 1

            name = argument[1:end].replace(QUOTE * 2, QUOTE)
            type_name = argument[end + 1 :]
        else:
            name, _, type_name = argument.partition(" ")

        SchemaError.raise_if(
            not type_name.strip(),
            f"Struct field `{argument}` has no type",
        )

        return name, DuckdbType(type_name)

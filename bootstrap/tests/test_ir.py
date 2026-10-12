
"""Unit tests for the Kupln Intermediate Representation model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from bootstrap.ir.lowering import (
    IRLoweringError,
    lower_compilation_unit,
)
from bootstrap.ir.model import (
    IRBasicBlock,
    IRConstant,
    IRFunction,
    IRInstruction,
    IRModule,
    IROpcode,
    IRParameter,
    IRSourceLocation,
    IRValue,
)
from bootstrap.pipeline import parse_source


class IRModelTests(unittest.TestCase):
    def test_source_location_preserves_coordinates(self) -> None:
        location = IRSourceLocation(line=2, column=5, offset=10)

        self.assertEqual(location.line, 2)
        self.assertEqual(location.column, 5)
        self.assertEqual(location.offset, 10)

    def test_value_supports_optional_type(self) -> None:
        value = IRValue(name="v1", type_name="Int")
        untyped_value = IRValue(name="v2")

        self.assertEqual(value.name, "v1")
        self.assertEqual(value.type_name, "Int")
        self.assertIsNone(untyped_value.type_name)

    def test_constant_preserves_kind_and_value(self) -> None:
        constant = IRConstant(kind="int", value="42")

        self.assertEqual(constant.kind, "int")
        self.assertEqual(constant.value, "42")

    def test_instruction_stores_opcode_result_and_operands(self) -> None:
        result = IRValue(name="v1", type_name="Int")
        constant = IRConstant(kind="int", value="42")
        location = IRSourceLocation(line=1, column=1, offset=0)

        instruction = IRInstruction(
            opcode=IROpcode.CONSTANT,
            result=result,
            operands=(constant,),
            source_location=location,
        )

        self.assertEqual(instruction.opcode, IROpcode.CONSTANT)
        self.assertEqual(instruction.result, result)
        self.assertEqual(instruction.operands, (constant,))
        self.assertEqual(instruction.source_location, location)

    def test_function_and_module_preserve_ordered_structure(self) -> None:
        parameter = IRParameter(name="count", type_name="Int")
        instruction = IRInstruction(opcode=IROpcode.RETURN)
        block = IRBasicBlock(
            name="entry",
            instructions=(instruction,),
        )
        function = IRFunction(
            name="calculate",
            parameters=(parameter,),
            return_type="Int",
            blocks=(block,),
        )
        module = IRModule(functions=(function,))

        self.assertEqual(module.functions, (function,))
        self.assertEqual(function.parameters, (parameter,))
        self.assertEqual(function.blocks, (block,))
        self.assertEqual(block.instructions, (instruction,))

    def test_ir_model_objects_are_immutable(self) -> None:
        value = IRValue(name="v1")

        with self.assertRaises(FrozenInstanceError):
            value.name = "v2"  # type: ignore[misc]

    def test_lowering_function_with_binary_return(self) -> None:
        source = (
            "function add(left: Int, right: Int): Int { "
            "return left + right; "
            "}"
        )

        module = lower_compilation_unit(parse_source(source))

        self.assertEqual(len(module.functions), 1)

        function = module.functions[0]
        self.assertEqual(function.name, "add")
        self.assertEqual(
            tuple(parameter.name for parameter in function.parameters),
            ("left", "right"),
        )
        self.assertEqual(function.return_type, "Int")
        self.assertEqual(len(function.blocks), 1)

        opcodes = tuple(
            instruction.opcode
            for instruction in function.blocks[0].instructions
        )
        self.assertEqual(
            opcodes,
            (
                IROpcode.PARAMETER,
                IROpcode.PARAMETER,
                IROpcode.LOAD,
                IROpcode.LOAD,
                IROpcode.BINARY,
                IROpcode.RETURN,
            ),
        )

    def test_lowering_is_deterministic(self) -> None:
        source = (
            "function calculate(value: Int): Int { "
            "return value * 2; "
            "}"
        )

        first = lower_compilation_unit(parse_source(source))
        second = lower_compilation_unit(parse_source(source))

        self.assertEqual(first, second)

    def test_lowering_rejects_unsupported_top_level_construct(
        self,
    ) -> None:
        source = "class User {}"

        with self.assertRaisesRegex(
            IRLoweringError,
            "Unsupported top-level construct",
        ):
            lower_compilation_unit(parse_source(source))

    def test_lowering_rejects_unsupported_control_flow(
        self,
    ) -> None:
        source = (
            "function choose(flag: Bool): Int { "
            "if (flag) { return 1; } "
            "return 0; "
            "}"
        )

        with self.assertRaisesRegex(
            IRLoweringError,
            "Unsupported function-body construct: IfStatement",
        ):
            lower_compilation_unit(parse_source(source))


if __name__ == "__main__":
    unittest.main()

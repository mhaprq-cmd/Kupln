"""Unit tests for the Kupln Intermediate Representation model."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

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


if __name__ == "__main__":
    unittest.main()

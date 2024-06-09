from block import Block
from pycparser import c_ast
import utils
from utils import GlobalParameters


class NewFunctions:
    """
    A class that handles the operation related to changing the definition of the involved functions so that the
    external interfaces of the involved functions remain the same, and they call the block function with the correct
    inputs and return the correct output.
    """
    @staticmethod
    def change_function_definitions(involved_functions, block_call_union):
        """
        Changes the definitions of involved functions so that they call the block function with correct inputs and
        returns the result. This helps so that the code that calls these function will not be affected by the
        tail call elimination and the external interface of the functions remain the same.
        """
        block_call_union_instance = Block.generate_block_call_union_instance(block_call_union)
        for function in involved_functions:
            block_items = [block_call_union_instance]
            NewFunctions.generate_params_assignments_in_frame(block_items, involved_functions[function])
            block_items.append(Block.generate_block_call_stmt(involved_functions[function].index_label))
            block_items.append(NewFunctions.generate_return_stmt_in_new_functions(function))

            involved_functions[function].function_definition.body.block_items = block_items

    @staticmethod
    def generate_params_assignments_in_frame(block_items, function_info):
        """
        Generates the parameters assignments for the frame
        For example, in a function named foo, if the function has two inputs called x and y of type integer,
        this statement will be:
            frame.foo.x = x;
            frame.foo.y = y;
        """
        function_args = function_info.function_definition.decl.type.args
        if function_args is None:
            return

        function_name = function_info.function_definition.decl.name
        for param in function_args.params:
            param_name = c_ast.ID(param.name)
            frame_field = utils.generate_2d_struct_ref(GlobalParameters.block_call_union_instance_name,
                                                       function_name,
                                                       param.name)
            assignment = c_ast.Assignment('=', frame_field, param_name)
            block_items.append(assignment)

    @staticmethod
    def generate_return_stmt_in_new_functions(function_name):
        """
        Generates the return statements in the new functions.
        For example, in a function named foo, if the block call union is called frame
        and the return value is called result, this statement will be:
            return frame.foo.result
        """
        return_expr = utils.generate_2d_struct_ref(GlobalParameters.block_call_union_instance_name,
                                                   function_name,
                                                   GlobalParameters.function_return_val_name)

        return_stmt = c_ast.Return(return_expr)
        return return_stmt



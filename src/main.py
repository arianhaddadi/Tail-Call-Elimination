import utils
import os
from pycparser import parse_file
from block import Block
from new_functions import NewFunctions
import sys


def remove_tail_calls(filename):
    """
    Calls all the functions for the steps of the tail call elimination process.
    """
    temp_filename = f"{filename[:-2]}_temp.c"
    directives = utils.remove_and_save_directives(filename, temp_filename)

    ast = parse_file(temp_filename)
    func_def_map = utils.get_functions_def_map(ast)
    involved_functions = utils.identify_involved_functions(ast, func_def_map)
    block_call_union = Block.generate_block_call_union(involved_functions)
    block_function = Block.generate_block_function(
        involved_functions, func_def_map
    )
    NewFunctions.change_function_definitions(
        involved_functions, block_call_union
    )

    utils.write_result_to_disk(
        directives,
        involved_functions,
        block_call_union,
        block_function,
        ast,
        filename,
    )
    os.remove(temp_filename)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print(
            "Wrong number of arguments. The only accepted argument is the "
            "address of the input source file to be converted."
        )
    elif len(sys.argv) < 2:
        print("Input file not given.")
    else:
        filename = sys.argv[1]
        if os.path.exists(filename):
            remove_tail_calls(filename=filename)
        else:
            print("Input file does not exist.")

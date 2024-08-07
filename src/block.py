from utils import GlobalParameters
from pycparser import c_ast
from copy import deepcopy
import utils


class Block:
    """
    Used to handle operations related to the block function and its inputs and
    its calling inside the new definitions of the involved functions.

    Block function is the function that includes the logic of all functions
    that originally had tail calls with their tail calls having been removed.
    This is essentially the main function that this program generates
    to remove tail calls from the source code.
    """

    @staticmethod
    def generate_block_call_union(involved_functions):
        """
        This function generates the union that contains all the involved
        function's call structs. For example if the involved functions are foo
        and bar, and their call structs are named foo_ios and bar_ios
        respectively, this union would be
            union block_call {
              struct bar_ios bar;
              struct foo_ios foo;
            };
        """
        name = GlobalParameters.block_call_union_name
        decls = []
        for function in involved_functions:
            function_call_struct = involved_functions[function].call_struct
            struct_type = c_ast.Struct(function_call_struct.type.name, None)
            type_declaration = c_ast.TypeDecl(function, [], None, struct_type)
            decl = c_ast.Decl(
                function, [], [], [], [], type_declaration, None, None
            )
            decls.append(decl)
        union_type = c_ast.Union(name, decls)
        union = c_ast.Decl(None, [], [], [], [], union_type, None, None)
        return union

    @staticmethod
    def generate_block_function_index_arg():
        """
        In the block function declaration, the first parameters is the index of
        the function that initially called the block function. In order to make
        the code cleaner, the logic for generating this is separated into
        a distinct method. If the block function's declaration is this:
            void block(int index, union block_call *frame)

        This function generates the first parameter which is 'int index'
        """
        declaration_type = c_ast.TypeDecl(
            "index", [], [], c_ast.IdentifierType(["int"])
        )
        declaration = c_ast.Decl(
            "index", [], [], [], [], declaration_type, None, None
        )
        return declaration

    @staticmethod
    def generate_block_function_union_arg():
        """
        In the block function declaration, the second parameters is the union
        block_call. In order to make the code cleaner, the logic for generating
        this is separated into a distinct method. In reality if the block
        function's declaration is this:
            void block(int index, union block_call *frame)

        This function generates the second argument which is
        'union block_call *frame'
        """
        pointer_union_type = c_ast.Union(
            GlobalParameters.block_call_union_name, None
        )
        pointer_type = c_ast.TypeDecl(
            GlobalParameters.block_call_union_instance_name,
            [],
            None,
            pointer_union_type,
        )
        declaration_type = c_ast.PtrDecl([], pointer_type)
        declaration = c_ast.Decl(
            GlobalParameters.block_call_union_instance_name,
            [],
            [],
            [],
            [],
            declaration_type,
            None,
            None,
        )
        return declaration

    @staticmethod
    def generate_block_function_declaration():
        """
        Generates the declaration of the block function. For instance, it can
        be like this:
            void block(int index, union block_call *frame)
        """
        return_type = c_ast.TypeDecl(
            GlobalParameters.block_name,
            [],
            None,
            c_ast.IdentifierType(["void"]),
        )
        args = c_ast.ParamList(
            [
                Block.generate_block_function_index_arg(),
                Block.generate_block_function_union_arg(),
            ]
        )
        declaration_type = c_ast.FuncDecl(args, return_type)
        function_declaration = c_ast.Decl(
            GlobalParameters.block_name,
            [],
            [],
            [],
            [],
            declaration_type,
            None,
            None,
        )
        return function_declaration

    @staticmethod
    def generate_arguments_assignments(function_info):
        """
        Generates the argument assignment in the beginning of the case statement
        for each of the functions. For example, if the function has the
        declaration int foo(int x, int y), it generates these statements:
            int x = frame->foo.x;
            int y = frame->foo.y;
        So that the rest of the function's body can access these values the same
        as they could in the body of the original function which received these
        values as its parameters
        """
        assignments = []
        function_params = (
            function_info.function_definition.decl.type.args.params
        )
        function_name = function_info.function_definition.decl.name
        for param in function_params:
            param_clone = deepcopy(param)
            param_clone.init = utils.generate_2d_struct_ref(
                GlobalParameters.block_call_union_instance_name,
                function_name,
                param.name,
                inner_ptr=True,
            )
            assignments.append(param_clone)
        return assignments

    @staticmethod
    def convert_return_in_block(function_name, return_expr, func_def_map):
        """
        Converts the return statement of original function to the form it should
        have in block function.
        For example if the original function has:
            return foo(x);
        it converts this into:
            frame->foo.x = x;
            goto foo_Label;
        and if it's a function named foo and has:
            return 2;
        it converts this into:
            frame->foo.result = 2;
            return;
        """
        items = []
        if isinstance(return_expr.expr, c_ast.FuncCall):
            called_function_name = return_expr.expr.name.name
            function_params = func_def_map[
                called_function_name
            ].decl.type.args.params
            args = return_expr.expr.args.exprs
            for i, param in enumerate(function_params):
                param_assignment = c_ast.Assignment(
                    op="=",
                    rvalue=args[i],
                    lvalue=utils.generate_2d_struct_ref(
                        GlobalParameters.block_call_union_instance_name,
                        called_function_name,
                        param.name,
                        inner_ptr=True,
                    ),
                )
                items.append(param_assignment)
            items.append(c_ast.Goto(f"{called_function_name}_LABEL"))
        else:
            return_assignment = c_ast.Assignment(
                op="=",
                rvalue=return_expr.expr,
                lvalue=utils.generate_2d_struct_ref(
                    GlobalParameters.block_call_union_instance_name,
                    function_name,
                    GlobalParameters.function_return_val_name,
                    inner_ptr=True,
                ),
            )
            items.append(return_assignment)
            items.append(c_ast.Return(None))
        return items

    @staticmethod
    def traverse(items, function_name, func_def_map):
        """
        Recursively traverses the body of the function.
        This is necessary because the return statements of the functions need to
        change in order to be inside block function. So each statement that has
        a block scope (E.g., switch case, if, while, for, etc.) is recursively
        checked whether it contains a return statement so that it is changed
        properly.
        """
        new_items = []
        for item in items:
            if isinstance(item, c_ast.Return):
                new_items.extend(
                    Block.convert_return_in_block(
                        function_name, item, func_def_map
                    )
                )
            elif isinstance(item, c_ast.If):
                item_clone = deepcopy(item)
                if item.iftrue is not None:
                    item_clone.iftrue.block_items = Block.traverse(
                        item.iftrue.block_items, function_name, func_def_map
                    )
                if item.iffalse is not None:
                    if isinstance(item.iffalse, c_ast.If):
                        item_clone.iffalse = Block.traverse(
                            [item.iffalse], function_name, func_def_map
                        )[0]
                    else:
                        item_clone.iffalse.block_items = Block.traverse(
                            item.iffalse.block_items,
                            function_name,
                            func_def_map,
                        )
                new_items.append(item_clone)
            elif (
                isinstance(item, c_ast.While)
                or isinstance(item, c_ast.For)
                or isinstance(item, c_ast.Switch)
            ):
                item_clone = deepcopy(item)
                if item.stmt is not None:
                    item_clone.stmt.block_items = Block.traverse(
                        item.stmt.block_items, function_name, func_def_map
                    )
                new_items.append(item_clone)
            elif isinstance(item, c_ast.Case):
                item_clone = deepcopy(item)
                if item.stmts is not None:
                    item_clone.stmts.block_items = Block.traverse(
                        item.stmts.block_items, function_name, func_def_map
                    )
                new_items.append(item_clone)
            else:
                new_items.append(item)
        return new_items

    @staticmethod
    def generate_function_case_body_in_block(function_info, func_def_map):
        """
        Generates the case statement body for each involved function.
        generate_function_case_in_block wraps a case statement around the result
        of this function.
        """
        argument_assignments = Block.generate_arguments_assignments(
            function_info
        )
        function_name = function_info.function_definition.decl.name
        body_items = Block.traverse(
            function_info.function_definition.body.block_items,
            function_name,
            func_def_map,
        )
        return argument_assignments + body_items

    @staticmethod
    def generate_function_case_in_block(function_info, func_def_map):
        """Generates the case statement for each involved function."""
        case_body = Block.generate_function_case_body_in_block(
            function_info, func_def_map
        )
        case_stmt = c_ast.Case(
            c_ast.ID(function_info.index_label), [c_ast.Compound(case_body)]
        )
        label = c_ast.Label(function_info.block_label, case_stmt)
        return label

    @staticmethod
    def generate_block_function_definition(involved_functions, func_def_map):
        """Generates the block function's body."""
        functions_bodies = [
            Block.generate_function_case_in_block(
                involved_functions[function], func_def_map
            )
            for function in involved_functions
        ]
        switch_body = c_ast.Compound(functions_bodies)
        switch_stmt = c_ast.Switch(c_ast.ID("index"), switch_body)
        body_items = [switch_stmt]
        body = c_ast.Compound(body_items)
        return body

    @staticmethod
    def generate_block_function(involved_functions, func_def_map):
        """Generates the block function in its entirety"""
        function_declaration = Block.generate_block_function_declaration()
        function_body = Block.generate_block_function_definition(
            involved_functions, func_def_map
        )
        block_function = c_ast.FuncDef(
            function_declaration, None, function_body
        )
        return block_function

    @staticmethod
    def generate_block_call_union_instance(block_call_union):
        """
        Generates an instance of the union that is passed to the block function
        """
        name = GlobalParameters.block_call_union_instance_name
        type = deepcopy(block_call_union.type)
        type.decls = None
        type_declaration = c_ast.TypeDecl(name, [], None, type)
        instance = c_ast.Decl(
            name, [], [], [], [], type_declaration, None, None
        )
        return instance

    @staticmethod
    def generate_block_call_stmt(index_label):
        """
        Generates the statement that calls the block function.
        For example, if the function is called foo, this statement would be
            block(foo_INDEX, &frame);
        """
        block_call_struct_name = c_ast.ID(
            GlobalParameters.block_call_union_instance_name
        )
        expressions = [
            c_ast.ID(index_label),
            c_ast.UnaryOp("&", block_call_struct_name),
        ]
        args = c_ast.ExprList(expressions)
        block_call_stmt = c_ast.FuncCall(
            c_ast.ID(GlobalParameters.block_name), args
        )
        return block_call_stmt

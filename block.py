from utils import GlobalParameters
from pycparser import c_ast
from copy import deepcopy
import utils


class Block:
    @staticmethod
    def generate_block_call_union(involved_functions):
        name = GlobalParameters.block_call_union_name
        decls = []
        for function in involved_functions:
            function_call_struct = involved_functions[function].call_struct
            struct_type = c_ast.Struct(function_call_struct.type.name, None)
            type_declaration = c_ast.TypeDecl(function, [], None, struct_type)
            decl = c_ast.Decl(function, [], [], [], [], type_declaration, None, None)
            decls.append(decl)
        union_type = c_ast.Union(name, decls)
        union = c_ast.Decl(None, [], [], [], [], union_type, None, None)
        return union

    @staticmethod
    def generate_block_function_index_arg():
        declaration_type = c_ast.TypeDecl("index", [], [], c_ast.IdentifierType(['int']))
        declaration = c_ast.Decl('index', [], [], [], [], declaration_type, None, None)
        return declaration

    @staticmethod
    def generate_block_function_union_arg():
        pointer_union_type = c_ast.Union(GlobalParameters.block_call_union_name, None)
        pointer_type = c_ast.TypeDecl(GlobalParameters.block_call_union_instance_name, [], None, pointer_union_type)
        declaration_type = c_ast.PtrDecl([], pointer_type)
        declaration = c_ast.Decl(GlobalParameters.block_call_union_instance_name, [], [], [], [], declaration_type,
                                 None, None)
        return declaration

    @staticmethod
    def generate_block_function_declaration():
        return_type = c_ast.TypeDecl(GlobalParameters.block_name, [], None, c_ast.IdentifierType(["void"]))
        args = c_ast.ParamList([Block.generate_block_function_index_arg(), Block.generate_block_function_union_arg()])
        declaration_type = c_ast.FuncDecl(args, return_type)
        function_declaration = c_ast.Decl(GlobalParameters.block_name, [], [], [], [], declaration_type, None, None)
        return function_declaration

    @staticmethod
    def generate_arguments_assignments(function_info):
        assignments = []
        function_params = function_info.function_definition.decl.type.args.params
        function_name = function_info.function_definition.decl.name
        for param in function_params:
            param_clone = deepcopy(param)
            param_clone.init = utils.generate_2d_struct_ref(GlobalParameters.block_call_union_instance_name,
                                                            function_name,
                                                            param.name,
                                                            inner_ptr=True)
            assignments.append(param_clone)
        return assignments

    @staticmethod
    def convert_return_inside_block(function_name, return_expr, func_def_map):
        items = []
        if isinstance(return_expr.expr, c_ast.FuncCall):
            called_function_name = return_expr.expr.name.name
            function_params = func_def_map[called_function_name].decl.type.args.params
            args = return_expr.expr.args.exprs
            for i, param in enumerate(function_params):
                param_assignment = c_ast.Assignment(op='=',
                                                    rvalue=args[i],
                                                    lvalue=utils.generate_2d_struct_ref(GlobalParameters.block_call_union_instance_name,
                                                                                        called_function_name,
                                                                                        param.name,
                                                                                        inner_ptr=True))
                items.append(param_assignment)
            items.append(c_ast.Goto(f'{called_function_name}_LABEL'))
        else:
            return_assignment = c_ast.Assignment(op="=",
                                                 rvalue=return_expr.expr,
                                                 lvalue=utils.generate_2d_struct_ref(GlobalParameters.block_call_union_instance_name,
                                                                                     function_name,
                                                                                     GlobalParameters.function_return_val_name,
                                                                                     inner_ptr=True))
            items.append(return_assignment)
            items.append(c_ast.Return(None))
        return items

    @staticmethod
    def traverse(items, function_name, func_def_map):
        new_items = []
        for item in items:
            if isinstance(item, c_ast.Return):
                new_items.extend(Block.convert_return_inside_block(function_name, item, func_def_map))
            elif isinstance(item, c_ast.If):
                item_clone = deepcopy(item)
                if item.iftrue is not None:
                    item_clone.iftrue.block_items = Block.traverse(item.iftrue.block_items, function_name, func_def_map)
                if item.iffalse is not None:
                    item_clone.iffalse.block_items = Block.traverse(item.iffalse.block_items, function_name, func_def_map)
                new_items.append(item_clone)
            elif isinstance(item, c_ast.While) or isinstance(item, c_ast.For) or isinstance(item, c_ast.Switch):
                item_clone = deepcopy(item)
                if item.stmt is not None:
                    item_clone.stmt.block_items = Block.traverse(item.stmt.block_items, function_name, func_def_map)
                new_items.append(item_clone)
            elif isinstance(item, c_ast.Case):
                item_clone = deepcopy(item)
                if item.stmts is not None:
                    item_clone.stmts.block_items = Block.traverse(item.stmts.block_items, function_name, func_def_map)
                new_items.append(item_clone)
            else:
                new_items.append(item)
        return new_items

    @staticmethod
    def generate_case_body_inside_block(function_info, func_def_map):
        argument_assignments = Block.generate_arguments_assignments(function_info)
        function_name = function_info.function_definition.decl.name
        body_items = Block.traverse(function_info.function_definition.body.block_items, function_name, func_def_map)
        return argument_assignments + body_items

    @staticmethod
    def generate_function_body_in_block(function_info, func_def_map):
        case_body = Block.generate_case_body_inside_block(function_info, func_def_map)
        case_stmt = c_ast.Case(c_ast.ID(function_info.index_label), [c_ast.Compound(case_body)])
        label = c_ast.Label(function_info.block_label, case_stmt)
        return label

    @staticmethod
    def generate_block_function_body(involved_functions, func_def_map):
        functions_bodies = [Block.generate_function_body_in_block(involved_functions[function], func_def_map)
                            for function in involved_functions]
        switch_body = c_ast.Compound(functions_bodies)
        switch_stmt = c_ast.Switch(c_ast.ID('index'), switch_body)
        body_items = [switch_stmt]
        body = c_ast.Compound(body_items)
        return body

    @staticmethod
    def generate_block_function(involved_functions, func_def_map):
        function_declaration = Block.generate_block_function_declaration()
        function_body = Block.generate_block_function_body(involved_functions, func_def_map)
        block_function = c_ast.FuncDef(function_declaration, None, function_body)
        return block_function

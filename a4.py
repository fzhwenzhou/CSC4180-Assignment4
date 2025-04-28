# Copyright (c) 2024 Liu Yuxuan
# Email: yuxuanliu1@link.cuhk.edu.cn
#
# This code is licensed under MIT license (see LICENSE file for details)
#
# This code is for teaching purpose of course: CUHKSZ's CSC4180: Compiler Construction
# as Assignment 4: Oat v.1 Compiler Frontend to LLVM IR using llvmlite
#
# Copyright (c)
# Oat v.1 Language was designed by Prof.Steve Zdancewic when he was teaching CIS 341 at U Penn.
# 

import sys                          # for CLI argument parsing
import llvmlite.binding as llvm     # for llvmlite IR generation
import llvmlite.ir as ir            # for llvmlite IR generation
import pydot                        # for .dot file parsing
from enum import Enum               # for enum in python
from random import random


DEBUG = False

class SymbolTable:
    """
    Symbol table is a stack of maps, and each map represents a scope

    The key of map is the lexeme (string, not unique) of an identifier, and the value is its type (DataType)

    The size of self.scopes and self.scope_ids should always be the same
    """
    def __init__(self):
        """
        Initialize the symbol table with no scope inside
        """
        self.id_counter = 0      # Maintain an increment counter for each newly pushed scope
        self.scopes = []         # map<str, DataType> from lexeme to data type in one scope
        self.scope_ids = []      # stores the ID for each scope

    def push_scope(self):
        """
        Push a new scope to symbol table

        Returns:
            - (int) the ID of the newly pushed scope
        """
        self.id_counter += 1
        self.scopes.append({})   # push a new table (mimics the behavior of stack)
        self.scope_ids.append(self.id_counter)
        return self.id_counter

    def pop_scope(self):
        """
        Pop a scope out of symbol table, usually called when the semantic analysis for one scope is finished
        """
        self.scopes.pop()    # pop out the last table (mimics the behavior of stack)
        self.scope_ids.pop()

    def unique_name(self, lexeme, scope_id):
        """
        Compute the unique name for an identifier in one certain scope

        Args:
            - lexeme(str)
            - scope_id(int)
        
        Returns:
            - str: the unique name of identifier used for IR codegen
        """
        return lexeme + "-" + str(scope_id)

    def insert(self, lexeme, type):
        """
        Insert a new symbol to the top scope of symbol table

        Args:
            - lexeme(str): lexeme of the symbol
            - type(DataType): type of the symbol
        
        Returns:
            - (str): the unique ID of the symbol
        """
        # check the size of scopes and scope_id
        if len(self.scopes) != len(self.scope_ids):
            raise ValueError("Mismatch size of symbol_table and id_table")
        scope_idx = len(self.scopes) - 1
        self.scopes[scope_idx][lexeme] = type
        return self.unique_name(lexeme, self.scope_ids[scope_idx])

    def lookup_local(self, lexeme):
        """
        Lookup a symbol in the top scope of symbol table only
        called when we want to declare a new local variable

        Args:
            - lexeme(str): lexeme of the symbol

        Returns:
            - (str, DataType): 2D tuple of unique_id and data type if the symbol is found
            - None if the symbol is not found
        """
        if len(self.scopes) != len(self.scope_ids):
            raise ValueError("Mismatch size of symbol_table and id_table")
        table_idx = len(self.scopes) - 1
        if lexeme in self.scopes[table_idx]:
            unique_name = self.unique_name(lexeme, self.scope_ids[table_idx])
            type = self.scopes[table_idx][lexeme]
            return unique_name, type
        else:
            return None

    def lookup_global(self, lexeme):
        """
        Lookup a symbol in all the scopes of symbol table (stack)
        called when we want to search a lexeme or declare a global variable

        Args:
            - lexeme(str): lexeme of the symbol

        Returns:
            - (str, DataType): 2D tuple of unique_id and data type if the symbol is found
            - None if the symbol is not found
        """
        if len(self.scopes) != len(self.scope_ids):
            raise ValueError("Mismatch size of symbol_table and id_table")
        for table_idx in range(len(self.scopes) - 1, -1, -1):
            if lexeme in self.scopes[table_idx]:
                unique_name = self.unique_name(lexeme, self.scope_ids[table_idx])
                type = self.scopes[table_idx][lexeme]
                return unique_name, type
        return None

# Global Symbol Table for Semantic Analysis
symbol_table = SymbolTable()

# Global Context of LLVM IR Code Generation
module = ir.Module()                    # Global LLVM IR Module
builder = ir.IRBuilder()                # Global LLVM IR Builder
ir_map = {}                             # Global Map from unique names to its LLVM IR item

class TreeNode:
    def __init__(self, index, lexeme):
        self.index = index              # [int] ID of the TreeNode, used for visualization 
        self.lexeme = lexeme            # [str] lexeme of the node (may have naming conflicts, and needs unique name in IR codegen)
        self.id = ""                    # [str] unique name of the node (used in IR codegen), filled in semantic analysis
        self.nodetype = NodeType.NONE   # [NodeType] type of node, used to determine which actions to do with the current node in semantic analysis or IR codegen
        self.datatype = DataType.NONE   # [DataType] data type of node, filled in semantic analysis and used in IR codegen
        self.children = []              # Array of childern TreeNodes

    def add_child(self, child_node):
        self.children.append(child_node)

def print_tree(node, level = 0):
    print("  " * level + '|' + node.lexeme.replace("\n","\\n") + ", " + node.nodetype.name)
    for child in node.children:
        print_tree(child, level + 1)

def visualize_tree(root_node, output_path):
    """
    Visulize TreeNode in Graphviz

    Args:
        - root_node(TreeNode)
        - output_path(str): the output path for png file 
    """
    # construct pydot Node from TreeNode with label
    def pydot_node(tree_node):
        node = pydot.Node(tree_node.index)
        label = tree_node.nodetype.name
        if len(tree_node.id) > 0:
            label += "\n" + tree_node.id.replace("\\n","\/n")
        elif len(tree_node.lexeme) > 0:
            label += "\n" + tree_node.lexeme.replace("\\n","\/n")
        label += "\ntype: " + tree_node.datatype.name
        node.set("label", label)
        return node
    # Recursively visualize node
    def visualize(node, graph):
        # Add Root Node Only
        if node.index == 0:
            graph.add_node(pydot_node(node))
        # Add Children Nodes and Edges
        for child in node.children:
            graph.add_node(pydot_node(child))
            graph.add_edge(pydot.Edge(node.index, child.index))
            visualize(child, graph)
    # Output visualization png graph
    graph = pydot.Dot(graph_type="graph")
    visualize(root_node, graph)
    graph.write_png(output_path)

def construct_tree_from_dot(dot_filepath):
    """
    Read .dot file, which records the AST from parser

    Args:
        - dot_filepath(str): path of the .dot file

    Return:
        - TreeNode: the root node of the AST
    """
    # Extract the first graph from the list (assuming there is only one graph in the file)
    graph = pydot.graph_from_dot_file(dot_filepath)[0]
    # Initialize Python TreeNode structure
    nodes = []
    # code_type_map = { member.value: member for member in NodeType }
    # Add nodes
    for node in graph.get_nodes():
        if len(node.get_attributes()) == 0: continue
        index = int(node.get_name()[4:])
        # print(node.get_attributes(), node.get_attributes()['label'], node.get_attributes()['lexeme'])
        label = node.get_attributes()["label"][1:-1]    # exlcude enclosing quotes
        lexeme = node.get_attributes()['lexeme'][1:-1]  # exclude enclosing quotes
        tree_node = TreeNode(index, lexeme)
        tree_node.lexeme = lexeme
        tree_node.nodetype = { member.value: member for member in NodeType }[label] if any(label == member.value for member in NodeType) else NodeType.NONE
        if DEBUG: print("Index: ", index, ", lexeme: ", lexeme, ", nodetype: ", tree_node.nodetype)
        nodes.append(tree_node)
    # Add Edges
    for edge in graph.get_edges():
        src_id = int(edge.get_source()[4:])
        dst_id = int(edge.get_destination()[4:])
        nodes[src_id].add_child(nodes[dst_id])
    # root node should always be the first node
    return nodes[0]

class NodeType(Enum):
    """
    Map lexeme of AST node to code type in IR generation

    The string value here is to convert the token class by bison to Python NodeType
    """
    PROGRAM = "<program>"
    GLOBAL_DECL = "<global_decl>"     # global variable declaration
    FUNC_DECL = "<function_decl>"       # function declaration
    VAR_DECLS = "<var_decls>"
    VAR_DECL = "<var_decl>"        # variable declaration
    ARGS = "<args>"
    ARG = "<arg>"
    REF = "<ref>"
    GLOBAL_EXPS = "<global_exps>"
    STMTS = "<stmts>"
    EXPS = "<exps>"
    FUNC_CALL = "<func call>"       # function call
    ARRAY_INDEX = "<array index>"    # array element retrieval by index
    IF_STMT = "IF"         # if-else statement (nested case included)
    ELSE_STMT = "ELSE"
    FOR_LOOP = "FOR"        # for loop statement (nested case included)
    WHILE_LOOP = "WHILE"      # while loop statement (nested case included)
    RETURN = "RETURN"          # return statement
    NEW = "NEW"         # new variable with/without initialization
    ASSIGN = "ASSIGN"         # assignment (lhs = rhs)
    EXP = "<exp>"     # expression (including a lot of binary operators)
    TVOID = "void"
    TINT = "int"
    TSTRING = "string"
    TBOOL = "bool"
    NULL = "NULL"
    TRUE = "TRUE"
    FALSE = "FALSE"
    STAR = "STAR"
    PLUS = "PLUS"
    MINUS = "MINUS"
    LSHIFT = "LSHIFT"
    RLSHIFT = "RLSHIFT"
    RASHIFT = "RASHIFT"
    LESS = "LESS"
    LESSEQ = "LESSEQ"
    GREAT = "GREAT"
    GREATEQ = "GREATEQ"
    EQ = "EQ"
    NEQ = "NEQ"
    LAND = "LAND"
    LOR = "LOR"
    BAND = "BAND"
    BOR = "BOR"
    NOT = "NOT"
    TILDE = "TILDE"
    INTLITERAL = "INTLITERAL"
    STRINGLITERAL = "STRINGLITERAL"
    ID = "ID"
    NONE = "unknown"         # unsupported

class DataType(Enum):
    INT = 1             # INT refers to Int32 type (32-bit Integer)
    BOOL = 2            # BOOL refers to Int1 type (1-bit Integer, 1 for True and 0 for False)
    STRING = 3          # STRING refers to an array of Int8 (8-bit integer for a single character)
    INT_ARRAY = 4       # Array of integers, no need to support unless for bonus
    BOOL_ARRAY = 5      # Array of booleans, no need to support unless for bonus
    STRING_ARRAY = 6    # Array of strings, no need to support unless for bonus
    VOID = 7            # Void, you can choose whether to support it or not
    NONE = 8            # Unknown type, used as initialized value for each TreeNode

def ir_type(data_type, array_size = 1):
    map = {
        DataType.INT: ir.IntType(32),       # integer is in 32-bit
        DataType.BOOL: ir.IntType(32),      # bool is also in 32-bit, 0 for false and 1 for True
        DataType.STRING: ir.ArrayType(ir.IntType(8), array_size + 1),   # extra \0 (null terminator)
        DataType.INT_ARRAY: ir.ArrayType(ir.IntType(32), array_size),
        DataType.BOOL_ARRAY: ir.ArrayType(ir.IntType(32), array_size),
        DataType.STRING_ARRAY: ir.ArrayType(ir.ArrayType(ir.IntType(8), 32), array_size),   # string max size = 32 for string array 
    }
    type = map.get(data_type)
    if type:
        return type
    else:
        raise ValueError("Unsupported data type: ", data_type)

def declare_runtime_functions():
    """
    Declare built-in functions for Oat v.1 Language
    """
    # int32_t* array_of_string (char *str)
    func_type = ir.FunctionType(
        ir.PointerType(ir.IntType(32)),     # return type
        [ir.PointerType(ir.IntType(8))])    # args type
    # map function unique name in global scope to the function body
    # the global scope should have scope_id = 1 
    func = ir.Function(module, func_type, name="array_of_string")
    ir_map[SymbolTable.unique_name(None, "array_of_string", 1)] = func
    # char* string_of_array (int32_t *arr)
    func_type = ir.FunctionType(
        ir.PointerType(ir.IntType(8)),      # return type
        [ir.PointerType(ir.IntType(32))])   # args type
    func = ir.Function(module, func_type, name="string_of_array")
    ir_map[SymbolTable.unique_name(None, "string_of_array", 1)] = func
    # int32_t length_of_string (char *str)
    func_type = ir.FunctionType(
        ir.IntType(32),                      # return type
        [ir.PointerType(ir.IntType(8))])    # args type
    func = ir.Function(module, func_type, name="length_of_string")
    ir_map[SymbolTable.unique_name(None, "length_of_string", 1)] = func
    # char* string_of_int(int32_t i)
    func_type = ir.FunctionType(
        ir.PointerType(ir.IntType(8)),      # return type
        [ir.IntType(32)])                   # args type
    func = ir.Function(module, func_type, name="string_of_int")
    ir_map[SymbolTable.unique_name(None, "string_of_int", 1)] = func
    # char* string_cat(char* l, char* r)
    func_type = ir.FunctionType(
        ir.PointerType(ir.IntType(8)),      # return tyoe
        [ir.PointerType(ir.IntType(8)), ir.PointerType(ir.IntType(8))]) # args type
    func = ir.Function(module, func_type, name="string_cat")
    ir_map[SymbolTable.unique_name(None, "string_cat", 1)] = func
    # void print_string (char* str)
    func_type = ir.FunctionType(
        ir.VoidType(),                      # return type
        [ir.PointerType(ir.IntType(8))])    # args type
    func = ir.Function(module, func_type, name="print_string")
    ir_map[SymbolTable.unique_name(None, "print_string", 1)] = func
    # void print_int (int32_t i)
    func_type = ir.FunctionType(
        ir.VoidType(),                      # return type
        [ir.IntType(32)])                   # args type
    func = ir.Function(module, func_type, name="print_int")
    ir_map[SymbolTable.unique_name(None, "print_int", 1)] = func
    # void print_bool (int32_t i)
    func_type = ir.FunctionType(
        ir.VoidType(),                      # return type
        [ir.IntType(32)])                   # args type
    func = ir.Function(module, func_type, name="print_bool")
    ir_map[SymbolTable.unique_name(None, "print_bool", 1)] = func

def codegen(node):
    """
    Recursively do LLVM IR generation

    Call corresponding handler function for each NodeType

    Different NodeTypes may be mapped to the same handelr function

    Args:
        node(TreeNode)
    """
    module.triple = 'riscv64'
    codegen_func_map = {
        NodeType.GLOBAL_DECL: codegen_handler_global_decl,
        # TODO: add more mappings from NodeType to its handler function of IR generation
        NodeType.FUNC_DECL: codegen_handler_func_decl,
        NodeType.VAR_DECL: codegen_handler_var_decl,
        NodeType.RETURN: codegen_handler_return,
        NodeType.FUNC_CALL: codegen_handler_func_call,
        NodeType.ASSIGN: codegen_handler_assign,
        NodeType.PLUS: codegen_handler_plus,
        NodeType.IF_STMT: codegen_handler_if,
        NodeType.FOR_LOOP: codegen_handler_for,
        NodeType.WHILE_LOOP: codegen_handler_while,
        NodeType.STAR: codegen_handler_star
    }
    codegen_func = codegen_func_map.get(node.nodetype)
    if codegen_func:
        codegen_func(node)
    else:
        codegen_handler_default(node)

# Some sample handler functions for IR codegen
# TODO: implement more handler functions for various node types
def codegen_handler_default(node):
    for child in node.children:
        codegen(child)

def codegen_handler_global_decl(node):
    """
    Global variable declaration
    """
    var_name = node.children[0].id
    variable = ir.GlobalVariable(module, typ=ir_type(node.children[1].datatype), name=var_name)
    variable.linkage = "private"
    variable.global_constant = True
    variable.initializer = ir.Constant(ir_type(node.children[1].datatype), int(node.children[1].lexeme))
    ir_map[var_name] = variable

def codegen_handler_func_decl(node):
    global builder
    func_name = node.children[1].id
    if func_name == 'main-1':
        func_name = 'main'
    params = []
    for t in node.children[2].children:
        params.append(ir_type(t.children[0].datatype))
    fnty = ir.FunctionType(ir_type(node.children[0].datatype), params)
    func = ir.Function(module, fnty, name=func_name)
    ir_map[func_name] = func
    block = func.append_basic_block(name='entry')
    builder = ir.IRBuilder(block)
    for param_node, arg in zip(node.children[2].children, func.args):
        param_name = param_node.children[1].id
        ptr = builder.alloca(arg.type)
        builder.store(arg, ptr)
        ir_map[param_name] = ptr
    codegen_handler_default(node)
    if not builder.block.is_terminated:
        if func.type.pointee.return_type == ir.VoidType():
            builder.ret_void()
        else:
            builder.ret(ir.Constant(func.type.pointee.return_type, 0))
    
def codegen_handler_var_decl(node):
    global builder
    var_name = node.children[0].id
    type = node.children[0].datatype
    if type == DataType.STRING:
        var_type = ir_type(DataType.STRING, len(node.children[1].lexeme))
    else:
        var_type = ir_type(type)
    variable = builder.alloca(var_type, name=var_name)
    builder.store(codegen_eval_expr(node.children[1]), variable)
    ir_map[var_name] = variable

def codegen_handler_return(node):
    global builder
    builder.ret(codegen_eval_expr(node.children[0]))
    
def codegen_handler_func_call(node):
    global builder
    fn = ir_map[node.children[0].id]
    args = []
    for i in node.children[1].children:
        args.append(codegen_eval_expr(i))
        if isinstance(args[-1].type, ir.ArrayType):
            variable = ir.GlobalVariable(module, typ=args[-1].type, name=f'tmp{random()}')
            variable.linkage = 'private'
            variable.global_constant = True
            variable.initializer = args[-1]
            zero = ir.Constant(ir.IntType(32), 0)
            args[-1] = builder.gep(variable, [zero, zero])
    return builder.call(fn, args)
        
    
def codegen_handler_assign(node):
    global builder
    lhs = ir_map[node.children[0].id]
    rhs = codegen_eval_expr(node.children[1])
    builder.store(rhs, lhs)

def codegen_handler_plus(node):
    global builder
    lhs, rhs = map(codegen_eval_expr, node.children)
    return builder.add(lhs, rhs)

def codegen_handler_minus(node):
    global builder
    lhs, rhs = map(codegen_eval_expr, node.children)
    return builder.sub(lhs, rhs)

def codegen_handler_star(node):
    global builder
    lhs, rhs = map(codegen_eval_expr, node.children)
    return builder.mul(lhs, rhs)

def codegen_handler_if(node):
    global builder
    
    then_block = builder.append_basic_block(f'then{random()}')
    else_block = builder.append_basic_block(f'else{random()}')
    endif_block = builder.append_basic_block(f'endif{random()}')
    
    cond_val = codegen_eval_expr(node.children[0])
    
    if cond_val.type == ir.IntType(32):
        zero = ir.Constant(ir.IntType(32), 0)
        cond = builder.icmp_signed('!=', cond_val, zero)
    else:
        cond = cond_val
    
    builder.cbranch(cond, then_block, else_block)
    
    builder.position_at_end(then_block)
    codegen(node.children[1]) 
    if not builder.block.is_terminated:
        builder.branch(endif_block)

    builder.position_at_end(else_block)
    codegen(node.children[2]) 
    if not builder.block.is_terminated:
        builder.branch(endif_block) 
    
    builder.position_at_end(endif_block)

def codegen_handler_while(node):
    global builder
    cond_block = builder.append_basic_block(f'cond{random()}')
    while_block = builder.append_basic_block(f'while{random()}')
    wend_block = builder.append_basic_block(f'wend{random()}')
    builder.branch(cond_block)
    
    builder.position_at_end(cond_block)
    
    cond_val = codegen_eval_expr(node.children[0])
    
    if cond_val.type == ir.IntType(32):
        zero = ir.Constant(ir.IntType(32), 0)
        cond = builder.icmp_signed('!=', cond_val, zero)
    else:
        cond = cond_val
        
    builder.cbranch(cond, while_block, wend_block)
    
    builder.position_at_end(while_block)
    codegen(node.children[1])
    if not builder.block.is_terminated:
        builder.branch(cond_block)
    
    builder.position_at_end(wend_block)
    
    

def codegen_handler_for(node):
    global builder
    cond_block = builder.append_basic_block(f'cond{random()}')
    for_block = builder.append_basic_block(f'for{random()}')
    next_block = builder.append_basic_block(f'next{random()}')
    
    codegen(node.children[0])
    
    builder.branch(cond_block)
    builder.position_at_end(cond_block)
    
    cond_val = codegen_eval_expr(node.children[1])
    
    if cond_val.type == ir.IntType(32):
        zero = ir.Constant(ir.IntType(32), 0)
        cond = builder.icmp_signed('!=', cond_val, zero)
    else:
        cond = cond_val
        
    builder.cbranch(cond, for_block, next_block)
    
    builder.position_at_end(for_block)
    codegen(node.children[3])
    codegen(node.children[2])
    if not builder.block.is_terminated:
        builder.branch(cond_block)
    
    builder.position_at_end(next_block)
    

def codegen_handler_great(node):
    global builder
    lhs, rhs = map(codegen_eval_expr, node.children)
    return builder.icmp_signed('>', lhs, rhs)

def codegen_handler_less(node):
    global builder
    lhs, rhs = map(codegen_eval_expr, node.children)
    return builder.icmp_signed('<', lhs, rhs)

def codegen_handler_true(node):
    return ir.Constant(ir.IntType(32), 1)

def codegen_handler_false(node):
    return ir.Constant(ir.IntType(32), 0)

def codegen_handler_intliteral(node):
    return ir.Constant(ir.IntType(32), int(node.lexeme))

def codegen_handler_stringliteral(node):
    s = bytearray((eval(f'"{node.lexeme}"') + '\0').encode('utf-8'))
    return ir.Constant(ir.ArrayType(ir.IntType(8), len(s)), s)

def codegen_handler_id(node):
    global builder
    var_ptr = ir_map[node.id]
    if node.datatype == DataType.STRING:
        zero = ir.Constant(ir.IntType(32), 0)
        return builder.gep(var_ptr, [zero, zero])
    else:
        return builder.load(var_ptr)

def codegen_eval_expr(node):
    if node.nodetype == NodeType.ID:
        return codegen_handler_id(node)
    elif node.nodetype == NodeType.INTLITERAL:
        return codegen_handler_intliteral(node)
    elif node.nodetype == NodeType.STRINGLITERAL:
        return codegen_handler_stringliteral(node)
    elif node.nodetype == NodeType.PLUS:
        return codegen_handler_plus(node)
    elif node.nodetype == NodeType.MINUS:
        return codegen_handler_minus(node)
    elif node.nodetype == NodeType.TRUE:
        return codegen_handler_true(node)
    elif node.nodetype == NodeType.FALSE:
        return codegen_handler_false(node)
    elif node.nodetype == NodeType.GREAT:
        return codegen_handler_great(node)
    elif node.nodetype == NodeType.LESS:
        return codegen_handler_less(node)
    elif node.nodetype == NodeType.FUNC_CALL:
        return codegen_handler_func_call(node)
    elif node.nodetype == NodeType.STAR:
        return codegen_handler_star(node)
    else:
        return codegen_eval_expr(node.children[0])


def semantic_analysis(node):
    """
    Perform semantic analysis on the root_node of AST

    Args:
        node(TreeNode)

    Returns:
        (DataType): datatype of the node
    """
    handler_map = {
        NodeType.PROGRAM: semantic_handler_program,
        NodeType.ID: semantic_handler_id,
        NodeType.TINT: semantic_handler_int,
        NodeType.TBOOL: semantic_handler_bool,
        NodeType.TSTRING: semantic_handler_string,
        NodeType.INTLITERAL: semantic_handler_int,
        NodeType.STRINGLITERAL: semantic_handler_string,
        NodeType.TRUE: semantic_handler_bool,
        NodeType.FALSE: semantic_handler_bool,
        # TODO: add more mapping from NodeType to its corresponding handler functions here
        NodeType.GLOBAL_DECL: semantic_handler_global_decl,
        NodeType.FUNC_DECL: semantic_handler_func_decl,
        NodeType.VAR_DECL: semantic_handler_var_decl,
        NodeType.STMTS: semantic_handler_stmts,
        NodeType.ARG: semantic_handler_arg_decl
    }
    int_arith = (
        NodeType.PLUS,
        NodeType.MINUS,
        NodeType.STAR,
        NodeType.LSHIFT,
        NodeType.RLSHIFT,
        NodeType.RASHIFT,
        NodeType.BAND,
        NodeType.BOR,
        NodeType.TILDE
    )
    bool_arith = (
        NodeType.EQ,
        NodeType.NEQ,
        NodeType.GREAT,
        NodeType.GREATEQ,
        NodeType.LESS,
        NodeType.LESSEQ,
        NodeType.LAND,
        NodeType.LOR,
        NodeType.NOT
    )
    for t in int_arith:
        handler_map[t] = semantic_handler_int_arith
    for t in bool_arith:
        handler_map[t] = semantic_handler_bool_arith
    handler = handler_map.get(node.nodetype)
    if handler:
        handler(node)
    else:
        default_handler(node)
    return node.datatype

def semantic_handler_program(node):
    symbol_table.push_scope()
    # insert built-in function names in global scope symbol table
    symbol_table.insert("array_of_string", DataType.INT_ARRAY)
    symbol_table.insert("string_of_array", DataType.STRING)
    symbol_table.insert("length_of_string", DataType.INT)
    symbol_table.insert("string_of_int", DataType.STRING)
    symbol_table.insert("string_cat", DataType.STRING)
    symbol_table.insert("print_string", DataType.VOID)
    symbol_table.insert("print_int", DataType.VOID)
    symbol_table.insert("print_bool", DataType.BOOL)
    # recursively do semantic analysis in left-to-right order for all children nodes
    for child in node.children:
        semantic_analysis(child)
    symbol_table.pop_scope()

# Some Sample handler functions
# TODO: define more handler functions for various node types
def semantic_handler_id(node):
    if symbol_table.lookup_global(node.lexeme) is None:
        raise ValueError("Variable not defined: ", node.lexeme)
    else:
        node.id, node.datatype = symbol_table.lookup_global(node.lexeme)

def semantic_handler_int(node):
    node.datatype = DataType.INT

def semantic_handler_bool(node):
    node.datatype = DataType.BOOL

def semantic_handler_string(node):
    node.datatype = DataType.STRING

def semantic_handler_global_decl(node):
    if len(node.children) != 2:
        raise ValueError('Wrong format for Global Declarations')
    semantic_handler_var_decl(node)

def semantic_handler_func_decl(node):
    if len(node.children) != 4:
        raise ValueError('Wrong format for Function Declarations')
    type, id, args, stmts = node.children
    semantic_analysis(type)
    id.datatype = stmts.datatype = type.datatype
    id.id = symbol_table.insert(id.lexeme, id.datatype)
    stmts.children = args.children + stmts.children
    semantic_analysis(stmts)
    stmts.children = stmts.children[len(args.children):]

def semantic_handler_var_decl(node):
    if len(node.children) != 2:
        raise ValueError('Wrong format for Variable Declarations')
    id, expr = node.children
    semantic_analysis(expr)
    id.datatype = expr.datatype
    id.id = symbol_table.insert(id.lexeme, id.datatype)

def semantic_handler_arg_decl(node):
    if len(node.children) != 2:
        raise ValueError('Wrong format for Argument Declarations')
    typ, id = node.children
    semantic_analysis(typ)
    id.datatype = typ.datatype
    id.id = symbol_table.insert(id.lexeme, id.datatype)

def semantic_handler_stmts(node):
    symbol_table.push_scope()
    default_handler(node)
    symbol_table.pop_scope()  

def semantic_handler_int_arith(node):
    node.datatype = DataType.INT
    default_handler(node)

def semantic_handler_bool_arith(node):
    node.datatype = DataType.BOOL
    default_handler(node)

def default_handler(node):
    for child in node.children:
        semantic_analysis(child)

if len(sys.argv) == 3:
    # visualize AST before semantic analysis
    dot_path = sys.argv[1]
    ast_png_before_semantic_analysis = sys.argv[2]
    root_node = construct_tree_from_dot(dot_path)
    if DEBUG: print_tree(root_node)
    visualize_tree(root_node, ast_png_before_semantic_analysis)
elif len(sys.argv) == 4:
    # visualize AST after semantic analysis
    dot_path = sys.argv[1]
    ast_png_after_semantics_analysis = sys.argv[2]
    llvm_ir = sys.argv[3]
    root_node = construct_tree_from_dot(dot_path)
    semantic_analysis(root_node)
    visualize_tree(root_node, ast_png_after_semantics_analysis)
    ## Uncomment the following when you are trying the do IR generation
    # # init llvm
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    declare_runtime_functions()
    codegen(root_node)
    # # print LLVM IR
    # print(module)
    with open(llvm_ir, 'w') as f:
        f.write(str(module))
else:
    raise SyntaxError("Usage: python3 a4.py <.dot> <.png before>\nUsage: python3 ./a4.py <.dot> <.png after> <.ll>")

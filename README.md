# CSC4180 Assignment 4: Compiler Frontend for Oat v.1
## Name: Fang Zihao, Student ID: 122090106

# Implement A Simple Semantic Analyzer for Oat v.1

## Usage
To run the program, simply follow the requirements below:
```
Usage: python3 a4.py <.dot> <.png before>
Usage: python3 ./a4.py <.dot> <.png after> <.ll>
```
For the first one, it will only convert the dot file to its PNG representation. For the second one, it will perform semantic analysis on the input abstract syntax tree, and use code generation to generate LLVM IR code. 

## Basic Requirements
Here, I strictly follow the template to implement the semantic analyzer and IR generator. Apart from the functions defined in the template, I have defined the following functions:
- `semantic_handler_global_decl`: Call the `semantic_handler_var_decl` function, as they share the same implementation. The only difference is that global declarations put variables in the global scope, while the local declarations put variables in some levels of the local scope. 
- `semantic_handler_var_decl`: It will firstly perform robustness test towards the node. That is, it has to have two children, the first one being the data type, and the second one being the expression. Therefore, it will firstly call semantic analysis recursively to the second child, obtaining its data type. Then, it will set the first child's data type to its second's. Finally, it will insert the lexeme into the symbol table, and store its unique ID computed by the function to "id" property. 
- `semantic_handler_func_decl`: It will firstly perform robustness test towards the node. That is, it has to have four children: The first being type, the second being ID, the third being arguments, and the last being statements. Firstly, recursively process the last three with semantic analysis, and then set the ID's type to the type. Then, it will insert the ID's lexeme to the symbol table and store the unique ID into the "id" field of ID. 
- `semantic_handler_stmts`: Before executing, it will push one scope in the symbol table. Then, it will call default handler to itself. Finally, it will pop the scope out. 

By utilizing all the existing functions and recursion techniques, it highly simplifies the implementation, and make the code much more reusable.

As for the code generator, the following functions are implemented. NOTE THAT THESE FUNCTIONS ARE IMPLEMENTED ONLY INTENDED TO PASS THE TESTCASES BETWEEN test0 AND test2. SOME ARITHMETIC OPERATIONS ARE OMITTED AS THEY ARE JUST DUPLICATIONS OF CURRENT CODES WITH MINOR MODIFICATIONS. THEREFORE, THESE ARE NOT INCLUDED.
- `codegen_handler_global_decl`: This function declares a global constant variable in the IR. It extracts the variable name, type, and initial value from the AST node, creates an ir.GlobalVariable, configures its linkage, and initializes it with a constant value stored in the second child. The variable is stored in ir_map for later access.
- `codegen_handler_func_decl`: This function generates IR for function declarations. It constructs the function signature (name, return type, parameters), creates an ir.Function, and initializes its entry block. Then, the function is stored in ir_map for later access. The IR builder is reset to this block, and code generation proceeds recursively for the function body.
- `codegen_handler_var_decl`: This function handles local variable declarations. It allocates stack space for the variable via builder.alloca, computes its type by getting the type of its first child (with special handling for string length), stores the evaluated initial value into the allocated space, and registers the variable in ir_map.
- `codegen_handler_ret`: This function emits a ret instruction for return statements. The return value is obtained by evaluating the child expression node and passed to builder.ret.
- `codegen_handler_func_call`: Generates IR for function calls. It resolves the function from ir_map, evaluates arguments , and emits a call instruction with the processed arguments. For arrays, it will perform special operations: firstly store the array constant into a global variable, and then get its pointer.
- `codegen_handler_assign`: Implements variable assignment. It retrieves the variable’s IR reference from ir_map, evaluates the right-hand side expression, and emits a store instruction to update the variable’s value.
- `codegen_handler_intliteral`: This function creates an IR constant for integer literals. Converts the AST node's lexeme to a 32-bit integer type (i32), returning an ir.Constant of that value. Directly maps source-level integers to their LLVM IR equivalents.
- `codegen_handler_stringliteral`: This function generates a null-terminated byte array constant for string literals. Encodes the string with UTF-8, appends a \0 terminator, then creates an IR array of 8-bit integers (i8) representing the bytes. The constant’s type is [N x i8] where N includes the terminator, emulating C-style strings in IR.
- `codegen_handler_plus/minus`: Handles addition/subtraction operations. Both evaluate the left/right operands recursively and emit an add or sub instruction using the IR builder.
Apart from these, a helper function, `codegen_eval_expr` is defined to take any expression, judge its type, and call the specific function above to handle different situations. 
These functions would correctly deal with functions without branches.

## Advanced Requirements
The semantic analyzer implemented in "Basic Requirements" can fully fit the requirements, so there is no modification made to the semantic analyzer. However, some additional functions should be added to the code generator. `codegen_handler_true` and `codegen_handler_false` return corresponding values for boolean values. `codegen_handler_great` and `codegen_handler_less` use the builder.icmp_signed to compare the left/right operands with specific operators and returns a boolean value. The following are the functions to handle control flows:
- `codegen_handler_if`: This function generates IR for an if statement. It creates three basic blocks: then (if-body), else (else-body), and endif (merge point after the if-else). The condition expression is first evaluated, and if it’s an integer, it’s compared to zero via icmp_signed to produce a Boolean number. A conditional branch (cbranch) directs control flow to the then or else block based on the condition. After generating code for both branches, each path unconditionally jumps to the shared endif block to unify control flow. The IR builder’s position is reset to endif.
- `codegen_handler_while`: This handles while loops by structuring IR into three blocks: cond (condition check), while (loop body), and wend (loop exit). Execution starts by jumping to cond, where the loop condition is evaluated. If true, control enters while to execute the body, then jumps back to cond to re-evaluate the condition, creating the loop. If false, it branches to wend to exit. This forms a cyclic flow: cond -> while -> cond until the condition fails, at which point execution proceeds to wend. The design ensures the condition is checked before every iteration, including the first.
- `codegen_handler_for`: This implements for loops, assuming a structure like for(init; cond; step) { body }. Four blocks are used: cond (condition check), for (loop body), and next (post-loop). First, the initialization code, that is, the first child runs. Control flows to cond, where the loop condition is tested. If true, the for block executes the loop body (node.children[3]) followed by the after expression (node.children[2]), then loops back to cond. If false, it exits to next. The node's third child runs after the body in each iteration.
These handle all the control flows.

# Get Familiar with LLVM’s Optimization Passes Through llvm-tutor
## llvm-tutor's Written Passes

llvm-tutor is a collection of self-contained reference LLVM passes. It is out-of-tree, that is, it builds against a binary LLVM installation, so there isno need to build LLVM from sources. The CMake file would build the optimization passes as dynamic-linked libraries. To use these passes, just load the libraries in the "opt" command and choose the specific optimization pass. 

All the optimization passes can be separated into three categories: Analysis, Transformation, and CFG (Control-Flow Graph). The first one: analysis, will only analysis the LLVM IR code without perform any modification. The second one: transformation, will perform transformation with or without analysis. The last one will perform analysis and/or transformation to the intermediate representations, but only at the block level. 

Here, I pick "RIV" pass as an example. RIV is an analysis pass that for each basic block BB in the input function computes the set reachable integer values, i.e. the integer values that are visible (i.e. can be used) in BB. Since the pass operates on the LLVM IR representation of the input file, it takes into account all values that have integer type in the LLVM IR sense. Here, I used the input_for_riv.ll generated by input_for_riv.c as the input (Compiled by clang with O1 optimization):
```llvm
; ModuleID = 'inputs/input_for_riv.c'
source_filename = "inputs/input_for_riv.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

; Function Attrs: norecurse nounwind readnone uwtable
define dso_local i32 @foo(i32 %0, i32 %1, i32 %2) local_unnamed_addr #0 {
  %4 = add nsw i32 %0, 123
  %5 = icmp sgt i32 %0, 0
  br i1 %5, label %6, label %17

6:                                                ; preds = %3
  %7 = mul nsw i32 %1, %0
  %8 = sdiv i32 %1, %2
  %9 = icmp eq i32 %7, %8
  br i1 %9, label %10, label %14

10:                                               ; preds = %6
  %11 = mul i32 %7, -2
  %12 = mul i32 %11, %8
  %13 = add i32 %4, %12
  br label %17

14:                                               ; preds = %6
  %15 = mul nsw i32 %2, 987
  %16 = mul nsw i32 %15, %8
  br label %17

17:                                               ; preds = %3, %10, %14
  %18 = phi i32 [ %13, %10 ], [ %16, %14 ], [ 321, %3 ]
  ret i32 %18
}

attributes #0 = { norecurse nounwind readnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 10.0.0-4ubuntu1~18.04.2 "}
```
The optimization phase command is:
```
opt -load libRIV.so -legacy-riv -analyze input_for_riv.ll
```
The output is:
```
Printing analysis 'Compute Reachable Integer values' for function 'foo':
=================================================
LLVM-TUTOR: RIV analysis results
=================================================
BB id      Reachable Ineger Values       
-------------------------------------------------
BB %3                                         
             i32 %0                        
             i32 %1                        
             i32 %2                        
BB %6                                         
               %4 = add nsw i32 %0, 123    
               %5 = icmp sgt i32 %0, 0     
             i32 %0                        
             i32 %1                        
             i32 %2                        
BB %17                                        
               %4 = add nsw i32 %0, 123    
               %5 = icmp sgt i32 %0, 0     
             i32 %0                        
             i32 %1                        
             i32 %2                        
BB %10                                        
               %7 = mul nsw i32 %1, %0     
               %8 = sdiv i32 %1, %2        
               %9 = icmp eq i32 %7, %8     
               %4 = add nsw i32 %0, 123    
               %5 = icmp sgt i32 %0, 0     
             i32 %0                        
             i32 %1                        
             i32 %2                        
BB %14                                        
               %7 = mul nsw i32 %1, %0     
               %8 = sdiv i32 %1, %2        
               %9 = icmp eq i32 %7, %8     
               %4 = add nsw i32 %0, 123    
               %5 = icmp sgt i32 %0, 0     
             i32 %0                        
             i32 %1                        
             i32 %2 
```
Here, it uses a special algorithm to identify all integer values in a basic block by considering all values in its dominating blocks. A dominating block is a block that can enter or branch to this basic block, and the values inside could affect the values in this basic block. The algorithm is as follows:
1. Compute Defined Values: For each block, collect values defined within it.
2. Initialize Entry Block: The entry block's RIV starts with function arguments and global integers.
3. Propagate via Dominance: For each block, propagate its RIV and defined values to blocks it dominates.
Here are the result analysis of the output:
BB %3 (Entry):
    Arguments %0, %1, %2 are reachable.
BB %6:
    Inherits %0, %1, %2 from entry.
    Adds values defined in %3 (%4, %5).
BB %10:
    Inherits RIV from %6 (arguments, %4, %5).
    Adds %6's definitions: %7, %8, %9.
BB %14: Similar to %10; inherits from %6.
BB %17:
    Dominated by %3 (not %6), so inherits entry's RIV (%0, %1, %2, %4, %5).
All values are reachable in all basic blocks, so the output contains all arguments in all basic blocks. 

## LLVM's Built-in Passes
Some built-in optimization passes perform code optimizations to maximize performance. Here, I take DLE (Dead Code Elimination) as an example. Dead Code Elimination is a technique that removes unreachable and unused code to improve the performance of execution and eliminate the code size, as the executions of these instructions won't affect the results. Here is the sample input: 
```llvm
define signext i8 @foo(i8 signext, i8 signext, i8 signext, i8 signext) {
; CHECK-LABEL: foo
; CHECK-NEXT: ret i8 123
  %5 = add i8 %1, %0
  %6 = add i8 %5, %2
  %7 = add i8 %6, %3

  ret i8 123
}


define signext i8 @foo_v2(i8 signext %0, i8 signext %1, i8 signext %2, i8 signext %3) {
; CHECK-LABEL: foo_v2
; CHECK-NEXT: ret i8 123
  %5 = xor i8 %1, %0
  %6 = and i8 %1, %0
  %7 = mul i8 2, %6
  %8 = add i8 %5, %7
  %9 = mul i8 39, %8
  %10 = add i8 23, %9
  %11 = mul i8 -105, %10
  %12 = add i8 111, %11
  %13 = xor i8 %12, %2
  %14 = and i8 %12, %2
  %15 = mul i8 2, %14
  %16 = add i8 %13, %15
  %17 = mul i8 39, %16
  %18 = add i8 23, %17
  %19 = mul i8 -105, %18
  %20 = add i8 111, %19
  %21 = xor i8 %20, %3
  %22 = and i8 %20, %3
  %23 = mul i8 2, %22
  %24 = add i8 %21, %23
  %25 = mul i8 39, %24
  %26 = add i8 23, %25
  %27 = mul i8 -105, %26
  %28 = add i8 111, %27
  ret i8 123
}


declare i8* @strcat(i8*, i8*) readonly nounwind willreturn

define void @foo_v3() {
; CHECK-LABEL: foo_v3
; CHECK-NEXT: ret void
  call i8* @strcat(i8* null,  i8* null)
  ret void
}


declare void @llvm.sideeffect()

define void @foo_v4() {
; CHECK-LABEL: foo_v4
; CHECK: call void @llvm.sideeffect()
    call void @llvm.sideeffect()
    ret void
}
```
The example contains four functions, where the former three functions should be optimized and the last function should not be optimized. For the first two functions, they take parameters by value, so the parameters won't be changed. There are only arithmetic operations without side-effects (memory or I/O operations) before the return function, and the value in the return function is a constant, so it is safe to eliminate all the instructions before. For the third function, it calls a function which takes two pointer parameters and returns one pointer parameter. However, in the function declaration, it is "readonly," which means the function would not write to the parameters, and "nounwind," which means the function would not perform I/O operations. Therefore, it is safe to eliminate the function call. Lastly, the final function calls to a side effect function, which could perform I/O operations. Therefore, it should not be eliminated.

The execution command is (as you entered the folder of testing IRs):
```
opt -S --passes=dce dce.ll
```

The output follows the above-mentioned principles:
```llvm
; ModuleID = 'llvm/dce.ll'
source_filename = "llvm/dce.ll"

define signext i8 @foo(i8 signext %0, i8 signext %1, i8 signext %2, i8 signext %3) {
  ret i8 123
}

define signext i8 @foo_v2(i8 signext %0, i8 signext %1, i8 signext %2, i8 signext %3) {
  ret i8 123
}

; Function Attrs: nounwind readonly
declare i8* @strcat(i8*, i8*) #0

define void @foo_v3() {
  ret void
}

; Function Attrs: inaccessiblememonly nounwind willreturn
declare void @llvm.sideeffect() #1

define void @foo_v4() {
  call void @llvm.sideeffect()
  ret void
}

attributes #0 = { nounwind readonly }
attributes #1 = { inaccessiblememonly nounwind willreturn }
```

# Bonus

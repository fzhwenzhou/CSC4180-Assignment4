; ModuleID = ""
target triple = "unknown-unknown-unknown"
target datalayout = ""

declare i32* @"array_of_string"(i8* %".1") 

declare i8* @"string_of_array"(i32* %".1") 

declare i32 @"length_of_string"(i8* %".1") 

declare i8* @"string_of_int"(i32 %".1") 

declare i8* @"string_cat"(i8* %".1", i8* %".2") 

declare void @"print_string"(i8* %".1") 

declare void @"print_int"(i32 %".1") 

declare void @"print_bool"(i32 %".1") 

define i32 @"main"() 
{
entry:
  %"i-2" = alloca i32
  store i32 0, i32* %"i-2"
  br label %"cond"
cond:
  %".4" = load i32, i32* %"i-2"
  %".5" = icmp slt i32 %".4", 10
  br i1 %".5", label %"for", label %"next"
for:
  %".7" = load i32, i32* %"i-2"
  call void @"print_int"(i32 %".7")
  %".9" = getelementptr [2 x i8], [2 x i8]* @"tmp0.7784282332917158", i32 0, i32 0
  call void @"print_string"(i8* %".9")
  %".11" = load i32, i32* %"i-2"
  %".12" = add i32 %".11", 1
  store i32 %".12", i32* %"i-2"
  br label %"cond"
next:
  ret i32 0
}

@"tmp0.7784282332917158" = private constant [2 x i8] c"\0a\00"
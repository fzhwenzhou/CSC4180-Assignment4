; ModuleID = ""
target triple = "riscv64"
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
  %"value-2" = alloca i32
  store i32 10, i32* %"value-2"
  br label %"cond0.6547170412976974"
cond0.6547170412976974:
  %".4" = load i32, i32* %"value-2"
  %".5" = icmp sgt i32 %".4", 0
  br i1 %".5", label %"while0.3623336600138114", label %"wend0.5113298770300008"
while0.3623336600138114:
  %".7" = load i32, i32* %"value-2"
  call void @"print_int"(i32 %".7")
  %".9" = getelementptr [2 x i8], [2 x i8]* @"tmp0.24159074240151268", i32 0, i32 0
  call void @"print_string"(i8* %".9")
  %".11" = load i32, i32* %"value-2"
  %".12" = sub i32 %".11", 1
  store i32 %".12", i32* %"value-2"
  br label %"cond0.6547170412976974"
wend0.5113298770300008:
  ret i32 0
}

@"tmp0.24159074240151268" = private constant [2 x i8] c"\0a\00"
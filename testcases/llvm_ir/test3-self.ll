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
  %"y-2" = alloca i32
  store i32 5, i32* %"y-2"
  %".3" = load i32, i32* %"y-2"
  call void @"print_int"(i32 %".3")
  %".5" = getelementptr [2 x i8], [2 x i8]* @"tmp0.9878587972744131", i32 0, i32 0
  call void @"print_string"(i8* %".5")
  %".7" = load i32, i32* %"y-2"
  %".8" = icmp sgt i32 %".7", 0
  br i1 %".8", label %"then0.5314568631158353", label %"else0.8092935971335848"
then0.5314568631158353:
  %"is_y_positive-3" = alloca i32
  store i32 1, i32* %"is_y_positive-3"
  %".11" = load i32, i32* %"is_y_positive-3"
  call void @"print_bool"(i32 %".11")
  br label %"endif0.5886231480321878"
else0.8092935971335848:
  %"is_y_positive-4" = alloca i32
  store i32 0, i32* %"is_y_positive-4"
  %".15" = load i32, i32* %"is_y_positive-4"
  call void @"print_bool"(i32 %".15")
  br label %"endif0.5886231480321878"
endif0.5886231480321878:
  ret i32 0
}

@"tmp0.9878587972744131" = private constant [2 x i8] c"\0a\00"
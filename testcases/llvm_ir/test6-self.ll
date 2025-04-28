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

define i32 @"add-1"(i32 %".1", i32 %".2") 
{
entry:
  %".4" = alloca i32
  store i32 %".1", i32* %".4"
  %".6" = alloca i32
  store i32 %".2", i32* %".6"
  %".8" = load i32, i32* %".4"
  %".9" = load i32, i32* %".6"
  %".10" = add i32 %".8", %".9"
  ret i32 %".10"
}

define i32 @"main"() 
{
entry:
  %"x-3" = alloca i32
  store i32 15, i32* %"x-3"
  %"y-3" = alloca i32
  store i32 16, i32* %"y-3"
  %".4" = load i32, i32* %"x-3"
  %".5" = load i32, i32* %"y-3"
  %".6" = call i32 @"add-1"(i32 %".4", i32 %".5")
  call void @"print_int"(i32 %".6")
  ret i32 0
}

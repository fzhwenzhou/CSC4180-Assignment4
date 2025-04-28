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

define i32 @"fac-1"(i32 %".1") 
{
entry:
  %".3" = alloca i32
  store i32 %".1", i32* %".3"
  %".5" = load i32, i32* %".3"
  %".6" = icmp slt i32 %".5", 2
  br i1 %".6", label %"then0.9239652165485113", label %"else0.34611750383167805"
then0.9239652165485113:
  ret i32 1
else0.34611750383167805:
  %".9" = load i32, i32* %".3"
  %".10" = sub i32 %".9", 1
  %".11" = call i32 @"fac-1"(i32 %".10")
  %".12" = load i32, i32* %".3"
  %".13" = mul i32 %".11", %".12"
  ret i32 %".13"
endif0.7460736160628325:
  ret i32 0
}

define i32 @"main"() 
{
entry:
  %"t-5" = alloca i32
  store i32 5, i32* %"t-5"
  %".3" = load i32, i32* %"t-5"
  %".4" = call i32 @"fac-1"(i32 %".3")
  call void @"print_int"(i32 %".4")
  ret i32 0
}

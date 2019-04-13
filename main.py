"""
主程序
"""
#coding:utf-8
from lexical_new import Lexical

# 新建词法分析器
lexical = Lexical()
# 载入源代码
lexical.load(open('test.c',encoding='UTF-8').read())
# 执行词法分析
lexical_success = lexical.analyze()
# 打印结果
print('词法分析是否成功:\t', lexical_success)
if lexical_success:
    lexical_result1,lexical_result2 = lexical.get_result()
    print()
    print('词法分析结果:')
    for i in lexical_result1:
        print(i.token_type, i.token_name, i.token_line,i.token_code,i.token_symindex)
    print()
    for i in lexical_result2:
        print(lexical_result2[i].lex_type)
    print()
else:
    lexical_error= lexical.get_error()
    for i in lexical_error:
        print('错误原因:\t', i.info,i.line)
    lexical_result1,lexical_result2 = lexical.get_result()
    for i in lexical_result1:
        print(i.token_type, i.token_name, i.token_line,i.token_code,i.token_symindex)
    print()
    for i in lexical_result2:
        print(lexical_result2[i].lex_type)

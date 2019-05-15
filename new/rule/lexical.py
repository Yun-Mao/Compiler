"""The Rule of Lexical
@Author:YunMao
"""

# 关键字
type_keywords = [
    "auto", "break", "case", "char", "const", "continue",
    "default", "do", "double", "else", "enum", "extern",
    "float", "for", "goto", "if", "int", "long", "register",
    "return", "short", "signed", "static", "sizeof", "struct",
    "switch", "typedef", "union", "unsigned", "void", "volatile", "while"
]
# 标识符
type_id = [
    r'\b[a-zA-Z_]\w*'
]
# 数字
types_num = [
    r'^-?[1-9]\d*\.\d*|-0\.\d*[1-9]\d*',
    r'^-?[1-9]\d*'
]
# 操作数
type_op = [
    r'\+', r'-', r'\*', r'/', r'%', r'==', r'>=', r'<=', r'!=', r'>', r'=', r'<'
]

# 分隔符
type_specialchar = [
    r',',r'\(',r'\)',r'\[',r'\]',r'\{',r'\}',r';',r'\''
]
_type_specialchar_name = [
   'comma','left-parentheses','right-parentheses','left-bracket','right-bracket','left-brace','right-brace','semicolon'
]
# 空格符号
split_char_type = [
    r' +',
]

# 注释
note_char_type = (
    'note-start',
    'note-end',
    'note'
)

# 注释正则表达式
regex_dict = {
    'note': r'//',
    'note-start': r'/\*',
    'note-end': r'\*/'
}

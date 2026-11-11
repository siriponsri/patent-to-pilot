"""Cheap necessary JSON-string prefix filter; exact parser still decides tokens."""


def possible_string_transition(text):
    escaped=False;unicode_remaining=0
    for char in text:
        if unicode_remaining:
            if char not in '0123456789abcdefABCDEF':return False
            unicode_remaining-=1
        elif escaped:
            if char=='u':unicode_remaining=4
            elif char not in '"\\/bfnrt':return False
            escaped=False
        elif char=='\\':escaped=True
        elif char=='"':return True # Remainder is checked by the exact schema parser.
        elif ord(char)<32:return False
    return True # Partial escape/Unicode prefixes remain possible across tokens.

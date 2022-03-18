# -*- coding: utf-8 -*-

def object_type_to_function_comparison(object_type) -> str:
    """
    return postgresql get_{type}def function name (https://www.postgresql.org/docs/current/functions-info.html)
    """
    object_type_to_function = {
        'view': 'pg_get_viewdef',             # pg_get_viewdef ( view oid [, pretty boolean ] ) → text
        'index': 'pg_get_indexdef',           # pg_get_indexdef ( index oid [, column integer, pretty boolean ] ) → text
        'constraint': 'pg_get_constraintdef', # pg_get_constraintdef ( constraint oid [, pretty boolean ] ) → text
        'func': 'pg_get_functiondef',     # pg_get_functiondef ( func oid ) → text
        'rule': 'pg_get_ruledef',             # pg_get_ruledef ( rule oid [, pretty boolean ] ) → text
        'trigger': 'pg_get_triggerdef',       # pg_get_triggerdef ( trigger oid [, pretty boolean ] ) → text
    }
    return object_type_to_function.get(object_type)

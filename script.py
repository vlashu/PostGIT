# -*- coding: utf-8 -*-

import graphviz
import pprint
import string

from copy import deepcopy
from sqlalchemy import create_engine

from include.comparison import object_type_to_function_comparison

def sqlresult(e, sql):
    """
    Метод для выполнения запроса с созданием подключения
    ToDo 
        Либо контролировать отсутствие сессий, либо держать одну, работая в рамках
        одного снэпшота. В текущей реализации между транзакциями возможно изменение БД
    """
    try:
        conn = e.connect()
        result = conn.execute(sql)
        return result
    except:
        raise
    finally:
        conn.close()

def get_graphvis(objects, filename, graph_type):
    """
    Метод для генерации представления графа
    Вход:
        список объектов - list
        имя генерируемого файла .png - str
        тип графа - str (oids, names)
    """
    if graph_type == 'oids':
        parent = lambda object: str(object.oid)
        child = lambda object, node: str(node)
    elif graph_type == 'names':
        parent = lambda object: '.'.join([object.schema_name, object.name])
        child = lambda object, node: '.'.join([objects[node].schema_name, objects[node].name])
        
    g = graphviz.Digraph('G', filename='process.gv', engine='sfdp')
    for object in objects.values():
        for node in object.children:
            g.edge(parent(object), child(object, node))
    g.save() 
    graphviz.render('dot', 'png', 'process.gv', outfile = filename).replace('\\', '/')    
    
class db_object():
    """Общий класс для хранения объектов БД"""
    def __init__(self, oid, schema_name, schema_oid, name, object_type, owner):
        self.oid = oid
        self.schema_name = schema_name
        self.schema_oid = schema_oid
        self.name = name
        self.object_type = object_type
        self.owner = owner
        self.source = None
        self.children = []
        self.parents = []
        self.columns = {}
        self.fkeys = []

        self._get_source()

    def __repr__(self):
        # return '{0}.{1}({2})'.format(self.schema_name, self.name, self.oid)
        column_information = []
        if self.columns:
            for num, data in self.columns.items():
                infos = []
                for cname, cvalue in data.items():
                    infos.append('{0}: {1}'.format(cname, cvalue))
                column_information.append(('                {0}    {1}'.format(num, '  |  '.join(infos))))
        return '''{4} {0}.{1}  
            children:{2}
            parents:{3}
            columns: 
{5}

'''.format(self.schema_name, self.name, self.children, self.parents, self.object_type, '\n'.join(column_information))
        
    def _get_source(self):
        sql = 'select {0}({1})' # ToDo Переделать на f
        sql_source_function = object_type_to_function_comparison(self.object_type)
        if sql_source_function:
            self.source = sqlresult(e, sql.format(sql_source_function, self.oid)).fetchone()[0]
        
    def get_parents(self, oid_object):
        return self.parents

    def add_column(self, num, name, column_type, nullable, col_description):
        try:
            self.columns[num] = {'name':name, 'type':column_type, 'nullable':nullable}#, 'col_description':col_description}
        except:
            pass
            
if __name__ == "__main__":

    e = create_engine('postgresql://postgres:postgres@127.0.0.1:5435/knd02_damp')

    with open('./sql/get_table_all.sql', 'r', encoding='utf-8') as sql:
        all_tables = sqlresult(e, sql.read())
    objects = {}
    for obj in all_tables.fetchall():
        oid, schema_name, schema_oid, name, object_type, owner = obj
        objects[oid] = db_object(oid, schema_name, schema_oid, name, object_type, owner)
    
    with open('./sql/get_fk_all.sql', 'r', encoding='utf-8') as sql:
        all_fk = sqlresult(e, sql.read())
    for fk in all_fk.fetchall():
        fk_from, fk_to, fk_name, fk_sql, _ = fk
        objects[fk_from].parents.append(fk_from)
        objects[fk_to].children.append(fk_from)
        objects[fk_from].fkeys.append(fk)
    
    with open('./sql/get_column_all.sql', 'r', encoding='utf-8') as sql:
        all_columns = sqlresult(e, sql.read())
    for column in all_columns.fetchall():
        oid, num, name, column_type,_ ,nullable,_,_,_,_,_,col_description = column  
        objects[oid].add_column(num, name, column_type, nullable, col_description)
        
    names = {'.'.join([object.schema_name, object.name]).lower().translate(str.maketrans('', '', string.punctuation)):oid for oid, object in objects.items()}
    pprint.pprint(names)
    
    for oid, object in objects.items():
        #print(object.source)
        if object.object_type in ('view'):
            code = self.source.lower().translate(str.maketrans('', '', string.punctuation))
            parents = set(names.keys()) & set(code.split())
            if parents:
                for parent in parents:
                    object.parents.append(names[parent])
    
    pprint.pprint(objects)
    
 #   get_graphvis(objects, 'oids.png','oids')
 #   get_graphvis(objects, 'names.png','names')

# -*- coding: utf-8 -*-
import argparse
import configparser
import graphviz
import os
import pprint
import random
import sys
import string
import subprocess

from progress.bar import IncrementalBar
from sqlalchemy import create_engine
from include.comparison import object_type_to_function_comparison

# ToDo разобраться с последовательностями (sequence), сначала последоватекльность, потом таблица + вынимать последний номер по порядку если есть
# ToDo реализовать создание структуры каталогов для файлов.
# ToDo Переработать дублирование кода в main

# ToDo выделить в класс подключения с хранением параметров подключения###################
# ToDo обработка ошибок в ситуации не все ключи, не та БД, не тот ip, сеттинги битые, добавить -help

def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host')
    parser.add_argument('-p', '--port')
    parser.add_argument('-U', '--username')
    parser.add_argument('-W', '--password')
    parser.add_argument('-d', '--dbname')
    parser.add_argument('-P', '--path')
    parser.add_argument('-S', '--settings', action='store_true')
    return parser

def connect_params(namespace):
    if namespace.settings:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        connparamdict = {name: config.get('conn_settings', name) for name in config.options('conn_settings')}
        path = config.get('path', 'PATH')
    else:
        host =  namespace.host
        port =  namespace.port
        user =  namespace.username
        password = namespace.password
        db = namespace.dbname
        path = namespace.path
        connparamdict = {'host': host, 'port':  port, 'dbname': db, 'username': user, 'password': password}
    return connparamdict, path
#ToDo######################################################################################

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
        g = graphviz.Digraph('G', filename='process.gv', engine='sfdp')
        gnode = lambda object: g.node(parent(object), style='filled', fillcolor=colore.get(object.object_type))

    elif graph_type == 'names':
        parent = lambda object: '.'.join([object.schema_name, object.name])
        child = lambda object, node: '.'.join([objects[node].schema_name, objects[node].name])
        g = graphviz.Digraph('structs', filename='process.gv', node_attr={'shape': 'plaintext'})
        gnode = lambda object: g.node(parent(object), '''<
                <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
                  <TR>
                    <TD>{0}</TD>
                  </TR>
                  <TR>
                    <TD>{1}</TD>
                  </TR>
                  <TR>
                    <TD>{2}</TD>
                  </TR>
                  <TR>
                    <TD>{3}</TD>
                  </TR>
                </TABLE>>'''.format(object.oid, object.schema_name, object.name, object.object_type, ), style='filled',
                                      fillcolor=colore.get(object.object_type))

    colore = {'table': '#40e0d0',
              'view': '#F0E68C',
              'func': '#FFA07A',
              'materialized view': '#90EE90',
              'trigger_func': '#87CEEB',
              'trigger': '#FFDAB9'
              }

    for object in objects.values():
        gnode(object)
        for node in object.children:
            edge_color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
            g.edge(parent(object), child(object, node), color=edge_color)
    g.save() 
    graphviz.render('dot', 'png', 'process.gv', outfile=filename).replace('\\', '/')
    
class db_object():
    """Общий класс для хранения объектов БД"""
    # ToDo перевести на __slots__
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
        self.rank = None
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
            rank:{6}
            columns: 
{5}

'''.format(self.schema_name,
           self.name,
           self.children,
           self.parents,
           self.object_type,
           '\n'.join(column_information),
           self.rank)
        
    def _get_source(self):
        sql_source_function = object_type_to_function_comparison(self.object_type)
        if sql_source_function:
            self.source = sqlresult(e, f'select {sql_source_function}({self.oid})').fetchone()[0]
        elif self.object_type == 'table':  # ToDo Переписать на f  учетом класса подключения.
            self.source = subprocess.check_output('PGPASSWORD="postgres" \
                                                    pg_dump -t {0} \
                                                    --schema-only \
                                                    --host=127.0.0.1 \
                                                    --port=5435 \
                                                    --username=postgres \
                                                    --dbname=knd02_damp'.format('.'.join([self.schema_name, self.name])),
                                                  shell=True).decode("utf-8")

    def write(self):
        with open("repo/{0}.sql".format(self.name), "w") as file:
            file.write("{0}".format(self.source))

    def get_parents(self, oid_object):
        return self.parents

    def add_column(self, num, name, column_type, nullable, col_description):
        try:
            self.columns[num] = {'name':name, 'type':column_type, 'nullable':nullable}#, 'col_description':col_description}
        except:
            pass
            
if __name__ == "__main__":
    # Создал коннект
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    connparams,  path = connect_params(namespace)
    e = create_engine(f"postgresql://{connparams['username']}:{connparams['password']}@{connparams['host']}:{connparams['port']}/{connparams['dbname']}") #ToDo требуется рефактор с учетом класса-подключения
    # Объявляем словарь объектов
    objects = {}

    # Базовые запросы
    with open('./sql/get_table_all.sql', 'r', encoding='utf-8') as sql:
        all_objects = sqlresult(e, sql.read())
    sql_obj_list = all_objects.fetchall()
    bar = IncrementalBar('tables'.ljust(12), max=len(sql_obj_list))
    for obj in sql_obj_list:
        oid, schema_name, schema_oid, name, object_type, owner = obj
        objects[oid] = db_object(oid, schema_name, schema_oid, name, object_type, owner)
        bar.next()
    bar.finish()

    with open('./sql/get_func_trigger_all.sql', 'r', encoding='utf-8') as sql:
        all_objects = sqlresult(e, sql.read())
    sql_obj_list = all_objects.fetchall()
    bar = IncrementalBar('functions'.ljust(12), max=len(sql_obj_list))
    for obj in sql_obj_list:
        oid, schema_name, schema_oid, name, object_type, owner, _, _ = obj
        objects[oid] = db_object(oid, schema_name, schema_oid, name, object_type, owner)
        bar.next()
    bar.finish()

    with open('./sql/get_all_trigger.sql', 'r', encoding='utf-8') as sql:
        all_objects = sqlresult(e, sql.read())
    sql_obj_list = all_objects.fetchall()
    bar = IncrementalBar('triggers'.ljust(12), max=len(sql_obj_list))
    for obj in sql_obj_list:
        oid, schema_name, schema_oid, name, object_type, owner = obj
        objects[oid] = db_object(oid, schema_name, schema_oid, name, object_type, owner)
        bar.next()
    bar.finish()

    with open('./sql/get_fk_all.sql', 'r', encoding='utf-8') as sql:
        all_objects = sqlresult(e, sql.read())
    sql_obj_list = all_objects.fetchall()
    bar = IncrementalBar('fk'.ljust(12), max=len(sql_obj_list))
    for fk in sql_obj_list:
        fk_from, fk_to, fk_name, fk_sql, _ = fk
        objects[fk_from].parents.append(fk_from)
        objects[fk_to].children.append(fk_from)
        objects[fk_from].fkeys.append(fk)
        bar.next()
    bar.finish()

    with open('./sql/get_column_all.sql', 'r', encoding='utf-8') as sql:
        all_objects = sqlresult(e, sql.read())
    sql_obj_list = all_objects.fetchall()
    bar = IncrementalBar('columns'.ljust(12), max=len(sql_obj_list))
    for column in sql_obj_list:
        oid, num, name, column_type,_ ,nullable,_,_,_,_,_,col_description = column  
        objects[oid].add_column(num, name, column_type, nullable, col_description)
        bar.next()
    bar.finish()

    # Подготовка имен объектов для поиска через множества (public.all_users -> publicallusers). Вынужденная история для сравнения с sql
    names = {}
    for oid, object in objects.items():
        names['.'.join([object.schema_name, object.name]).lower().translate(str.maketrans('', '', string.punctuation))] = oid
        names[object.name.lower().translate(str.maketrans('', '', string.punctuation))] = oid # For default (public) schema. ToDo необходимо прикрутить механизм поиска схемы по умолчанию либо получать запрос всегда со схемами.
    # Сравнение имен и sql через set
    for oid, object in objects.items():
        if object.object_type in ('view', 'materialized view', 'func', 'trigger_func', 'trigger'):
            try:
                code = object.source.lower().translate(str.maketrans('', '', string.punctuation))
                parents = set(names.keys()) & set(code.split()) # Пересечение множеств
                if parents:
                    for parent in parents:
                        object.parents.append(names[parent])
                        objects[names[parent]].children.append(object.oid)
            except:
                print(object.oid, object.name, object.source)

    # Ранжирование по очереди создания

    def ranker(all_objects_list, objects, rank, list_ranked):
        #print(len(all_objects_list))
        removed_list = []
        for oid in all_objects_list:
            list_ranked.append(oid)
            if not objects[oid].parents or set(objects[oid].parents).issubset(set(list_ranked)):
                objects[oid].rank = rank
                rank += 1
                removed_list.append(oid)
        return removed_list, rank

    rank = 1
    list_ranked = []
    all_objects_list = [oid for oid in objects.keys()]

    while all_objects_list:
        removed_list, rank = ranker(all_objects_list, objects, rank, list_ranked)
        all_objects_list = list(set(all_objects_list) - set(removed_list))

    # Блок записи ####################################################

    # pprint.pprint(objects) # Все объекты
    # Записываем все объекты в человеческом виде
    with open("repo/objects.txt", "w") as file:
        for obj in objects.values():
            file.write(obj.__repr__())

    # Записываем порядок создания объектов
    with open("repo/order.txt", "w") as file:
        rank_obj = {value.rank: value.schema_name+'.'+value.name for key, value in objects.items()} # Порядок накатки
        for order in sorted(rank_obj.keys()):
            file.write("{1}.sql\n".format(order, rank_obj[order]))

    # Записываем sql файлы
    for obj_oid, obj in objects.items():
        obj.write()

    # Создаем графическое представление
    #get_graphvis(objects, 'oids.png', 'oids')
    #get_graphvis(objects, 'names.png', 'names')


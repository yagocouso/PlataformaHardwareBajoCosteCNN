# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 21:38:06 2021

@author: Yago
"""

from pymongo import MongoClient
import sqlite3
import os
import time

class Conexion:
    def __init__(self, database = 'Finances'):
        con = MongoClient('localhost',27017)
        self.db = con[database]
        
    def client(self, collection):
        return self.db[collection]
    
    def __call__(self, collection):
        return self.db[collection] 
    
class ConexionSQLite:
    def __init__(self, filename = "finances"):
        self.filename = filename if '.db' in filename else filename + '.db'
        self.path_sqlite = os.path.split(os.path.abspath(__file__))[0] + '/' + self.filename
        self.intentos_seguridad = 20
        self.intento = 0
        self.memory = set()
        
        
    @property
    def connect(self):
        self.con = sqlite3.connect(self.path_sqlite, detect_types=sqlite3.PARSE_DECLTYPES,  check_same_thread=False)
        self.cursorObj = self.con.cursor()

    @property
    def close(self):
        self.con.close()
  
    def query(self, query):
        self.connect
        self.cursorObj.execute(query)
        
    def insertData(self, query):
        try:
            self.query(query)
            self.con.commit()
            self.close
            self.intento = 0
            print("Inserccion Completada satisfactoriamente")
        except (sqlite3.OperationalError, sqlite3.ProgrammingError):
            print("Tenemos un error")
            self.connect
            #self.memory.add(query)
            time.sleep(1)
            self.intento += 1
            self.insertData(query) if self.intento <= self.intentos_seguridad else print("Error en la inserccion, paramos..")

            
        
    def getData(self, query):
        self.query(query)
        rows = self.cursorObj.fetchall()
        return rows
    
    def cleanMemory(self):
        #En desarrollo
        for query in self.memory:
            self.memory.pop()
            self.insertData(query)

    def deleteData(self, table):
        self.query(f"DELETE FROM {table}")
        self.close
        
#ver = ConexionSQLite()
#ver.getData("SELECT * FROM FixedIncome")

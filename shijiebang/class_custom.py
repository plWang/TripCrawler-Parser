#!/usr/bin/python
#coding=UTF-8
'''
    @author:wangpenglin
    @date:2016-08-18
    $desc:
        世界邦线路类定义
'''

class Route():
    def __init__(self):
        self.page_id = 'NULL'
        self.title = 'NULL'
        self.tags = 'NULL'
        self.days = 'NULL'
        self.page_url = 'NULL'
        self.description = 'NULL'
        self.popular_time = 'NULL'
        self.route = 'NULL'
        self.full_tags = 'NULL'
        self.price = -1

    def items(self):
        results = []                                                             
        for k,v in self.__dict__.items():                                        
            results.append((k, str(v).decode("UTF-8")))                          
        return results

    def __str__(self):
        for k,v in self.__dict__.items():
            print k, '=>', v
        return 'testEND'
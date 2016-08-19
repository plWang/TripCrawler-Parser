#!/usr/bin/python
#coding=UTF-8
'''
    @author:wangpenglin
    @date:2016-08-18
    $desc:
        世界邦自由行线路抓取和解析
'''

import sys
sys.path.append('../')
sys.path.append('../../lib')

import re
import json
import random
import traceback
import time
import datetime
import requests
import logging
from lxml import html as HTML
from util.Browser import MechanizeCrawler as MC
from common.common import get_proxy
from common.logger import logger
from common.insert_db import InsertShijiebang1
from common.city_common import City
from common.station_common import Station
from common.task import Task
from common.city_common import City
from common.db import ExecuteSQL
from class_custom import Route
reload(sys)
sys.setdefaultencoding('utf-8')

PROXY_NONE = 21
TASK_ERROR = 12
PROXY_INVALID = 22
PROXY_FORBIDDEN = 23
DATA_NONE = 24
UNKNOWN_TYPE = 25
DEBUG = True

page_id_pat = re.compile(r'.*/(\d+)/')
time_pat = re.compile(r'\d+月')

def get_url_list():
    url_ori = "http://www.shijiebang.com/powers/?sort=1"
    mc = MC()
    mc.set_debug(True)
    p = get_proxy(source='ctripFlight')
    if p == None or p == '':
        logger.error('SHIJIEBANG :: get proxy failed.')
        result['error'] = 21
        return result
    print "proxy: %s"% p
    #mc.set_proxy(p)
    res = get_page(url_ori, mc)
    page = res['content']
    host = "http://www.shijiebang.com"
    url_list = [url_ori]
    result = {'proxy': '', 'error': 0, 'content': url_list}
    try: 
        html = HTML.fromstring(page.decode('utf-8'))
        total_count = html.find_class('mod-super-result')[0].xpath('./em/text()')[0]
        print "total_count: %s"% total_count
    except Exception, e:
        traceback.print_exc(str(e))
        print "Can't get total_count"
        result['error'] = 25
        return result
    
    while True:
        try:
            paging = html.find_class('paging')[0]
            try:
                next_page = paging.xpath('./a[@class="paging-next"]/@href')[0]
            except Exception, e:
                traceback.print_exc(str(e))
                print "Can't find next page url, quit"
                break
            url_next = host + next_page
            print "next_page: %s"% url_next
            url_list.append(url_next)
            res = get_page(url_next, mc)
            if res['error'] != 0:
                print "get page failed, try again"
                res = get_page(url_next, mc)
            if res['error'] != 0:
                print "get page failed again, quit!!!!"
            page = res['content']
            html = HTML.fromstring(page.decode('utf-8'))

        except Exception, e:
            traceback.print_exc(str(e))
            result['error'] = 25
            return result

    return result

def get_page(url, mc=None):
    result = {'proxy': '', 'error': 0, 'content': ''}
    if not mc:
        mc = MC()
        mc.set_debug(True)
        p = get_proxy(source='ctripFlight')
        if p == None or p == '':
            logger.error('SHIJIEBANG :: get proxy failed.')
            result['error'] = 21
            return result
        print "proxy: %s"% p
        #mc.set_proxy(p)
    try:
        page = mc.req('get', url, html_flag=True)
    except Exception, e:
        result['error'] = 22
        return result
    print "Get page Done!!!"
    if len(page) < 1000:
        result['error'] = 22
        return result
    result['content'] = page
    with open('page.html', 'w')as f:
        f.write(page)
    return result

def list_page_parser(page):
    result = {'proxy': '', 'error': 0, 'content': {'routes': [], 'url_list': []}}
    host = "http://www.shijiebang.com"
    routes = []
    url_list = []
    try:
        html = HTML.fromstring(page.decode('utf-8'))
        root = html.find_class('mod-super-list')[0]
        route_list = root.find_class('item init')
        print route_list
        for route in route_list:
            route_new = Route()
            body = route.xpath('./div[1]/div[@class="c-txt"]/a')[0]
            title = body.xpath('./h3/text()')
            day = body.xpath('./h3/em/text()')[0]
            title = title[0] + day + title[1]
            #print "title: %s"% title
            page_url = body.xpath('./@href')[0]
            page_url = host + page_url
            url_list.append(page_url)
            page_id = page_id_pat.findall(page_url)[0]
            #print "page_url: %s"% page_url
            tags = body.xpath('./div[@class="cell-light-tag"]/div[@class="c-light-tag"]/text()')
            #print '|'.join(tags)
            price_tmp = body.xpath('./div[@class="price-wrap"]/span/em/text()')[0]
            price = float(price_tmp.replace(',', ''))
            #print "price: %s"% price
            try:
                other_day = route.xpath('./div[@class="other-day"]/table[1]/tr[1]/td')
                #print "other day: %s"% other_day
                days = []
                for td in other_day:
                    s = td.xpath('./a/text()')[0]
                    days.append(s)
                #print "days: %s"% '-'.join(days)
            except:
                pass
            route_new.page_id = page_id
            route_new.title = title
            route_new.tags = '|'.join(tags)
            if days != []:
                route_new.days = '-'.join(days)
            route_new.page_url = page_url
            route_new.price = price
            route_tuple = (route_new.page_id, route_new.title, route_new.tags, \
                route_new.days, route_new.page_url, route_new.description, \
                route_new.popular_time, route_new.route, route_new.full_tags, route_new.price)
            routes.append(route_tuple)
            print "********************************"
            print route_new


    except Exception, e:
        traceback.print_exc(str(e))
        result['error'] = 25
        return result

    result['content']['routes'] = routes
    result['content']['url_list'] = url_list
    return result


def detail_page_parser(url):
    result = {'proxy': '', 'error': 0, 'content': {'routes': []}}
    host = "http://www.shijiebang.com"
    route = Route()
    page_id = page_id_pat.findall(url)[0]
    print "page_id: %s"% page_id
    mc = MC()
    mc.set_debug(True)
    p = get_proxy(source='ctripFlight')
    if p == None or p == '':
        logger.error('SHIJIEBANG :: get proxy failed.')
        result['error'] = 21
        return result
    print "proxy: %s"% p
    #mc.set_proxy(p)
    res = get_page(url, mc)
    if res['error'] != 0:
        result['error'] = res['error']
        return result
    page = res['content']
    html0 = HTML.fromstring(page.decode('utf-8'))
    try:
        page_url = html0.find_class("layout-auto mod-follow-nav js-follow-nav")[0].\
                    find_class("drop-menu")[0].xpath('./a[1]/@href')[0]
        map_url = host + page_url.replace('detail', 'map')
        print "page_url: %s"% map_url
    except Exception, e:
        print "Can't find page url: ", str(e)
        result['error'] = 25

    try:
        page1 = mc.req('get', map_url, html_flag=True)
    except Exception, e:
        result['error'] = 22
        return result
    if len(page1) < 1000:
        result['error'] = 22
        return result
    html1 = HTML.fromstring(page1.decode('utf-8'))
    summary = html1.get_element_by_id("trip-reader").find_class("summary")
    description = summary[0].xpath('./p/text()')[0]
    tags = summary[1].xpath('./p/span/text()')
    print "description: %s"% description
    tags = '|'.join(tags)
    print "tags: %s"% tags
    popular_time = time_pat.findall(tags.encode('utf-8'))
    print "popular_time: %s"% popular_time
    popular_time = '|'.join(popular_time)

    route_container = html1.find_class("trip-bd mod-hp trip-map-bd")[0]
    lis = route_container.xpath('./ul[1]/li[@class="tab"]')
    print len(lis)
    city_list = []
    for li in lis:
        city = li.xpath('./span[@class="place"]/text()')[0]
        if city not in city_list:
            city_list.append(city)
    print "citys: %s"% ('_'.join(city_list))

    route.page_id = page_id
    route.description = description
    route.full_tags = tags
    route.popular_time = popular_time
    route.route = '_'.join(city_list)
    print route


    return result


def shijiebang_task_parser():
    #result = get_page()
    #page = result['content']
    #result = list_page_parser(page)

    # result = get_url_list()
    # print "SHIJIEBANG: error code: %s"% result['error']
    # url_list = result['content']
    # print url_list
    # f = open('url_list', 'w')
    # for url in url_list:
    #     f.write(url + '\n')
    # f.close()
    pass
    


def parse_detail_page():
    url = "http://www.shijiebang.com/super/1806/"
    result = detail_page_parser(url)

def parse_list_page():
    url = "http://www.shijiebang.com/powers/?sort=1"
    print "Start a new task: %s"% url
    res = get_page(url)
    page = res['content']
    result = list_page_parser(page)
    detail_url_list = result['content']['url_list']
    print detail_url_list
    routes = result['content']['routes']
    #print routes
    # try:
    #     ret = InsertShijiebang1(routes)
    # except Exception, e:
    #     traceback.print_exc(str(e))
    #     print "Insert into DB failed"
    for route in routes:
        sql = 'INSERT INTO shijiebang (page_id, title, tags, days, page_url, description, popular_time, route, full_tags, price) VALUES ("%s", "%s", "%s", "%s", "%s", "%s" ,"%s", "%s", "%s", "%s")'\
                % (route[0], route[1], route[2], route[3], route[4], route[5], route[6], route[7], route[8], route[9])
        print sql
        try: 
            ret = ExecuteSQL(sql)
        except Exception, e:
            print route
            #traceback.print_exc(str(e))
            print "Insert into DB failed"
            break




if __name__ == '__main__':
    #shijiebang_task_parser()
    #parse_detail_page()
    parse_list_page()



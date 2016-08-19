#!/bin/env/python
#coding=utf-8
import time
import Queue
import threading
import sys
sys.path.append('../')
#from dbworkload import get_task, get_single_task
from get_task import get_task, get_single_task
from common.task import Task
from common.logger import logger
from ctripTW import ctripTWParser

class Runner(threading.Thread):
    def __init__(self, queue, out_queue): 
        threading.Thread.__init__(self)
        self._queue = queue
        self.out_queue = out_queue
        ## modify Parser
        self.parser = ctripTWParser() 

    def run(self):
        while True: 
            task = self._queue.get() 
            if isinstance(task, str) and task == 'quit':
                break
            ## param: task or content
            error, p = self.parser.parse(task)
            self.out_queue.put((task.content, p, error))
        print 'Bye byes!'

def build_worker_pool(queue, out_queue, size):
    workers = []
    for _ in range(size):
        worker = Runner(queue, out_queue)
        worker.start() 
        workers.append(worker)
    return workers

def report(error_dict):
    print "****************** TEST REPORT *******************"
    for key in error_dict:
        print "--- 错误码%s: %s个 ---"% (key, error_dict[key]['count'])
        for case in error_dict[key]['cases']:
            print case

if __name__ == '__main__':
    ## modify Parser and source
    parser = ctripTWParser()
    source = 'ctripTWRail'

    if sys.argv[1] == "1":
        task = Task()
        task.source = source
        #task.ticket_info['flight_no'] = "F90560_F90324"
        #workload_key = sys.argv[2]
        #info = sys.argv[3]
        #task.ticket_info['flight_no'] = info
        #print workload_key
        #task.content = get_single_task(source, workload_key)[0]['content']
        task.content = get_single_task()
        print "task content: %s"% task.content
        ## param: task or content
        error, p = parser.parse(task)
        logger.info('task proxy: %s'% p)
        logger.info('task error code: %s'% error)
    elif sys.argv[1] == '2':
        tasks = get_task(source)
        print tasks
        error_count = 0
        error_dict = {}
        q = Queue.Queue()
        out_q = Queue.Queue()
        worker_threads = build_worker_pool(q, out_q, 30)
        start_time = time.time()
        for each in tasks:
            task = Task()
            task.source = source
            task.content = each
            q.put(task)
        for worker in worker_threads:
            q.put('quit')
        for worker in worker_threads:
            worker.join()

        print 'Done! Time taken: {0}'.format(time.time() - start_time)
        while not out_q.empty():
            s = out_q.get()
            error = s[2]
            if error != 0:
                error_count += 1
            if error_dict.has_key(error):
                error_dict[error]['count'] += 1
                error_dict[error]['cases'].append(s)
            else:
                d = {'count': 0, 'cases': []}
                error_dict[error] = d
                error_dict[error]['count'] += 1
                error_dict[error]['cases'].append(s)
        print "error_count: %s"% error_count
        report(error_dict)
    else:
        task = Task()
        task.source = source
        #task.ticket_info['flight_no'] = 'VX1936_HU7924_HU7626'
        task.content = sys.argv[2]
        print "task content: %s"% task.content
        ## param: task or content
        error, p = parser.parse(task)
        logger.info('task proxy: %s'% p)
        logger.info('task error code: %s'% error)

#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2014, Matthew Doiron. All rights reserved.

IDF+ is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

IDF+ is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with IDF+. If not, see <http://www.gnu.org/licenses/>.
"""

# System imports
import sys
import logging
import multiprocessing as mp
from whoosh.fields import Schema, ID
from whoosh import index
from whoosh.writing import IndexingError
from Queue import Empty

# Package imports
from . import config

# Setup logging
log = logging.getLogger(__name__)


class IDFIndex(object):

    def __init__(self, index_name):
        log.debug('Initializing indexer.')
        schema = Schema(uuid=ID(unique=True, stored=True),
                        obj_class=ID(stored=True),
                        value=ID(stored=True))
        # Could save index and re-use if unmodified, but for now recreate each time
        # index_exists = index.exists_in(config.DATA_DIR, indexname=index_name)
        # if not index_exists:
        #     self.index = index.create_in(config.DATA_DIR, schema=schema, indexname=index_name)
        # else:
        #     self.index = index.open_dir(config.DATA_DIR, indexname=index_name)
        self.index = index.create_in(config.DATA_DIR, schema=schema, indexname=index_name)
        self.job_queue = mp.JoinableQueue()
        self.worker_process = None

    def start_worker(self):

        log.debug('Worker starting...')

        # Hack to make this work with PyCharm IDE
        if not hasattr(sys.stdin, 'close'):
            def dummy_close():
                pass
            sys.stdin.close = dummy_close

        self.worker_process = mp.Process(target=self.worker, name='idf_indexer',
                                         args=(self.job_queue,))
        self.worker_process.start()

    def stop_worker(self):
        """Cleanly stops the worker process
        """

        log.debug('Stopping indexing worker...')
        self.job_queue.put('COMMIT')
        self.job_queue.put('STOP')
        self.job_queue.join()
        log.debug('Terminating worker process...')
        self.worker_process.join()
        self.worker_process.terminate()
        log.debug('Worker status: {}'.format(self.worker_process.is_alive()))

    def open_writer(self):
        """Opens a writer for the index
        """

        procs_count = 1 if mp.cpu_count() - 1 <= 1 else mp.cpu_count() - 1
        writer = self.index.writer(procs=procs_count, limitmb=128)
        return writer

    def worker(self, job_queue):
        """Worker to retrieve and process indexing jobs.

        :param job_queue: Queue containing documents to be indexed
        """

        # print('Worker started')

        job = None
        retry = False
        retry_count = 0
        writer = self.open_writer()

        while job != 'STOP':
            try:
                # Grab a job from the queue or use previous one
                if retry is True:
                    retry = False
                else:
                    job = job_queue.get(timeout=0.3)

                # Write the document to the index or commit the changes
                if job == 'COMMIT' or job == 'STOP':
                    writer.commit()
                    if job != 'STOP':
                        writer = self.open_writer()
                else:
                    writer.add_document(**job)

                if retry is False:
                    job_queue.task_done()

            except Empty:
                # print('Queue currently empty, waiting for a job...')
                pass
            except IndexingError:
                if retry_count > 5:
                    raise
                # print('No open writer. Opening one!')
                writer = self.open_writer()
                retry = True
                retry_count += 1

        # print('Worker stopped!')

    def add_document(self, document):
        self.job_queue.put(document)

    def commit(self):
        log.debug('Committing changes to index.')
        self.job_queue.put('COMMIT')
        self.job_queue.join()

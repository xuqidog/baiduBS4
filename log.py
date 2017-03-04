import os
import logging
import datetime
from logging.handlers import BaseRotatingHandler

log_base_dir = "./logs"
log_to_file = True


class LogHandler(BaseRotatingHandler):
    def __init__(self, filename, maxbytes=30 * 1024 * 1024, mode='a', encoding=None, delay=0):
        if maxbytes > 0:
            mode = 'a'
        self.index = 0
        self.maxBytes = maxbytes
        self.createdate = datetime.datetime.now().strftime("%Y%m%d")
        BaseRotatingHandler.__init__(self, filename, mode, encoding, delay)

    def shouldRollover(self, record):
        if self.stream is None:
            self.stream = self._open()
        if datetime.datetime.now().strftime("%Y%m%d") != self.createdate:
            return 1
        if self.maxBytes > 0:
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        return 0

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
            dfn = self.baseFilename + '_' + self.createdate + '_' + str(self.index)
            if os.path.exists(self.baseFilename):
                os.rename(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()
        curdate = datetime.datetime.now().strftime("%Y%m%d")
        if curdate == self.createdate:
            self.index += 1
        else:
            self.createdate = curdate
            self.index = 0


class Logger(logging.Logger):
    def findCaller(self):
        f = logging.currentframe()
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if 'log_mixin.py' in filename or filename == logging._srcfile:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break
        return rv


class LogMixin(object):
    def init_logger(self):
        if hasattr(self.__class__, 'logger_inited'):
            return
        logging.setLoggerClass(Logger)
        if hasattr(self.__class__, "logBaseDir"):
            log_base_name = getattr(self.__class__, "logBaseDir")
        else:
            log_base_name = "default"
        setattr(self.__class__, 'log_base_name', log_base_name)
        log_dir = os.path.abspath(os.path.join(log_base_dir, log_base_name))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            os.chmod(log_dir, 0775)

        fmt = "[%(asctime)s-%(levelname)s-%(filename)s-%(lineno)d]-%(message)s"
        fmt = logging.Formatter(fmt)
        level_names = dict(debug=logging.DEBUG, info=logging.INFO, warning=logging.WARNING, error=logging.ERROR)
        for n, l in level_names.items():
            log_name = '%s_%s' % (log_base_name, n)
            logger = logging.getLogger(log_name)
            logger.setLevel(l)
            if log_to_file:
                path = os.path.join(log_dir, "%s.log" % (n))
                handler = LogHandler(path)
            else:
                handler = logging.StreamHandler()
            handler.setFormatter(fmt)
            logger.addHandler(handler)
            setattr(self.__class__, log_name, logger)
        setattr(self.__class__, 'logger_inited', True)

    def get_logger(self, level_name):
        self.init_logger()
        log_base_name = getattr(self.__class__, 'log_base_name')
        logger_name = '%s_%s' % (self.log_base_name, level_name)
        logger = getattr(self.__class__, logger_name)
        return logger

    def log_debug(self, msg, *args, **kwargs):
        self.get_logger('debug').debug(msg, *args, **kwargs)

    def log_info(self, msg, *args, **kwargs):
        self.get_logger('info').info(msg, *args, **kwargs)

    def log_warning(self, msg, *args, **kwargs):
        self.get_logger('warning').warning(msg, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        self.get_logger('error').error(msg, *args, **kwargs)

    def log_exception(self, msg, *args, **kwargs):
        self.get_logger('error').exception(msg, *args, **kwargs)

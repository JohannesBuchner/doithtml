import sys
import time
import datetime
import cgi

class TaskResult(object):
    """result object used by JsonReporter"""
    # FIXME what about returned value from python-actions ?
    def __init__(self, task):
        self.task = task
        self.result = None # fail, success, up-to-date, ignore
        self.out = None # stdout from task
        self.err = None # stderr from task
        self.error = None # error from doit (exception traceback)
        self.started = None # datetime when task execution started
        self.elapsed = None # time (in secs) taken to execute task
        self._started_on = None # timestamp
        self._finished_on = None # timestamp

    def start(self):
        """called when task starts its execution"""
        self._started_on = time.time()

    def set_result(self, result, error=None):
        """called when task finishes its execution"""
        self._finished_on = time.time()
        self.result = result
        if self.task is None:
            self.out = ''
            self.err = ''
        else:
            line_sep = "\n<hr>\n"
            self.out = line_sep.join([a.out for a in self.task.actions if a.out])
            self.err = line_sep.join([a.err for a in self.task.actions if a.err])
        self.error = error
    def get_status(self):
        if self.result is None:
            if self._started_on is None:
                return 'notstarted'
            elif self._finished_on is None:
                return 'running'
        return self.result
    def to_dict(self):
        """convert result data to dictionary"""
        if self._started_on is not None:
            started = datetime.datetime.utcfromtimestamp(self._started_on)
            self.started = str(started)
            self.elapsed = self._finished_on - self._started_on
        return {'name': self.task.name,
                'result': self.result,
                'out': self.out,
                'err': self.err,
                'error': self.error,
                'started': self.started,
                'elapsed': self.elapsed}


class HtmlReporter(object):
    """write current status in HTML file """

    desc = 'write current status in HTML file'
    header = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>DoIt Status Report</title>
<link rel="stylesheet" href="doit-report.css" type="text/css" />
</head>
<body>
<h1>DoIt Status Report</h1>

"""

    def __init__(self, outstream, options=None): #pylint: disable=W0613
        # options parameter is not used
        # json result is sent to stdout when doit finishes running
        self.t_results = {}
        self.t_all = []
        self.errors = []
    def initialize(self, tasks):
       """called just after tasks have been loaded before execution starts"""
       for task in tasks:
           self.t_results[task] = TaskResult(None)
       self.t_all = tasks
       
    def get_status(self, task):
        """called when task is selected (check if up-to-date)"""
        if task.name not in self.t_results or self.t_results[task.name].task is None:
           self.t_results[task.name] = TaskResult(task)

    def execute_task(self, task):
        """called when excution starts"""
        self.t_results[task.name].start()
        self.update()

    def add_failure(self, task, exception):
        """called when excution finishes with a failure"""
        self.t_results[task.name].set_result('fail', exception.get_msg())
        self.update()

    def add_success(self, task):
        """called when excution finishes successfuly"""
        self.t_results[task.name].set_result('success')
        self.update()

    def skip_uptodate(self, task):
        """skipped up-to-date task"""
        self.t_results[task.name].set_result('uptodate')
        self.update()

    def skip_ignore(self, task):
        """skipped ignored task"""
        self.t_results[task.name].set_result('ignore')
        self.update()

    def cleanup_error(self, exception):
        """error during cleanup"""
        self.errors.append(exception.get_msg())

    def runtime_error(self, msg):
        """error from doit (not from a task execution)"""
        self.errors.append(msg)

    def teardown_task(self, task):
        """called when starts the execution of teardown action"""
        pass
    def update(self):
        """ write status report to file """
        with open("dodo-report.html", 'w') as f:
            try:
                f.write(open('dodo-report-header.html').read())
            except IOError:
                f.write(HtmlReporter.header)
            nstatus = {}
            rows = []
        	
            for taskname, tr in self.t_results.iteritems():
                status = tr.get_status()
                nstatus[status] = nstatus.get(status, []) + [(taskname, tr)]
        	
            ntotal = len(self.t_results)
            logs = []
            f.write("<div class='status'><h2>Progress</h2>\n")
            f.write("<div class='progress'>\n")
            for k, symbol in zip(['uptodate', 'ignore', 'success', 'fail', 'running', 'notstarted'], ['U','_','#','!','R','.']):
                f.write("<span class='progress %s'>" % cgi.escape(k))
                for taskname, tr in nstatus.get(k, []):
                    htmlname = cgi.escape(taskname)
                    status = tr.get_status()
                    htmlclass = status
                    rows.append("<tr class='%s'><td><a name='status-%s' href='#log-%s'>%s</a></th><td>%s</td></tr>" % (htmlclass, htmlname, htmlname, htmlname, status))
                    f.write('<a href="#status-%s">%s</a>' % (htmlname, symbol))

                    logtxt = "<h3><a name='%s'>%s</a></h3>\n" % (taskname, taskname)
                    logtxt += "<pre class='log stderr'>%s</pre>\n" % tr.err
                    logtxt += "<pre class='log stdout'>%s</pre>\n" % tr.out
                    logs.append(logtxt)
        	    f.write("</span>")
            f.write("</div>\n")
            f.write("<div class='status'><h2>Status</h2>\n")
            f.write("<table>\n")
            f.write("<thead><tr><th>Task</th><th>Status</th></tr></thead>\n")
            f.write("<tbody>\n")
            f.write("\n".join(rows))
            f.write("\n</table>\n")
            f.write("<div class='logs'><h2>Logs</h2>\n")
            f.write("\n".join(logs))
    
    def complete_run(self):
        """called when finshed running all tasks"""
        self.update()


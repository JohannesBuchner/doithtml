from doithtml import HtmlReporter
DOIT_CONFIG = {'reporter': HtmlReporter}

def gen_tasks():
	for l in range(1, 100):
		yield dict(basename='task%d' % l,
			actions=[['./run.sh', '%d' % l]],
			file_dep=['in/%d' % l],
			targets=['out/%d' % l],
			)

def task_all():
	yield gen_tasks()


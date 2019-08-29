# auckland_traffic
Monitoring the traffic of Auckland

TODO:
    celery on_success on_failure hook
        ```
        class CallbackTask(Task):
            def on_success(self, retval, task_id, args, kwargs):
                pass

            def on_failure(self, exc, task_id, args, kwargs, einfo):
                pass


        @celery.task(base=CallbackTask)  # this does the trick
        def add(x, y):
            return x + y
        ```

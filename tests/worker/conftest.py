def retry_side_effect(**kwargs):
    task = kwargs['task']
    max_retries = getattr(task,
                          'override_max_retries',
                          getattr(task, 'retry_kwargs',
                                  {"max_retries": 0})["max_retries"])
    if task.request.retries < max_retries:
        raise task.retry(countdown=0, max_retries=1)

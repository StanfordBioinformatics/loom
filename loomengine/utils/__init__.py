import logging
import random
import time

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())


def execute_with_retries(retryable_function,
                         retryable_errors,
                         logger,
                         human_readable_action_name='Action'):
    """This attempts to execute "retryable_function" with exponential backoff
    on delay time.
    10 retries adds up to about 34 minutes total delay before the last attempt.
    "human_readable_action_name" is an option input to customize retry message.
    """
    max_retries = 10
    attempt = 0
    while True:
        try:
            return retryable_function()
        except tuple(retryable_errors) as e:
            attempt += 1
            if attempt > max_retries:
                raise
            # Exponentional backoff on retry delay as suggested by
            # https://cloud.google.com/storage/docs/exponential-backoff
            delay = 2**attempt + random.random()
            logger.info('"%s" failed with error "%s". '\
                        'Retry number %s of %s in %s seconds'
                        % (human_readable_action_name, str(e),
                           attempt, max_retries, delay))
            time.sleep(delay)

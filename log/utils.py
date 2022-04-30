import logging


def log_deco(logger: logging.Logger = None):
    def log_deco_inner(func):
        def wrap(*args, **kwargs):
            try:
                logger.debug(
                    f"Была вызвана функция {func.__name__} c параметрами {args}, {kwargs}. ",
                    stacklevel=2,
                )
                res = func(*args)
            except:
                logger.error(
                    f"Функция {func.__name__} с параметрами {args}, {kwargs} выполнена с ошибкой.",
                    stacklevel=2,
                )
                raise ValueError
            return res

        return wrap

    return log_deco_inner

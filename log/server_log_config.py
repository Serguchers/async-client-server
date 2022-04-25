import logging
import logging.handlers


_format = logging.Formatter("%(asctime)s - %(levelname)s - %(module)-20s %(message)s")
log_hand = logging.FileHandler("log/server_logs/server.log", encoding='utf-8')
log_hand.setFormatter(_format)

log = logging.getLogger('server_logger')
log.addHandler(log_hand)
log.setLevel(logging.DEBUG)


if __name__ == "__main__":
    log.info('Test')
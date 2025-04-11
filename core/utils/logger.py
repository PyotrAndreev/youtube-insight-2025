import logging

def setup_logger(name: str) -> logging.Logger:
    """
    Настраивает и возвращает логгер с заданным именем.
    Логгер выводит сообщения в консоль с уровнем DEBUG и выше.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Проверяем, есть ли уже обработчики, чтобы избежать дублирования
    if not logger.handlers:
        # Создаем обработчик вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Устанавливаем формат вывода
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Добавляем обработчик к логгеру
        logger.addHandler(console_handler)

    return logger

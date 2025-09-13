# postgres-init/Dockerfile
FROM postgres:17

# Устанавливаем пакет locales для поддержки локалей
RUN apt-get update && \
    apt-get install -y --no-install-recommends locales && \
    rm -rf /var/lib/apt/lists/*

# Генерируем русскую локаль ru_RU.UTF-8
RUN localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8

# Устанавливаем переменные окружения по умолчанию (важно: до запуска initdb!)
ENV LANG=ru_RU.UTF-8
ENV LC_ALL=ru_RU.UTF-8

# Не нужно копировать никакие скрипты — всё делается через POSTGRES_* переменные
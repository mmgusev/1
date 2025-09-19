FROM postgres:17

RUN apt-get update && \
    apt-get install -y --no-install-recommends locales && \
    rm -rf /var/lib/apt/lists/*

RUN localedef -i ru_RU -c -f UTF-8 -A /usr/share/locale/locale.alias ru_RU.UTF-8

ENV LANG=ru_RU.UTF-8
ENV LC_ALL=ru_RU.UTF-8

COPY ./postgres-sql/ /docker-entrypoint-initdb.d/

# Подменяем appuser → app_user
RUN find /docker-entrypoint-initdb.d/ -name "*.sql" -exec sed -i 's/appuser/app_user/g' {} \;

# Удаляем строки с \connect
RUN find /docker-entrypoint-initdb.d/ -name "*.sql" -exec sed -i '/\\connect/d' {} \;
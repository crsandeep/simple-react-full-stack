FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY prod.conf /etc/nginx/conf.d/prod.conf
COPY staging.conf /etc/nginx/conf.d/staging.conf
COPY check_health.sh /check_health.sh

RUN chmod +x /check_health.sh

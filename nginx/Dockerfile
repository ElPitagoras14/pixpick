FROM nginx:1.30.4

# The template stays outside conf.d; only its substituted output belongs
# there.
COPY nginx.conf.template /etc/pixpick/nginx.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

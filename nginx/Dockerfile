FROM nginx:1.30.4

# The template stays outside conf.d; only its substituted output belongs
# there (D3 in harden-local-profile's design, same shape as the frontend's
# own config.template.js / entrypoint.sh).
COPY nginx.conf.template /etc/pixpick/nginx.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

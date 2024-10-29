# Use the alpine image as the base
FROM alpine:latest

# Update the package list and install necessary packages
RUN apk update && \
    apk add --no-cache stress-ng busybox curl

# Set up cron job
RUN echo "*/30 * * * * /usr/local/bin/stress_script.sh" > /var/spool/cron/crontabs/root

# Start cron in the foreground
CMD ["crond", "-f"]

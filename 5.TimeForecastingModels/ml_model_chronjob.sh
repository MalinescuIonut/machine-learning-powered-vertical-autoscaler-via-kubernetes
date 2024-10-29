#!/bin/sh

# Write the cron job to a file
echo "*20,50 * * * * cd /python-scripts && /usr/local/bin/python arima_model.py >> forecast.log 2>&1" > /etc/cron.d/arima-forecast

# Load the cron job
crontab /etc/cron.d/arima-forecast

# Run cron in the foreground
cron -f

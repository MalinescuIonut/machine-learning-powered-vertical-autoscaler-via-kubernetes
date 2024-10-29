echo "*20,50 * * * * cd /python-scripts && /usr/local/bin/python arima_model.py >> forecast.log 2>&1" > /etc/cron.d/arima-forecast &&
crontab /etc/cron.d/arima-forecast &&
cron -f

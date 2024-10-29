echo "20,50 * * * * cd /python-scripts && /usr/local/bin/python arima_model.py >> forecast.log 2>&1" > /etc/cron.d/arima-forecast && 
echo "20,50 * * * * cd /python-scripts && sleep 1m && /usr/local/bin/python scaling.py >> scaling.log 2>&1" >> /etc/cron.d/arima-forecast &&

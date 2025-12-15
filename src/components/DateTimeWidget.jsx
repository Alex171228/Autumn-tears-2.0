import React, { useState, useEffect, memo } from 'react';

function DateTimeWidget() {
  const [dateTime, setDateTime] = useState('--:--\n--.--.----');

  useEffect(() => {
    const updateDateTime = () => {
      const now = new Date();
      const pad = n => String(n).padStart(2, "0");
      const timeStr = pad(now.getHours()) + ":" + pad(now.getMinutes());
      const dateStr = pad(now.getDate()) + "." + pad(now.getMonth() + 1) + "." + now.getFullYear();
      setDateTime(timeStr + "\n" + dateStr);
    };

    updateDateTime();
    const interval = setInterval(updateDateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div id="datetimeWidget">
      <div id="datetimeLabel">{dateTime}</div>
    </div>
  );
}

export default memo(DateTimeWidget);


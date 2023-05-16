CREATE VIEW `warm-portfolio-project.weather_project.saimai_view` AS
SELECT 
  SPLIT(dt, " ")[0] AS date,
  SPLIT(dt, " ")[1] AS time,
  SPLIT(sunrise, " ")[1] AS sunrise_time,
  SPLIT(sunset, " ")[1] AS sunset_time,
  `temp` AS temperature,
  feels_like,
  pressure,
  humidity,
  dew_point,
  uvi,
  clouds,
  visibility,
  wind_speed,
  wind_deg AS wind_degree,
  main AS weather_main,
  description AS weather_description,
  aqi,
  co,
  `no`,
  no2,
  o3,
  so2,
  pm2_5,
  pm10,
  nh3,
  wind_gust,
  rain
FROM `warm-portfolio-project.weather_project.weather_table_saimai`
WHERE dt in (
  SELECT MAX(dt)
  FROM `warm-portfolio-project.weather_project.weather_table_saimai`
);

CREATE VIEW `warm-portfolio-project.weather_project.pathumwan_view` AS
SELECT 
  SPLIT(dt, " ")[0] AS date,
  SPLIT(dt, " ")[1] AS time,
  SPLIT(sunrise, " ")[1] AS sunrise_time,
  SPLIT(sunset, " ")[1] AS sunset_time,
  `temp` AS temperature,
  feels_like,
  pressure,
  humidity,
  dew_point,
  uvi,
  clouds,
  visibility,
  wind_speed,
  wind_deg AS wind_degree,
  main AS weather_main,
  description AS weather_description,
  aqi,
  co,
  `no`,
  no2,
  o3,
  so2,
  pm2_5,
  pm10,
  nh3,
  wind_gust,
  rain
FROM `warm-portfolio-project.weather_project.weather_table_pathumwan`
WHERE dt in (
  SELECT MAX(dt)
  FROM `warm-portfolio-project.weather_project.weather_table_pathumwan`
);

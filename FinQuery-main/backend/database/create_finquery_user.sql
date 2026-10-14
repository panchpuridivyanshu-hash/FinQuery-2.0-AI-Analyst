CREATE USER IF NOT EXISTS 'finquery_app'@'localhost'
IDENTIFIED BY 'FinQuery@2026';

GRANT ALL PRIVILEGES ON finquery.* TO 'finquery_app'@'localhost';

FLUSH PRIVILEGES;

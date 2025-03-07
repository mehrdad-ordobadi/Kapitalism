import mysql.connector
import yaml

with open('app_config.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']

# Connect to MySQL
conn = mysql.connector.connect(
    host=hostname,
    user=user,
    password=password,
    database=db,
    port=port
)


cursor = conn.cursor()

cursor.execute('''
    DROP TABLE IF EXISTS review
''')

# Drop the 'product' and 'review' tables
cursor.execute('''
    DROP TABLE IF EXISTS product
''')

conn.commit()
conn.close()
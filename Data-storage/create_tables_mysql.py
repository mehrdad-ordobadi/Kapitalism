import mysql.connector
import yaml

with open('app_config.yml', 'r', encoding='utf-8') as f:
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

# Create Product table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS product (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(250) NOT NULL,
        model VARCHAR(250) NOT NULL,
        build_year INT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        category VARCHAR(250),
        stock_quantity INT NOT NULL,
        trace_id VARCHAR(36) NOT NULL,
        creation_date BIGINT NOT NULL
    ) ENGINE=InnoDB
''')

# Create Review table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS review (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_uuid VARCHAR(36) NOT NULL,
        product_id INT NOT NULL,
        rating INT NOT NULL,
        review_text TEXT NOT NULL,
        title VARCHAR(250) NOT NULL,
        submission_date VARCHAR(100) NOT NULL,
        creation_date BIGINT NOT NULL,
        trace_id VARCHAR(36) NOT NULL,
        FOREIGN KEY (product_id) REFERENCES product (id)
    ) ENGINE=InnoDB
''')

conn.commit()
conn.close()
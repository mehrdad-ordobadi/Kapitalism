import sqlite3

conn = sqlite3.connect('ecommerce.sqlite')

c = conn.cursor()

# Create Product table
c.execute('''
          CREATE TABLE product
          (id INTEGER PRIMARY KEY ASC,
           name VARCHAR(250) NOT NULL,
           model VARCHAR(250) NOT NULL,
           build_year INTEGER NOT NULL,
           price REAL NOT NULL,
           category VARCHAR(250),
           stock_quantity INTEGER NOT NULL,
           trace_id VARCHAR(36) NOT NULL)
          ''')
# Create Review table
c.execute('''
          CREATE TABLE review
          (id INTEGER PRIMARY KEY ASC,
           user_uuid VARCHAR(36) NOT NULL,
           product_id INTEGER NOT NULL,
           rating INTEGER NOT NULL,
           review_text TEXT NOT NULL,
           title VARCHAR(250) NOT NULL,
           submission_date VARCHAR(100) NOT NULL,
           creation_date VARCHAR(100) NOT NULL,
           trace_id VARCHAR(36) NOT NULL,
           FOREIGN KEY (product_id) REFERENCES product (id),
           FOREIGN KEY (user_uuid) REFERENCES user (uuid))
          ''')

conn.commit()
conn.close()
# Data Warehouse Modelling 

## Dimension Tables

- Star schema vs Snowflake Schema
- Star schema being putting all the dimensions (context) into one big table with only 1 primary key.
- Surrogate key is helpful when the table doesn't have natural primary key, where natural primary key is the primary key from application/source database.
- Snowflake schema will have the dimensions (context) split across tables, where there will be primary key and foreign key to present hierarchy. 

## Sources

- [[Udemy] Data Warehouse Fundamentals for Beginners](https://www.udemy.com/course/data-warehouse-fundamentals-for-beginners)


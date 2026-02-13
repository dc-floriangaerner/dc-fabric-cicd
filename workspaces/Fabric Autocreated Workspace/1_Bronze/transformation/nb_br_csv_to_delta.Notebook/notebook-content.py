# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "b892bcb4-b1d3-a9e0-4a9e-fac33bb0b654",
# META       "default_lakehouse_name": "lh_shortcuts",
# META       "default_lakehouse_workspace_id": "00000000-0000-0000-0000-000000000000",
# META       "known_lakehouses": [
# META         {
# META           "id": "b892bcb4-b1d3-a9e0-4a9e-fac33bb0b654"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Convert CSV Shortcut to Delta Table
# 
# This notebook reads data from the CSV shortcut in the lh_shortcuts lakehouse
# and converts it to a Delta table for optimized querying and analytics.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql.types import *

# CELL ********************

# Read CSV from shortcut
# The shortcut path: Files/Shortcuts/username_csv
df = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load("Files/Shortcuts/username_csv")

# CELL ********************

# Display the data
display(df)

# CELL ********************

# Show schema
df.printSchema()

# CELL ********************

# Write to Delta table
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("username_delta")

# CELL ********************

# Verify the Delta table was created
spark.sql("SELECT * FROM username_delta LIMIT 10").show()

# CELL ********************

# Get row count
count = spark.sql("SELECT COUNT(*) as total FROM username_delta").collect()[0]["total"]
print(f"Total rows in username_delta table: {count}")

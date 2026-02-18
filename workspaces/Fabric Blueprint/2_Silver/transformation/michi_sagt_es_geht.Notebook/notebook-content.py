# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "4f3864da-233e-496b-8bc9-b951acdd2b17",
# META       "default_lakehouse_name": "lakehouse_silver",
# META       "default_lakehouse_workspace_id": "46e75e85-b2f4-4b6a-9b98-b0f401bf8ff2",
# META       "known_lakehouses": [
# META         {
# META           "id": "6323ba06-e77d-4165-aac8-962913913992"
# META         },
# META         {
# META           "id": "4f3864da-233e-496b-8bc9-b951acdd2b17"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Welcome to your new notebook
# Type here in the cell editor to add code!


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.sql("SELECT * FROM lakehouse_bronze.dbo.titanic LIMIT 1000")
display(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Write a PySpark DataFrame 'df' as a Delta table to 'lakehouse_silver' with overwrite mode, table name 'titanic_silver'
df.write.format("delta") \
    .mode("overwrite") \
    .saveAsTable("dbo.titanic_silver")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

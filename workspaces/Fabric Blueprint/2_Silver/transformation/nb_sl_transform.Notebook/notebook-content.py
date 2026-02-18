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

variables = notebookutils.variableLibrary.getLibrary("Variables")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# --------------------------------------------------
# Build ABFSS path to TABLES (default target)
# --------------------------------------------------
def get_lakehouse_tables_path(workspace_guid, lakehouse_guid):
    workspace_id = workspace_guid
    lakehouse_id = lakehouse_guid

    return (
        f"abfss://{workspace_id}"
        f"@onelake.dfs.fabric.microsoft.com/"
        f"{lakehouse_id}/Tables"
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# --------------------------------------------------
# Create reusable references
# --------------------------------------------------
bronze_tables_path = get_lakehouse_tables_path(variables.workspace_guid, variables.lakehouse_bronze_guid)
silver_tables_path = get_lakehouse_tables_path(variables.workspace_guid, variables.lakehouse_silver_guid)

display(bronze_tables_path)
display(silver_tables_path)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df = spark.read.format("delta").load(bronze_tables_path + "/dbo/titanic")
display(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

target_table = "titanic_silver"
target_path  = f"{silver_tables_path}/dbo/{target_table}"

(df.write
  .format("delta")
  .mode("overwrite")
  .option("path", target_path)
  .saveAsTable(target_table)
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

from notion_client import Client
from dotenv import load_dotenv
import os

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

database_id = os.getenv("DEADLINES_DATABASE_ID")

# Get database info
database = notion.databases.retrieve(
    database_id=database_id
)

print("Database found!")
print("Title:")
print(database["title"][0]["plain_text"])

# Get data source ID
data_source_id = database["data_sources"][0]["id"]

print("\nData source ID:")
print(data_source_id)

# Retrieve data source info
data_source = notion.data_sources.retrieve(
    data_source_id=data_source_id
)

print("\nProperties:")
for prop_name in data_source["properties"]:
    print("-", prop_name)

from dotenv import load_dotenv
import os

load_dotenv()

print("Token:", os.getenv("NOTION_TOKEN"))
print("Database:", os.getenv("DEADLINES_DATABASE_ID"))

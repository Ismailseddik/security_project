import os
import json

# Set path to simulate the "user_management_module/userData.json" inside a project directory
project_dir = "/mnt/data/security_project"
user_management_dir = os.path.join(project_dir, "user_management_module")
os.makedirs(user_management_dir, exist_ok=True)

user_data_file_path = os.path.join(user_management_dir, "userData.json")

# Write empty initial data
with open(user_data_file_path, "w") as f:
    json.dump({}, f, indent=4)

user_data_file_path

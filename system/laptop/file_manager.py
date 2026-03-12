import os
import shutil
from datetime import datetime


# ---------------------------
# LIST FILES / FOLDERS
# ---------------------------

def list_files(path="."):
    """
    List files and folders in a directory
    """
    try:
        items = os.listdir(path)
        if not items:
            return f"📂 Folder '{path}' is empty"

        return "📂 Files & Folders:\n" + "\n".join(items)

    except FileNotFoundError:
        return f"❌ Path not found: {path}"
    except Exception as e:
        return f"❌ Error listing files: {e}"


# ---------------------------
# CREATE FOLDER
# ---------------------------

def create_folder(folder_name, path="."):
    """
    Create a new folder
    """
    try:
        full_path = os.path.join(path, folder_name)
        os.makedirs(full_path, exist_ok=True)
        return f"📁 Folder '{folder_name}' created"

    except Exception as e:
        return f"❌ Error creating folder: {e}"


# ---------------------------
# CREATE FILE
# ---------------------------

def create_file(file_name, path="."):
    """
    Create an empty file
    """
    try:
        full_path = os.path.join(path, file_name)
        with open(full_path, "w"):
            pass
        return f"📄 File '{file_name}' created"

    except Exception as e:
        return f"❌ Error creating file: {e}"


# ---------------------------
# DELETE FILE / FOLDER
# ---------------------------

def delete_item(name, path="."):
    """
    Delete a file or folder
    """
    try:
        full_path = os.path.join(path, name)

        if os.path.isfile(full_path):
            os.remove(full_path)
            return f"🗑 File '{name}' deleted"

        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
            return f"🗑 Folder '{name}' deleted"

        else:
            return f"⚠️ Item '{name}' not found"

    except Exception as e:
        return f"❌ Error deleting item: {e}"


# ---------------------------
# MOVE FILE
# ---------------------------

def move_file(file_name, destination, path="."):
    """
    Move a file to another directory
    """
    try:
        src = os.path.join(path, file_name)
        shutil.move(src, destination)
        return f"📦 '{file_name}' moved to '{destination}'"

    except FileNotFoundError:
        return f"❌ File not found: {file_name}"
    except Exception as e:
        return f"❌ Error moving file: {e}"


# ---------------------------
# COPY FILE
# ---------------------------

def copy_file(file_name, destination, path="."):
    """
    Copy a file to another directory
    """
    try:
        src = os.path.join(path, file_name)
        shutil.copy(src, destination)
        return f"📋 '{file_name}' copied to '{destination}'"

    except FileNotFoundError:
        return f"❌ File not found: {file_name}"
    except Exception as e:
        return f"❌ Error copying file: {e}"


# ---------------------------
# SEARCH FILE
# ---------------------------

def search_file(filename, path="."):
    """
    Search for a file in directory tree
    """
    try:
        matches = []
        for root, dirs, files in os.walk(path):
            if filename in files:
                matches.append(os.path.join(root, filename))

        if matches:
            return "🔍 Found Files:\n" + "\n".join(matches)
        else:
            return f"❌ File '{filename}' not found"

    except Exception as e:
        return f"❌ Error searching file: {e}"


# ---------------------------
# FILE INFORMATION
# ---------------------------

def file_info(file_name, path="."):
    """
    Get file details
    """
    try:
        full_path = os.path.join(path, file_name)

        if not os.path.exists(full_path):
            return f"❌ File '{file_name}' not found"

        size = os.path.getsize(full_path)
        created = datetime.fromtimestamp(os.path.getctime(full_path))
        modified = datetime.fromtimestamp(os.path.getmtime(full_path))

        return (
            f"📄 File Info:\n"
            f"Name: {file_name}\n"
            f"Size: {size} bytes\n"
            f"Created: {created}\n"
            f"Modified: {modified}"
        )

    except Exception as e:
        return f"❌ Error reading file info: {e}"

import contextlib
import os
from uuid import uuid4

from fastapi import UploadFile
from passlib.context import CryptContext

UPLOAD_FOLDER = "uploaded_images"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def save_image(image: UploadFile) -> str:
    """
    Saves the uploaded image to the server.

    Args:
        image (UploadFile): The uploaded image file.

    Returns:
        str: The file path where the image is saved.
    """
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    filename = f"{uuid4()}_{image.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, "wb") as buffer:
        buffer.write(image.file.read())
    return file_path


def delete_image(file_path: str):
    """
    Deletes the file at the given file path.

    Args:
        file_path (str): The path of the file to be deleted.

    Returns:
        None
    """
    with contextlib.suppress(FileNotFoundError):
        os.remove(file_path)


def hash_password(*, password: str) -> str:
    """
    Hashes the given password using the pwd_context.

    Args:
        password (str): The password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)

import os
from dotenv import load_dotenv
from imagekitio import ImageKit

load_dotenv()

# In the new ImageKit SDK, you ONLY pass the private_key
imagekit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY")
)

def upload_image(file_bytes, file_name):
    # The new method is .files.upload()
    upload_result = imagekit.files.upload(
        file=file_bytes,
        file_name=file_name
    )
    return {
        "url": upload_result.url,
        "file_id": upload_result.file_id
    }

def delete_image(file_id):
    # The new method is .files.delete()
    try:
        imagekit.files.delete(file_id)
    except Exception as e:
        print(f"Failed to delete from ImageKit: {e}")
from PIL import Image

img = Image.open(r"C:\Users\kalpe\Downloads\New folder\download (69).jpg")

# Ensure landscape
if img.height > img.width:
    img = img.rotate(90, expand=True)

img = img.resize((3840, 2160), Image.Resampling.LANCZOS)

img.save(
    r"D:\Jarvis\other\spiderman_4k.jpg",
    quality=100
)
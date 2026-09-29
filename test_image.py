from app.image_generator import generate_image

image_path = generate_image(
    "A cute fox standing in a magical forest at sunset, colorful comic book illustration",
    1
)

print("Image created:")
print(image_path)
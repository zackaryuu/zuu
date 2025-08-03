from PIL import Image   
import base64

def image_to_base64(image: str | Image.Image, include_markdown_header :bool = True, title : str = "image") -> str:
    """
    Converts an image to a base64 encoded string.

    Args:
        image (str | Image): The image to convert, can be a file path or a PIL Image object.
        include_markdown_header (bool): If True, includes the markdown header for images.

    Returns:
        str: The base64 encoded string of the image.
    """
    if isinstance(image, str):
        with open(image, "rb") as img_file:
            img_data = img_file.read()
    elif isinstance(image, Image.Image):
        from io import BytesIO
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
    else:
        raise TypeError("Image must be a file path or a PIL Image object.")

    base64_str = base64.b64encode(img_data).decode('utf-8')
    
    if include_markdown_header:
        return f"![{title}](data:image/png;base64,{base64_str})"

    return base64_str

def base64_to_image(base64_str: str, output_path: str = None) -> Image.Image|None:
    """
    Converts a base64 encoded string back to an image.

    Args:
        base64_str (str): The base64 encoded string of the image.
        output_path (str, optional): If provided, saves the image to this path.

    Returns:
        Image.Image: The PIL Image object created from the base64 string.
        None: If output_path is provided, returns None after saving the image.
    """
    img_data = base64.b64decode(base64_str)
    
    from io import BytesIO
    img_buffer = BytesIO(img_data)
    
    image = Image.open(img_buffer)
    
    if output_path:
        image.save(output_path)
    else:
        return image

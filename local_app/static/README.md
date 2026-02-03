# Static Assets

This folder contains static assets (images, icons, etc.) that are served by the Flask application.

## Structure

- `images/` - Image assets (icons, logos, etc.)

## Usage

Assets in this folder are accessible via the `/static` URL path.

For example:
- A file at `static/images/icon.png` is accessible at `http://localhost:8000/static/images/icon.png`

## Adding Assets

1. Place your image files in the appropriate subdirectory (e.g., `images/`)
2. Reference them in your code using the `/static` URL path
3. In markdown (Benchling Canvas), use: `![Alt text](/static/images/your-image.png)`
4. In Python code, construct URLs like: `f"/static/images/{filename}"`

## Note

Make sure your assets are properly accessible from the Benchling platform if you're displaying them in Canvas views.

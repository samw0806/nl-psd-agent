import json
from pathlib import Path

from PIL import Image, ImageDraw
from psd_tools import PSDImage


ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "eval" / "assets"
FIXTURES_DIR = ROOT / "eval" / "fixtures"


def ensure_dirs() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def make_rgba(size: tuple[int, int], color: tuple[int, int, int, int], text: str | None = None) -> Image.Image:
    image = Image.new("RGBA", size, color)
    if text:
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), text, fill=(255, 255, 255, 255))
    return image


def generate_assets() -> dict:
    logo = make_rgba((128, 128), (148, 55, 255, 255), "LOGO")
    logo_path = ASSETS_DIR / "logo_square.png"
    logo.save(logo_path)

    product = make_rgba((180, 260), (27, 121, 90, 255), "PRODUCT")
    product_path = ASSETS_DIR / "product_tall.png"
    product.save(product_path)

    photo = Image.new("RGB", (320, 180), (245, 232, 210))
    draw = ImageDraw.Draw(photo)
    draw.rectangle((20, 20, 300, 160), outline=(90, 65, 40), width=6)
    draw.text((32, 70), "WIDE PHOTO", fill=(90, 65, 40))
    photo_path = ASSETS_DIR / "photo_wide.jpg"
    photo.save(photo_path, "JPEG", quality=90)

    manifest = {
        "logo_square": str(logo_path.relative_to(ROOT)),
        "product_tall": str(product_path.relative_to(ROOT)),
        "photo_wide": str(photo_path.relative_to(ROOT)),
    }
    (ASSETS_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


def create_psd(path: Path, size: tuple[int, int], builders: list[tuple[str, tuple[int, int], tuple[int, int, int, int], int, int]]) -> None:
    psd = PSDImage.new(mode="RGB", size=size, depth=8)
    for name, layer_size, color, top, left in builders:
        image = make_rgba(layer_size, color, name)
        layer = psd.create_pixel_layer(image, name=name, top=top, left=left)
        psd.append(layer)
    psd.save(path)


def generate_simple_banner() -> None:
    psd = PSDImage.new(mode="RGB", size=(800, 400), depth=8)
    background = psd.create_pixel_layer(
        make_rgba((800, 400), (28, 35, 56, 255), "Background"),
        name="Background",
        top=0,
        left=0,
    )
    psd.append(background)

    header = psd.create_group(name="Header")
    psd.append(header)
    header.append(psd.create_pixel_layer(make_rgba((150, 60), (220, 120, 42, 255), "BrandBadge"), name="BrandBadge", top=24, left=32))
    header.append(psd.create_pixel_layer(make_rgba((180, 40), (55, 105, 255, 255), "HeroTitle"), name="HeroTitle", top=90, left=48))

    body = psd.create_group(name="Body")
    psd.append(body)
    body.append(psd.create_pixel_layer(make_rgba((180, 260), (27, 121, 90, 255), "ProductShot"), name="ProductShot", top=88, left=520))

    footer = psd.create_group(name="Footer")
    psd.append(footer)
    footer.append(psd.create_pixel_layer(make_rgba((220, 56), (173, 45, 76, 255), "CTA"), name="CTA", top=320, left=48))

    psd.save(FIXTURES_DIR / "simple_banner.psd")


def generate_nested_groups() -> None:
    psd = PSDImage.new(mode="RGB", size=(640, 360), depth=8)
    psd.append(psd.create_pixel_layer(make_rgba((640, 360), (18, 18, 18, 255), "Background"), name="Background", top=0, left=0))
    header = psd.create_group(name="Header")
    sub_header = psd.create_group(name="SubHeader")
    logo_group = psd.create_group(name="LogoGroup")
    logo_group.append(psd.create_pixel_layer(make_rgba((96, 96), (230, 230, 230, 255), "Logo"), name="Logo", top=16, left=16))
    sub_header.append(logo_group)
    header.append(sub_header)
    psd.append(header)
    psd.save(FIXTURES_DIR / "nested_groups.psd")


def generate_duplicate_names() -> None:
    psd = PSDImage.new(mode="RGB", size=(640, 360), depth=8)
    left = psd.create_group(name="Left")
    right = psd.create_group(name="Right")
    left.append(psd.create_pixel_layer(make_rgba((80, 80), (255, 99, 71, 255), "Icon"), name="Icon", top=40, left=40))
    right.append(psd.create_pixel_layer(make_rgba((80, 80), (65, 105, 225, 255), "Icon"), name="Icon", top=40, left=320))
    psd.append(left)
    psd.append(right)
    psd.save(FIXTURES_DIR / "duplicate_names.psd")


def generate_pixel_resample_only() -> None:
    psd = PSDImage.new(mode="RGB", size=(500, 500), depth=8)
    psd.append(psd.create_pixel_layer(make_rgba((500, 500), (245, 245, 245, 255), "Background"), name="Background", top=0, left=0))
    body = psd.create_group(name="Body")
    body.append(psd.create_pixel_layer(make_rgba((160, 240), (10, 128, 180, 255), "Product"), name="Product", top=120, left=170))
    psd.append(body)
    psd.save(FIXTURES_DIR / "pixel_resample_only.psd")


def generate_mutation_sandbox() -> None:
    psd = PSDImage.new(mode="RGB", size=(800, 400), depth=8)
    psd.append(psd.create_pixel_layer(make_rgba((800, 400), (249, 247, 241, 255), "Background"), name="Background", top=0, left=0))
    header = psd.create_group(name="Header")
    header.append(psd.create_pixel_layer(make_rgba((140, 56), (50, 50, 50, 255), "BrandBadge"), name="BrandBadge", top=24, left=32))
    header.append(psd.create_pixel_layer(make_rgba((100, 32), (60, 141, 255, 255), "PromoTag"), name="PromoTag", top=24, left=220))
    psd.append(header)
    body = psd.create_group(name="Body")
    body.append(psd.create_pixel_layer(make_rgba((220, 220), (74, 150, 97, 255), "Product"), name="Product", top=96, left=500))
    psd.append(body)
    psd.save(FIXTURES_DIR / "mutation_sandbox.psd")


def main() -> int:
    ensure_dirs()
    manifest = generate_assets()
    generate_simple_banner()
    generate_nested_groups()
    generate_duplicate_names()
    generate_pixel_resample_only()
    generate_mutation_sandbox()
    print(json.dumps({"assets": manifest, "fixtures_dir": str(FIXTURES_DIR.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

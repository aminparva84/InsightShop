"""Copy product seed images from Cursor assets to static/images.
First 6: product-1.png through product-6.png. Next 9: product-7.png through product-15.png.
Men's Basic T-shirt: basic-tshirt-men-yellow.png, basic-tshirt-men-grey.png, basic-tshirt-men-grey-back.png.
"""
import os
import shutil

_ASSETS_BASE = r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets\c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images"

# First 6 outfit images (product-1 to product-6)
ASSET_PATHS_1_6 = [
    os.path.join(_ASSETS_BASE, "1972297ad0d5886bebe5002c9d0ec284-c3d6680e-1a44-4155-8903-3129bca27fc9.png"),
    os.path.join(_ASSETS_BASE, "f81eb2f9c75641d47300ceae47328740-717a5de9-7403-4a1e-a05e-5517ca8b9252.png"),
    os.path.join(_ASSETS_BASE, "f01300ea9244a814bfafb374196de7bf-4e2c710d-380e-4d19-9211-8c46203f29a3.png"),
    os.path.join(_ASSETS_BASE, "db7adaf5fe0652472cc610249d8ea3ee-a3c7513c-fb56-401d-9357-86bcd8663b93.png"),
    os.path.join(_ASSETS_BASE, "597164376a26850c76a74ebb808a892e-b41778b3-d4e7-4d2c-bdde-c78e4e15d0d0.png"),
    os.path.join(_ASSETS_BASE, "24f68d705f8a3b26f4782d6cc05e26fe-7e3b8eb9-4a28-4b41-973a-5b7bcf7d9a0e.png"),
]

# 9 new outfit images (product-7 to product-15)
ASSET_PATHS_7_15 = [
    os.path.join(_ASSETS_BASE, "Good_Things-3711e290-cdec-4a76-8348-4de10fa670a6.png"),
    os.path.join(_ASSETS_BASE, "28bd0f05991592f1e04a90fb4d6f74ef-afffb4e4-2b45-44be-901e-ebd91a59443f.png"),
    os.path.join(_ASSETS_BASE, "045eb7209a83a4cac5c68493c54e15eb-86d0fd4e-8626-49ec-acb6-dabf9ca10584.png"),
    os.path.join(_ASSETS_BASE, "974b83ab166a3a4aed5a9ad2eb938ba7-838b9a51-aa82-4158-a66f-4bb47f11a53c.png"),
    os.path.join(_ASSETS_BASE, "55ed9944adf0fa8a0d7d9aacc94b47bf-a28db10b-6de2-4a3d-9092-0f018b6a2f84.png"),
    os.path.join(_ASSETS_BASE, "2823a3939afcc0c194124d73c7e42c39-67e4be5d-4543-420d-b97d-530dfe9caa2a.png"),
    os.path.join(_ASSETS_BASE, "068788fdeedba3732549098448746701-af3e4eb9-137d-4f0e-bf82-b6d4322622c9.png"),
    os.path.join(_ASSETS_BASE, "cdd265fed8930e61598830120b8df356-75b096ba-67c7-484e-97a7-3271ab458946.png"),
    os.path.join(_ASSETS_BASE, "a4989d005ab8644c2c01443a47297ec9-fa5f8825-a159-47c2-8dff-0501f9bc0ad5.png"),
]

# Men's Basic T-shirt (Yellow + Grey) — filenames used in seed_products.py
# Cursor stores these in assets/ with full long filename (no subfolder).
_ASSETS_DIR = r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets"
BASIC_TSHIRT_MEN_DEST_NAMES = [
    "basic-tshirt-men-yellow.png",
    "basic-tshirt-men-grey.png",
    "basic-tshirt-men-grey-back.png",
]
BASIC_TSHIRT_MEN_SOURCE_NAMES = [
    "c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_T_shirt_men_yellow-d2f77a74-1461-4375-9759-e33f1e6a7cd2.png",
    "c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_T_shirt_men_grey-ca6d7999-74bc-4fce-af01-64c64d8a1966.png",
    "c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_T_shirt_men_grey_back-41d01d5f-32a9-46fd-a1cb-ee8907f9fe59.png",
]
BASIC_TSHIRT_MEN = [
    (os.path.join(_ASSETS_DIR, BASIC_TSHIRT_MEN_SOURCE_NAMES[0]), BASIC_TSHIRT_MEN_DEST_NAMES[0]),
    (os.path.join(_ASSETS_DIR, BASIC_TSHIRT_MEN_SOURCE_NAMES[1]), BASIC_TSHIRT_MEN_DEST_NAMES[1]),
    (os.path.join(_ASSETS_DIR, BASIC_TSHIRT_MEN_SOURCE_NAMES[2]), BASIC_TSHIRT_MEN_DEST_NAMES[2]),
]

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest_dir = os.path.join(base, "static", "images")
    os.makedirs(dest_dir, exist_ok=True)
    copied = 0
    for i, src in enumerate(ASSET_PATHS_1_6, start=1):
        if not os.path.exists(src):
            print(f"Skip (not found): product-{i}.png")
            continue
        dest = os.path.join(dest_dir, f"product-{i}.png")
        shutil.copy2(src, dest)
        print(f"Copied product-{i}.png")
        copied += 1
    for i, src in enumerate(ASSET_PATHS_7_15, start=7):
        if not os.path.exists(src):
            print(f"Skip (not found): product-{i}.png")
            continue
        dest = os.path.join(dest_dir, f"product-{i}.png")
        shutil.copy2(src, dest)
        print(f"Copied product-{i}.png")
        copied += 1
    for src, dest_name in BASIC_TSHIRT_MEN:
        if not os.path.exists(src):
            # Fallback: look in workspace assets folder (e.g. assets/basic-tshirt-men-yellow.png)
            src = os.path.join(base, "assets", dest_name)
        if not os.path.exists(src):
            print(f"Skip (not found): {dest_name}")
            continue
        dest = os.path.join(dest_dir, dest_name)
        shutil.copy2(src, dest)
        print(f"Copied {dest_name}")
        copied += 1
    print(f"Done. Copied {copied} images to static/images.")

if __name__ == "__main__":
    main()

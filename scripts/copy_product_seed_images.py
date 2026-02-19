"""Copy the 6 product seed images from Cursor assets to static/images.
Run this from the project root, or ensure Cursor saved the images under the paths below.
Images will be copied as product-1.png through product-6.png.
"""
import os
import shutil

# Paths where Cursor saved the 6 outfit images (adjust if your paths differ)
ASSET_PATHS = [
    r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets\c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_a8cd24817ffeba66d127b9b47edad23d-b7da3054-3ba8-44db-907d-e4a4ea70ebcc.png",
    r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets\c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_55ed9944adf0fa8a0d7d9aacc94b47bf-8a026930-5e34-43a5-906b-6ee1eec82deb.png",
    r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets\c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_Good_Things-1591bcf2-0931-4eb6-b9b8-c77caca98ce9.png",
    r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets\c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_28bd0f05991592f1e04a90fb4d6f74ef-81cdea24-7754-47a0-8709-501704c1aae1.png",
    r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets\c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_2823a3939afcc0c194124d73c7e42c39-96d3394b-9f8b-4791-b569-0e9f8f0e99e1.png",
    r"C:\Users\Markazi\.cursor\projects\c-code-InsightShop\assets\c__Users_Markazi_AppData_Roaming_Cursor_User_workspaceStorage_b2a656acef54cfabc36259bc447173b3_images_068788fdeedba3732549098448746701-5e5701e6-2a8f-47f5-9c84-2c6a94cd2504.png",
]

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest_dir = os.path.join(base, "static", "images")
    os.makedirs(dest_dir, exist_ok=True)
    copied = 0
    for i, src in enumerate(ASSET_PATHS, start=1):
        if not os.path.exists(src):
            print(f"Skip (not found): {os.path.basename(src)[:50]}...")
            continue
        dest = os.path.join(dest_dir, f"product-{i}.png")
        shutil.copy2(src, dest)
        print(f"Copied product-{i}.png")
        copied += 1
    print(f"Done. Copied {copied}/6 images to static/images.")
    if copied < 6:
        print("Place the remaining images in static/images as product-1.png ... product-6.png if needed.")

if __name__ == "__main__":
    main()

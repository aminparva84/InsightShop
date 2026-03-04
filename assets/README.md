# Product seed images

Place the **Basic T-shirt for men** images here so they can be copied to `static/images`:

- `basic-tshirt-men-yellow.png` — yellow T-shirt (front)
- `basic-tshirt-men-grey.png` — grey T-shirt (front)
- `basic-tshirt-men-grey-back.png` — grey T-shirt (back)

Then run from the project root:

```bash
python -m scripts.copy_product_seed_images
```

If the images are already in Cursor’s asset storage at the path used in the script, the script will copy from there; otherwise it uses these files from `assets/`.

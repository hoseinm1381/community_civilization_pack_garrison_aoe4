"""Pillow-side statistics for a decoded trap atlas (runs under workspace Python)."""
import json
import sys

from PIL import Image


def pixels(path):
    with Image.open(path) as image:
        rgb = image.convert('RGB')
        rows = list(rgb.get_flattened_data())
        count = len(rows)
        means = [sum(pixel[i] for pixel in rows) / count for i in range(3)]
        return {'size': list(rgb.size), 'mean_rgb': means,
                'mean_luma': .2126 * means[0] + .7152 * means[1] + .0722 * means[2],
                'near_black_fraction': sum(max(pixel) < 35 for pixel in rows) / count}


if __name__ == '__main__':
    print(json.dumps(pixels(sys.argv[1])))

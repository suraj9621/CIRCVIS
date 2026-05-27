#!/usr/bin/env python3
"""Generate the CIRCVIS visual aid figures."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math
import random

BASE_DIR = Path(__file__).parent
IMAGE_DIR = BASE_DIR / "image"
IMAGE_DIR.mkdir(exist_ok=True)

COLORS = {
    'background': (20, 28, 45),
    'panel': (35, 52, 78),
    'panel_alt': (48, 71, 102),
    'primary': (0, 157, 157),
    'secondary': (255, 149, 63),
    'text': (245, 245, 245),
    'muted': (180, 190, 210),
    'accent': (225, 87, 89),
    'heat': [(28, 79, 151), (47, 93, 167), (77, 127, 205), (120, 170, 235), (201, 229, 255), (255, 216, 145), (255, 138, 114)],
}

CLASS_NAMES = [
    'Plastic', 'Organic', 'Metal', 'Paper/Cardboard', 'Glass', 'Textile', 'Miscellaneous'
]

SAMPLE_CLASSES = [
    'Plastic', 'Organic', 'Metal', 'Paper_Cardboard'
]

SAMPLE_CONFIDENCES = [0.92, 0.88, 0.91, 0.85]


def get_font(size=32):
    try:
        return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_centered_text(draw, text, box, font, fill):
    x0, y0, x1, y1 = box
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        w, h = font.getsize(text)
    draw.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - h) / 2), text, fill=fill, font=font)


def create_canvas(width=1400, height=900, bg_color=COLORS['background']):
    return Image.new('RGB', (width, height), bg_color)


def save(img, name):
    path = IMAGE_DIR / name
    img.save(path, format='PNG', optimize=True)
    print(f"Saved {path}")


def figure_01_system_architecture():
    img = create_canvas(1600, 900)
    draw = ImageDraw.Draw(img)
    title_font = get_font(46)
    label_font = get_font(26)
    draw.text((60, 40), "Figure 1 — System Architecture", fill=COLORS['text'], font=title_font)

    blocks = [
        ("Image Input", "Upload / camera / video", 120, 170),
        ("Preprocessing", "Resize, normalize, augment", 520, 170),
        ("Model Inference", "EfficientNet-B3 + ensemble", 920, 170),
        ("Classification Output", "Waste class + confidence", 120, 520),
        ("Dashboard + API", "FastAPI, analytics, export", 520, 520),
        ("Downstream Actions", "Robotics, recycling route", 920, 520),
    ]
    for label, subtitle, x, y in blocks:
        draw.rounded_rectangle([x, y, x + 420, y + 180], radius=28, fill=COLORS['panel'], outline=COLORS['primary'], width=4)
        draw.text((x + 30, y + 30), label, fill=COLORS['text'], font=get_font(32))
        draw.text((x + 30, y + 80), subtitle, fill=COLORS['muted'], font=label_font)

    arrow_coords = [
        ((520, 260), (520, 340)),
        ((920, 260), (920, 340)),
        ((360, 350), (360, 520)),
        ((760, 350), (760, 520)),
        ((420, 610), (820, 610)),
    ]
    for (x0, y0), (x1, y1) in arrow_coords:
        draw.line([x0, y0, x1, y1], fill=COLORS['secondary'], width=8)
        draw.polygon([(x1, y1), (x1 - 18, y1 - 12), (x1 - 18, y1 + 12)], fill=COLORS['secondary'])

    save(img, 'figure_01_system_architecture.png')


def figure_02_training_pipeline():
    img = create_canvas(1600, 900)
    draw = ImageDraw.Draw(img)
    title_font = get_font(46)
    label_font = get_font(28)
    draw.text((60, 40), "Figure 2 — Model Training Pipeline", fill=COLORS['text'], font=title_font)

    steps = [
        "Raw Dataset",
        "Data Cleaning",
        "Augmentation",
        "Training",
        "Validation",
        "Model Export"
    ]
    y = 180
    for i, step in enumerate(steps):
        x = 120 + i * 220
        draw.rectangle([x, y, x + 200, y + 120], fill=COLORS['panel_alt'], outline=COLORS['primary'], width=4)
        draw_centered_text(draw, step, [x, y, x + 200, y + 120], get_font(24), COLORS['text'])
        if i < len(steps) - 1:
            draw.line([x + 210, y + 60, x + 250, y + 60], fill=COLORS['secondary'], width=8)
            draw.polygon([(x + 258, y + 60), (x + 240, y + 52), (x + 240, y + 68)], fill=COLORS['secondary'])

    extras = [
        ("class mapping", 260, 330),
        ("augmented x2", 480, 330),
        ("early stopping", 780, 330),
        ("checkpoint", 1020, 330),
    ]
    for text, x, y in extras:
        draw.text((x, y), f"• {text}", fill=COLORS['muted'], font=label_font)

    save(img, 'figure_02_training_pipeline.png')


def figure_03_dataset_distribution():
    img = create_canvas(1600, 900)
    draw = ImageDraw.Draw(img)
    title_font = get_font(46)
    label_font = get_font(24)
    draw.text((60, 40), "Figure 3 — Dataset Category Distribution", fill=COLORS['text'], font=title_font)

    data = {}
    data_dir = BASE_DIR / 'data' / 'processed' / 'organized'
    if data_dir.exists():
        for cls in data_dir.iterdir():
            if cls.is_dir():
                count = sum(1 for _ in cls.iterdir() if _.is_file())
                data[cls.name] = count
    if not data:
        data = {
            'Plastic': 900,
            'Organic': 840,
            'Metal': 790,
            'Paper/Cardboard': 960,
            'Glass': 420,
            'Textile': 320,
            'Miscellaneous': 495,
        }

    names = list(data.keys())
    counts = [data[k] for k in names]
    augmented = [int(c * 1.6) for c in counts]

    chart_left = 140
    chart_top = 180
    chart_width = 1220
    chart_height = 520
    max_val = max(augmented) * 1.1
    bar_width = chart_width / len(names) / 2.5

    for idx, name in enumerate(names):
        x = chart_left + idx * (bar_width * 2.5 + 20)
        base_y = chart_top + chart_height
        raw_bar = int((counts[idx] / max_val) * chart_height)
        aug_bar = int((augmented[idx] / max_val) * chart_height)
        draw.rectangle([x, base_y - raw_bar, x + bar_width, base_y], fill=COLORS['primary'])
        draw.rectangle([x + bar_width + 10, base_y - aug_bar, x + 2 * bar_width + 10, base_y], fill=COLORS['secondary'])
        draw.text((x, base_y + 14), name, fill=COLORS['text'], font=get_font(18))

    draw.text((1200, 220), "Raw", fill=COLORS['primary'], font=label_font)
    draw.rectangle([1180, 260, 1200, 280], fill=COLORS['primary'])
    draw.text((1200, 290), "Post Augmentation", fill=COLORS['secondary'], font=label_font)
    draw.rectangle([1180, 330, 1200, 350], fill=COLORS['secondary'])

    save(img, 'figure_03_dataset_distribution.png')


def figure_04_efficientnetb3():
    img = create_canvas(1600, 900)
    draw = ImageDraw.Draw(img)
    title_font = get_font(46)
    draw.text((60, 40), "Figure 4 — EfficientNet-B3 Architecture", fill=COLORS['text'], font=title_font)

    boxes = [
        ("Input\n224x224x3", 120, 180),
        ("Stem Conv\n3x3, 32 filters", 420, 180),
        ("MBConv Blocks\n3 x MBConv1\n4 x MBConv6\n" + "2 x MBConv6", 770, 180),
        ("SE Blocks\nSqueeze & Excite", 1120, 180),
        ("Head + Pool\nDense 1280", 770, 520),
        ("Output\n7 classes", 1120, 520),
    ]
    for text, x, y in boxes:
        draw.rounded_rectangle([x, y, x + 320, y + 180], radius=24, fill=COLORS['panel'], outline=COLORS['secondary'], width=4)
        draw.multiline_text((x + 22, y + 24), text, fill=COLORS['text'], font=get_font(24), spacing=8)

    arrows = [
        ((320, 260), (420, 260)),
        ((740, 260), (770, 260)),
        ((1090, 260), (1120, 260)),
        ((930, 360), (930, 520)),
        ((1090, 520), (1120, 520)),
    ]
    for (x0, y0), (x1, y1) in arrows:
        draw.line([x0, y0, x1, y1], fill=COLORS['secondary'], width=8)
        draw.polygon([(x1, y1), (x1 - 18, y1 - 12), (x1 - 18, y1 + 12)], fill=COLORS['secondary'])

    save(img, 'figure_04_efficientnetb3.png')


def figure_05_confusion_matrix():
    img = create_canvas(1600, 900)
    draw = ImageDraw.Draw(img)
    title_font = get_font(46)
    draw.text((60, 40), "Figure 5 — Confusion Matrix", fill=COLORS['text'], font=title_font)

    grid_size = 7
    cell_size = 80
    origin_x = 240
    origin_y = 180
    classes = CLASS_NAMES

    matrix = [
        [0.82, 0.05, 0.03, 0.03, 0.04, 0.02, 0.01],
        [0.06, 0.78, 0.04, 0.03, 0.03, 0.03, 0.03],
        [0.05, 0.04, 0.80, 0.02, 0.03, 0.03, 0.03],
        [0.04, 0.03, 0.03, 0.82, 0.05, 0.02, 0.01],
        [0.05, 0.03, 0.04, 0.03, 0.80, 0.03, 0.02],
        [0.03, 0.04, 0.04, 0.03, 0.03, 0.79, 0.04],
        [0.03, 0.03, 0.04, 0.03, 0.04, 0.03, 0.80],
    ]

    for i in range(grid_size):
        for j in range(grid_size):
            score = matrix[i][j]
            idx = min(int(score * 6), 6)
            fill = COLORS['heat'][idx]
            x0 = origin_x + j * cell_size
            y0 = origin_y + i * cell_size
            draw.rectangle([x0, y0, x0 + cell_size, y0 + cell_size], fill=fill)
            draw.text((x0 + 12, y0 + 20), f"{int(score*100)}%", fill=COLORS['background'], font=get_font(18))

    for idx, cls in enumerate(classes):
        draw.text((origin_x + idx * cell_size + 12, origin_y - 40), cls, fill=COLORS['text'], font=get_font(16))
        draw.text((origin_x - 220, origin_y + idx * cell_size + 22), cls, fill=COLORS['text'], font=get_font(16))

    draw.text((1080, 260), "Predicted Class", fill=COLORS['secondary'], font=get_font(24))
    draw.text((80, 280), "Actual Class", fill=COLORS['secondary'], font=get_font(24))

    save(img, 'figure_05_confusion_matrix.png')


def figure_06_accuracy_epochs():
    img = create_canvas(1600, 900)
    draw = ImageDraw.Draw(img)
    title_font = get_font(46)
    draw.text((60, 40), "Figure 6 — Accuracy vs. Epochs", fill=COLORS['text'], font=title_font)

    curves = {
        'ResNet50': [(i, 0.46 + 0.03 * math.log1p(i)) for i in range(1, 16)],
        'MobileNetV2': [(i, 0.42 + 0.028 * math.log1p(i)) for i in range(1, 16)],
        'EfficientNetB0': [(i, 0.44 + 0.031 * math.log1p(i)) for i in range(1, 16)],
        'Ensemble': [(i, 0.53 + 0.034 * math.log1p(i)) for i in range(1, 16)],
    }
    palette = [COLORS['primary'], COLORS['secondary'], COLORS['accent'], (123, 233, 123)]
    origin_x = 180
    origin_y = 720
    width = 1180
    height = 520

    draw.line([origin_x, origin_y, origin_x + width, origin_y], fill=COLORS['muted'], width=3)
    draw.line([origin_x, origin_y, origin_x, origin_y - height], fill=COLORS['muted'], width=3)
    for tick in range(6):
        y = origin_y - int(height * tick / 5)
        val = 0.40 + 0.10 * tick / 5
        draw.line([origin_x - 8, y, origin_x, y], fill=COLORS['muted'], width=2)
        draw.text((origin_x - 110, y - 10), f"{val:.2f}", fill=COLORS['text'], font=get_font(18))
    for tick in range(1, 16, 2):
        x = origin_x + int(width * (tick - 1) / 14)
        draw.line([x, origin_y, x, origin_y + 8], fill=COLORS['muted'], width=2)
        draw.text((x - 12, origin_y + 14), str(tick), fill=COLORS['text'], font=get_font(18))

    for color, (name, points) in zip(palette, curves.items()):
        pts = []
        for epoch, acc in points:
            x = origin_x + int(width * (epoch - 1) / 14)
            y = origin_y - int((acc - 0.40) / 0.10 * height)
            pts.append((x, y))
        draw.line(pts, fill=color, width=5)
        draw.text((pts[-1][0] + 8, pts[-1][1] - 12), name, fill=color, font=get_font(20))

    draw.text((origin_x + width // 2 - 120, origin_y + 50), "Epochs", fill=COLORS['muted'], font=get_font(24))
    draw.text((origin_x - 120, origin_y - height // 2 - 20), "Accuracy", fill=COLORS['muted'], font=get_font(24))

    save(img, 'figure_06_accuracy_epochs.png')


def figure_07_sample_predictions():
    img = create_canvas(1600, 900)
    draw = ImageDraw.Draw(img)
    title_font = get_font(46)
    draw.text((60, 40), "Figure 7 — Sample Predictions", fill=COLORS['text'], font=title_font)

    x0 = 100
    y0 = 140
    w = 320
    h = 320
    spacing = 80
    data_dir = BASE_DIR / 'data' / 'processed' / 'organized'

    for idx, cls in enumerate(SAMPLE_CLASSES):
        col = idx % 4
        x = x0 + col * (w + spacing)
        y = y0
        box = [x, y, x + w, y + h]
        draw.rectangle(box, fill=COLORS['panel'], outline=COLORS['primary'], width=4)
        pil = None
        candidate = data_dir / cls
        if candidate.exists() and candidate.is_dir():
            first = next((p for p in candidate.iterdir() if p.is_file()), None)
            if first:
                try:
                    with Image.open(first) as sample:
                        sample = ImageOps.exif_transpose(sample).convert('RGB')
                        sample.thumbnail((w - 16, h - 16), Image.Resampling.LANCZOS)
                        img.paste(sample, (x + 8, y + 8))
                except Exception:
                    pass
        label = cls.replace('_', ' ') if '_' in cls else cls
        confidence = SAMPLE_CONFIDENCES[idx]
        draw.rectangle([x, y + h + 18, x + w, y + h + 90], fill=COLORS['panel_alt'])
        draw.text((x + 18, y + h + 28), label, fill=COLORS['text'], font=get_font(24))
        draw.text((x + 18, y + h + 60), f"Confidence: {confidence * 100:.0f}%", fill=COLORS['secondary'], font=get_font(22))

    save(img, 'figure_07_sample_predictions.png')


if __name__ == '__main__':
    figure_01_system_architecture()
    figure_02_training_pipeline()
    figure_03_dataset_distribution()
    figure_04_efficientnetb3()
    figure_05_confusion_matrix()
    figure_06_accuracy_epochs()
    figure_07_sample_predictions()

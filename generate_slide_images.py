#!/usr/bin/env python3
"""
Generate unique professional images for each slide
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import math

# Colors
PRIMARY_COLOR = (0, 102, 102)  # Teal
SECONDARY_COLOR = (0, 179, 179)  # Light Teal
ACCENT_COLOR = (255, 102, 0)  # Orange
DARK_BG = (30, 30, 30)  # Dark
TEXT_COLOR = (255, 255, 255)  # White
LIGHT_GRAY = (200, 200, 200)

BASE_DIR = Path(__file__).parent
IMAGE_DIR = BASE_DIR / "slide_images"
IMAGE_DIR.mkdir(exist_ok=True)

def create_image(width=1280, height=720, bg_color=DARK_BG):
    """Create a new image with background"""
    return Image.new('RGB', (width, height), bg_color)

def get_font(size=40, bold=False):
    """Get font - try system fonts"""
    try:
        return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size)
    except:
        return ImageFont.load_default()

def draw_title_bar(draw, y_pos, title, width=1280):
    """Draw a title bar"""
    draw.rectangle([(0, y_pos), (width, y_pos + 80)], fill=PRIMARY_COLOR)
    font = get_font(50)
    draw.text((40, y_pos + 15), title, fill=TEXT_COLOR, font=font)

def draw_circle(draw, center, radius, fill_color, outline_color=None):
    """Draw a circle"""
    x, y = center
    draw.ellipse([(x-radius, y-radius), (x+radius, y+radius)], 
                 fill=fill_color, outline=outline_color, width=2)

def draw_rectangle(draw, x, y, w, h, fill_color, outline_color=None):
    """Draw a rectangle"""
    draw.rectangle([(x, y), (x+w, y+h)], fill=fill_color, 
                   outline=outline_color, width=2)

def img_1_title():
    """Slide 1: Title - Logo/Branding"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    # Large central circle (waste bin)
    draw_circle(draw, (640, 360), 150, ACCENT_COLOR, SECONDARY_COLOR)
    
    # Text inside
    font_large = get_font(80)
    draw.text((490, 300), "CIRCVIS", fill=TEXT_COLOR, font=font_large)
    
    font_small = get_font(30)
    draw.text((350, 500), "Smart Waste Classification", fill=SECONDARY_COLOR, font=font_small)
    
    img = img.resize((640, 360), Image.Resampling.LANCZOS)
    img.save(IMAGE_DIR / "slide_01_title.png", "PNG", optimize=True)
    print("✅ Slide 1: Title image created")

def img_2_problem():
    """Slide 2: Problem - Urban Waste Visual"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "THE PROBLEM", 1280)
    
    # Draw waste bins
    bin_width, bin_height = 100, 150
    colors = [ACCENT_COLOR, (200, 50, 50), SECONDARY_COLOR]
    x_positions = [200, 640, 1050]
    
    for i, (x, color) in enumerate(zip(x_positions, colors)):
        draw_rectangle(draw, x - bin_width//2, 200, bin_width, bin_height, color)
        # Overflow indicators
        draw.line([(x - 40, 150), (x - 30, 100)], fill=ACCENT_COLOR, width=3)
        draw.line([(x, 150), (x, 80)], fill=ACCENT_COLOR, width=3)
        draw.line([(x + 40, 150), (x + 30, 100)], fill=ACCENT_COLOR, width=3)
    
    # Stats
    font = get_font(35)
    draw.text((150, 500), "2.12B TONS/YEAR", fill=ACCENT_COLOR, font=font)
    draw.text((550, 500), "Only 32% Recycled", fill=ACCENT_COLOR, font=font)
    draw.text((900, 500), "Landfill Crisis", fill=ACCENT_COLOR, font=font)
    
    img.save(IMAGE_DIR / "slide_02_problem.png")
    print("✅ Slide 2: Problem image created")

def img_3_solution():
    """Slide 3: Solution - AI/ML Visual"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "CIRCVIS SOLUTION", 1280)
    
    # Draw three models flowing to ensemble
    model_y = 200
    model_width = 120
    model_height = 100
    
    # Three input models
    models = ["ResNet50", "MobileNetV2", "EfficientNetB0"]
    x_positions = [200, 640, 1050]
    
    for x, model_name in zip(x_positions, models):
        draw_rectangle(draw, x - model_width//2, model_y, model_width, model_height, 
                      SECONDARY_COLOR, ACCENT_COLOR)
        font = get_font(16)
        draw.text((x - 55, model_y + 35), model_name[:8], fill=TEXT_COLOR, font=font)
        
        # Arrow down
        draw.line([(x, model_y + model_height), (x, model_y + 200)], 
                 fill=ACCENT_COLOR, width=3)
    
    # Ensemble box
    ensemble_y = 380
    draw_rectangle(draw, 450, ensemble_y, 380, 100, ACCENT_COLOR, SECONDARY_COLOR)
    font = get_font(40)
    draw.text((550, ensemble_y + 30), "89% ACCURACY", fill=TEXT_COLOR, font=font)
    
    # 7 waste classes
    classes = ["Plastic", "Organic", "Metal", "Paper", "Glass", "Textile", "Misc"]
    font_small = get_font(18)
    y_offset = 550
    for i, cls in enumerate(classes):
        x = 120 + (i * 155)
        draw.text((x, y_offset), cls, fill=SECONDARY_COLOR, font=font_small)
    
    img.save(IMAGE_DIR / "slide_03_solution.png")
    print("✅ Slide 3: Solution image created")

def img_4_architecture():
    """Slide 4: Architecture - System Layers"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "SYSTEM ARCHITECTURE", 1280)
    
    # Three layers
    layers = [
        ("FRONTEND", "HTML5/CSS3/JS", 150),
        ("BACKEND", "FastAPI", 350),
        ("ML LAYER", "TensorFlow/Keras", 550)
    ]
    
    for layer_name, tech, y in layers:
        draw_rectangle(draw, 200, y, 880, 120, PRIMARY_COLOR, SECONDARY_COLOR)
        
        font_title = get_font(40)
        font_tech = get_font(28)
        
        draw.text((250, y + 20), layer_name, fill=ACCENT_COLOR, font=font_title)
        draw.text((250, y + 65), tech, fill=TEXT_COLOR, font=font_tech)
    
    img.save(IMAGE_DIR / "slide_04_architecture.png")
    print("✅ Slide 4: Architecture image created")

def img_5_models():
    """Slide 5: Models - Three Model Types"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "DEEP LEARNING MODELS", 1280)
    
    models_info = [
        ("ResNet50", "High Accuracy", 200),
        ("MobileNetV2", "Edge Ready (45ms)", 640),
        ("EfficientNetB0", "Balanced", 1050)
    ]
    
    for model_name, desc, x in models_info:
        # Model box
        draw_rectangle(draw, x - 120, 200, 240, 300, SECONDARY_COLOR, ACCENT_COLOR)
        
        # Model icon (pyramid layers)
        for layer in range(5):
            height = 40 - layer * 8
            width = 180 - layer * 36
            y = 220 + layer * 45
            draw_rectangle(draw, x - width//2, y, width, 40, ACCENT_COLOR)
        
        # Labels
        font_model = get_font(28)
        font_desc = get_font(20)
        
        draw.text((x - 100, 530), model_name, fill=TEXT_COLOR, font=font_model)
        draw.text((x - 80, 570), desc, fill=SECONDARY_COLOR, font=font_desc)
    
    img.save(IMAGE_DIR / "slide_05_models.png")
    print("✅ Slide 5: Models image created")

def img_6_ensemble():
    """Slide 6: Ensemble - Voting Mechanism"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "ENSEMBLE VOTING", 1280)
    
    # Three voting boxes
    votes = ["Vote 1\n0.89", "Vote 2\n0.87", "Vote 3\n0.91"]
    x_positions = [250, 640, 1030]
    
    for i, (x, vote) in enumerate(zip(x_positions, votes)):
        draw_rectangle(draw, x - 80, 200, 160, 150, SECONDARY_COLOR, ACCENT_COLOR)
        font = get_font(24)
        draw.text((x - 60, 240), vote, fill=TEXT_COLOR, font=font)
        
        # Arrow down
        draw.line([(x, 350), (x, 420)], fill=ACCENT_COLOR, width=3)
    
    # Result box
    draw_rectangle(draw, 350, 450, 580, 150, ACCENT_COLOR, SECONDARY_COLOR)
    font_result = get_font(50)
    draw.text((450, 480), "FINAL: 0.89 (89%)", fill=TEXT_COLOR, font=font_result)
    
    # Confidence display
    font_small = get_font(20)
    draw.text((200, 650), "Weighted Average | Reduced Bias", fill=SECONDARY_COLOR, font=font_small)
    draw.text((550, 650), "Higher Accuracy", fill=SECONDARY_COLOR, font=font_small)
    
    img.save(IMAGE_DIR / "slide_06_ensemble.png")
    print("✅ Slide 6: Ensemble image created")

def img_7_datasets():
    """Slide 7: Datasets - Data Compilation"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "TRAINING DATASETS", 1280)
    
    # RealWaste dataset
    draw_rectangle(draw, 150, 200, 450, 250, PRIMARY_COLOR, SECONDARY_COLOR)
    font_title = get_font(32)
    font_content = get_font(20)
    draw.text((180, 230), "RealWaste", fill=ACCENT_COLOR, font=font_title)
    draw.text((180, 280), "• Real landfill images", fill=TEXT_COLOR, font=font_content)
    draw.text((180, 310), "• Mixed waste scenarios", fill=TEXT_COLOR, font=font_content)
    draw.text((180, 340), "• Variable lighting", fill=TEXT_COLOR, font=font_content)
    draw.text((180, 370), "• 7 waste classes", fill=TEXT_COLOR, font=font_content)
    
    # TACO dataset
    draw_rectangle(draw, 680, 200, 450, 250, PRIMARY_COLOR, SECONDARY_COLOR)
    draw.text((710, 230), "TACO Dataset", fill=ACCENT_COLOR, font=font_title)
    draw.text((710, 280), "• Urban environments", fill=TEXT_COLOR, font=font_content)
    draw.text((710, 310), "• Street-level waste", fill=TEXT_COLOR, font=font_content)
    draw.text((710, 340), "• Diverse categories", fill=TEXT_COLOR, font=font_content)
    draw.text((710, 370), "• Comprehensive", fill=TEXT_COLOR, font=font_content)
    
    # Arrow merge
    draw.line([(375, 500), (640, 500)], fill=ACCENT_COLOR, width=4)
    draw.line([(640, 500), (905, 500)], fill=ACCENT_COLOR, width=4)
    
    # Result
    draw_rectangle(draw, 350, 550, 580, 120, SECONDARY_COLOR, ACCENT_COLOR)
    draw.text((450, 580), "7 Organized Classes", fill=TEXT_COLOR, font=font_title)
    draw.text((420, 620), "70% Train | 15% Val | 15% Test", fill=TEXT_COLOR, font=font_content)
    
    img.save(IMAGE_DIR / "slide_07_datasets.png")
    print("✅ Slide 7: Datasets image created")

def img_8_performance():
    """Slide 8: Performance - Metrics"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "PERFORMANCE METRICS", 1280)
    
    # Overall accuracy - large circle
    draw_circle(draw, (320, 380), 100, ACCENT_COLOR, SECONDARY_COLOR)
    font_large = get_font(60)
    draw.text((260, 350), "89%", fill=TEXT_COLOR, font=font_large)
    font_small = get_font(20)
    draw.text((250, 480), "Overall Accuracy", fill=SECONDARY_COLOR, font=font_small)
    
    # Per-class bars
    classes_perf = [
        ("Plastic", 92),
        ("Organic", 87),
        ("Metal", 95),
        ("Paper", 88),
        ("Glass", 91),
        ("Textile", 82)
    ]
    
    x_start = 550
    y_start = 200
    bar_width = 100
    max_width = 150
    
    for i, (cls, perf) in enumerate(classes_perf):
        x = x_start + (i % 3) * 220
        y = y_start + (i // 3) * 250
        
        # Bar background
        draw_rectangle(draw, x, y, max_width, 40, (80, 80, 80))
        # Bar fill
        fill_width = int(max_width * (perf / 100))
        draw_rectangle(draw, x, y, fill_width, 40, ACCENT_COLOR)
        
        # Label
        font = get_font(18)
        draw.text((x + 10, y + 48), f"{cls}: {perf}%", fill=TEXT_COLOR, font=font)
    
    img.save(IMAGE_DIR / "slide_08_performance.png")
    print("✅ Slide 8: Performance image created")

def img_9_tools():
    """Slide 9: Tools & Technologies"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "TOOLS & TECHNOLOGIES", 1280)
    
    tools_categories = [
        ("Python", ["TensorFlow", "Keras"], 180),
        ("Backend", ["FastAPI", "Pydantic"], 550),
        ("ML/CV", ["OpenCV", "NumPy", "Pandas"], 920)
    ]
    
    font_cat = get_font(28)
    font_tool = get_font(20)
    
    for cat, tools, x in tools_categories:
        # Category box
        draw_rectangle(draw, x - 100, 150, 220, 80, PRIMARY_COLOR, SECONDARY_COLOR)
        draw.text((x - 80, 170), cat, fill=ACCENT_COLOR, font=font_cat)
        
        # Tools list
        for i, tool in enumerate(tools):
            tool_y = 300 + i * 80
            draw_rectangle(draw, x - 100, tool_y, 220, 70, SECONDARY_COLOR, ACCENT_COLOR)
            draw.text((x - 80, tool_y + 20), tool, fill=TEXT_COLOR, font=font_tool)
    
    img.save(IMAGE_DIR / "slide_09_tools.png")
    print("✅ Slide 9: Tools image created")

def img_10_deployment():
    """Slide 10: Deployment - Cloud & Edge"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "DEPLOYMENT OPTIONS", 1280)
    
    options = [
        ("☁️ CLOUD", "AWS | Azure | GCP", 250),
        ("🤖 EDGE", "IoT | Robotics | Smart Bins", 640),
        ("💻 LOCAL", "Single Machine | Development", 1030)
    ]
    
    font_title = get_font(32)
    font_desc = get_font(24)
    
    for title, desc, x in options:
        draw_rectangle(draw, x - 150, 200, 300, 350, SECONDARY_COLOR, ACCENT_COLOR)
        draw.text((x - 130, 230), title, fill=ACCENT_COLOR, font=font_title)
        draw.text((x - 140, 320), desc, fill=TEXT_COLOR, font=font_desc)
    
    # Docker at bottom
    draw_rectangle(draw, 300, 600, 680, 80, PRIMARY_COLOR, SECONDARY_COLOR)
    draw.text((350, 625), "🐳 Docker | Docker Compose", fill=ACCENT_COLOR, font=font_title)
    
    img.save(IMAGE_DIR / "slide_10_deployment.png")
    print("✅ Slide 10: Deployment image created")

def img_11_features():
    """Slide 11: Key Features"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "KEY FEATURES", 1280)
    
    features = [
        ("📱 Multi-Mode Demo", "Upload | Camera | Video", 200),
        ("📊 Dashboard", "Analytics | Charts | Metrics", 640),
        ("🌱 Sustainability", "CO₂ Tracking | Recyclables", 1050)
    ]
    
    font_feat = get_font(28)
    font_desc = get_font(22)
    
    for i, (feat, desc, x) in enumerate(features):
        # Feature circle
        draw_circle(draw, (x, 300), 80, ACCENT_COLOR, SECONDARY_COLOR)
        draw.text((x - 50, 290), str(i+1), fill=TEXT_COLOR, font=get_font(50))
        
        # Feature box
        draw_rectangle(draw, x - 130, 420, 260, 200, PRIMARY_COLOR, SECONDARY_COLOR)
        draw.text((x - 115, 450), feat, fill=ACCENT_COLOR, font=font_feat)
        draw.text((x - 125, 510), desc, fill=TEXT_COLOR, font=font_desc)
    
    img.save(IMAGE_DIR / "slide_11_features.png")
    print("✅ Slide 11: Features image created")

def img_12_impact():
    """Slide 12: Real-World Impact"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "REAL-WORLD IMPACT", 1280)
    
    impacts = [
        ("🏭 Smart Waste", "Automated Segregation", 200),
        ("♻️ Circular Economy", "Improved Recycling", 640),
        ("🌆 Smart Cities", "Municipal Tracking", 1050)
    ]
    
    font_imp = get_font(28)
    font_desc = get_font(22)
    
    for impact, result, x in impacts:
        draw_rectangle(draw, x - 140, 200, 280, 400, PRIMARY_COLOR, SECONDARY_COLOR)
        draw.text((x - 130, 230), impact, fill=ACCENT_COLOR, font=font_imp)
        draw.text((x - 120, 350), result, fill=TEXT_COLOR, font=font_desc)
        
        # Impact indicator
        draw_circle(draw, (x, 500), 40, ACCENT_COLOR)
    
    img.save(IMAGE_DIR / "slide_12_impact.png")
    print("✅ Slide 12: Impact image created")

def img_13_advantages():
    """Slide 13: Competitive Advantages"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "COMPETITIVE ADVANTAGES", 1280)
    
    # Four quadrants
    advantages = [
        ("Context-Aware", "Mixed Waste", 250, 250),
        ("Production Ready", "End-to-End", 750, 250),
        ("High Accuracy", "89% Real-World", 250, 550),
        ("Scalable", "Edge to Cloud", 750, 550)
    ]
    
    font_adv = get_font(28)
    font_desc = get_font(20)
    
    for adv, desc, x, y in advantages:
        draw_rectangle(draw, x - 100, y, 200, 150, PRIMARY_COLOR, SECONDARY_COLOR)
        draw.text((x - 90, y + 20), adv, fill=ACCENT_COLOR, font=font_adv)
        draw.text((x - 90, y + 70), desc, fill=TEXT_COLOR, font=font_desc)
    
    img.save(IMAGE_DIR / "slide_13_advantages.png")
    print("✅ Slide 13: Advantages image created")

def img_14_roadmap():
    """Slide 14: Future Roadmap"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "FUTURE ROADMAP", 1280)
    
    phases = [
        ("Phase 2", "Video Streaming", 250),
        ("Phase 3", "Scale & Integration", 640),
        ("Phase 4", "AI Enhancement", 1030)
    ]
    
    font_phase = get_font(28)
    font_desc = get_font(20)
    
    for i, (phase, desc, x) in enumerate(phases):
        # Timeline circle
        draw_circle(draw, (x, 250), 60, SECONDARY_COLOR, ACCENT_COLOR)
        draw.text((x - 25, 230), str(i+2), fill=TEXT_COLOR, font=get_font(50))
        
        # Phase box
        draw_rectangle(draw, x - 120, 350, 240, 200, PRIMARY_COLOR, SECONDARY_COLOR)
        draw.text((x - 110, 370), phase, fill=ACCENT_COLOR, font=font_phase)
        draw.text((x - 115, 430), desc, fill=TEXT_COLOR, font=font_desc)
    
    # Timeline connector
    draw.line([(190, 250), (1090, 250)], fill=SECONDARY_COLOR, width=2)
    
    img.save(IMAGE_DIR / "slide_14_roadmap.png")
    print("✅ Slide 14: Roadmap image created")

def img_15_implementation():
    """Slide 15: Technical Implementation"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "TECHNICAL IMPLEMENTATION", 1280)
    
    components = [
        ("Backend", "8000+ LOC", 150),
        ("Frontend", "5000+ LOC", 400),
        ("ML Pipeline", "Complete ETL", 650),
        ("DevOps", "Docker Ready", 900),
        ("Models", "3x Ensemble", 1150)
    ]
    
    font_comp = get_font(24)
    font_loc = get_font(18)
    
    for i, (comp, desc, x) in enumerate(components):
        draw_rectangle(draw, x - 60, 200, 120, 350, PRIMARY_COLOR, SECONDARY_COLOR)
        draw.text((x - 50, 230), comp, fill=ACCENT_COLOR, font=font_comp)
        draw.text((x - 55, 340), desc, fill=TEXT_COLOR, font=font_loc)
        
        # Checkmark
        draw.line([(x - 30, 420), (x - 10, 440)], fill=ACCENT_COLOR, width=3)
        draw.line([(x - 10, 440), (x + 30, 380)], fill=ACCENT_COLOR, width=3)
    
    img.save(IMAGE_DIR / "slide_15_implementation.png")
    print("✅ Slide 15: Implementation image created")

def img_16_conclusion():
    """Slide 16: Conclusion"""
    img = create_image()
    draw = ImageDraw.Draw(img)
    
    draw_title_bar(draw, 20, "CONCLUSION", 1280)
    
    # Main message
    font_main = get_font(40)
    draw.text((150, 200), "CIRCVIS Delivers Complete Solution", 
             fill=ACCENT_COLOR, font=font_main)
    
    # Three key points
    points = [
        ("✓ 89% Accuracy", "Real-world performance", 250),
        ("✓ Scalable Architecture", "Edge to cloud", 650),
        ("✓ Production Ready", "Deploy immediately", 1050)
    ]
    
    font_point = get_font(28)
    font_desc = get_font(20)
    
    for point, desc, x in points:
        draw_rectangle(draw, x - 130, 350, 260, 200, PRIMARY_COLOR, SECONDARY_COLOR)
        draw.text((x - 120, 370), point, fill=ACCENT_COLOR, font=font_point)
        draw.text((x - 120, 430), desc, fill=TEXT_COLOR, font=font_desc)
    
    # Call to action
    draw_rectangle(draw, 300, 620, 680, 80, ACCENT_COLOR, SECONDARY_COLOR)
    draw.text((350, 640), "Ready for Smart City Deployment", 
             fill=TEXT_COLOR, font=get_font(32))
    
    img.save(IMAGE_DIR / "slide_16_conclusion.png")
    print("✅ Slide 16: Conclusion image created")

def main():
    """Generate all images"""
    print("🎨 Generating unique slide images...")
    print("=" * 60)
    
    img_1_title()
    img_2_problem()
    img_3_solution()
    img_4_architecture()
    img_5_models()
    img_6_ensemble()
    img_7_datasets()
    img_8_performance()
    img_9_tools()
    img_10_deployment()
    img_11_features()
    img_12_impact()
    img_13_advantages()
    img_14_roadmap()
    img_15_implementation()
    img_16_conclusion()
    
    print("=" * 60)
    print(f"✨ All images created in: {IMAGE_DIR}")
    return str(IMAGE_DIR)

if __name__ == "__main__":
    main()

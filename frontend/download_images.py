import urllib.request
import urllib.parse
import os
import time

images = {
    # About remaining
    "abt_waste_1.png": "high end unreal engine 5 render of sleek robotic arm sorting plastic waste, dark industrial, neon green",
    "abt_waste_2.png": "high end unreal engine 5 render of glass and paper recycling conveyor, dark industrial, green lasers",
    "abt_deployment.png": "high end unreal engine 5 render of smart city IoT waste bin, dark cinematic, green glowing data",
    "abt_roadmap.png": "high end unreal engine 5 render of futuristic timeline glowing on dark glass, cybernetic",
    "abt_contact.png": "high end unreal engine 5 render of dark futuristic control room with communication interface",
    
    # Demo
    "demo_upload.png": "high end unreal engine 5 render of glowing digital file upload interface, dark mode, futuristic",
    "demo_analysis.png": "high end unreal engine 5 render of AI scanning a piece of waste, dark industrial, neon green laser",
    "demo_results.png": "high end unreal engine 5 render of futuristic data dashboard showing 99% accuracy, dark mode",
    "demo_mobilenet.png": "high end unreal engine 5 render of a small AI edge device processing data, dark cybernetic",
    "demo_realtime.png": "high end unreal engine 5 render of glowing data streams moving extremely fast, dark industrial",
    "demo_context.png": "high end unreal engine 5 render of AI bounding boxes over trash, hyperrealistic",
    "demo_analytics.png": "high end unreal engine 5 render of glowing charts and graphs floating in dark space",
    
    # Dashboard
    "dash_perf.png": "high end unreal engine 5 render of glowing green server performance metrics on dark glass",
    "dash_sust.png": "high end unreal engine 5 render of a glowing green tree made of data, dark background, futuristic",
    
    # Index Features
    "idx_ai.png": "high end unreal engine 5 render of artificial intelligence core, dark industrial, glowing green",
    "idx_ensemble.png": "high end unreal engine 5 render of three neural networks connecting, dark cybernetic",
    "idx_edge.png": "high end unreal engine 5 render of a futuristic factory with edge computing nodes, dark cinematic",
    "idx_realtime.png": "high end unreal engine 5 render of real-time data streaming over a dark city at night",
    "idx_multimodal.png": "high end unreal engine 5 render of thermal imaging and 3D point clouds of waste, dark industrial",
    "idx_sust.png": "high end unreal engine 5 render of glowing green recycling symbol holographic, dark tech",
    "idx_security.png": "high end unreal engine 5 render of an unbreakable futuristic digital lock, glowing green, dark mode",
    
    # Index Waste Categories
    "idx_plastic.png": "high end unreal engine 5 render of plastic bottles on a dark futuristic conveyor belt",
    "idx_organic.png": "high end unreal engine 5 render of organic food waste being processed by futuristic machine, dark mode",
    "idx_metal.png": "high end unreal engine 5 render of crushed metal cans under glowing green scanner, dark industrial",
    "idx_paper.png": "high end unreal engine 5 render of cardboard boxes in a high-tech dark facility",
    "idx_glass.png": "high end unreal engine 5 render of shattered glass being sorted by glowing lasers, dark cybernetic",
    "idx_textile.png": "high end unreal engine 5 render of old clothes on an automated sorting line, dark industrial"
}

output_dir = "assets/images"

for filename, prompt in images.items():
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        print(f"Skipping {filename}, already exists")
        continue
        
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true&seed=42"
    
    try:
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)
        time.sleep(0.5) 
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

print("Done!")

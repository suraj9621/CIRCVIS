CIRCVIS:
Context-Aware Waste Classification for Circular Cities

CIRCVIS is an AI-powered smart waste classification system developed to improve automated waste segregation for modern smart cities. The project uses Deep Learning and Computer Vision techniques to identify and classify waste materials such as Plastic, Organic, Metal, Glass, Cardboard, and Mixed Trash.

The primary goal of CIRCVIS is to support sustainable waste management and circular economy initiatives by enabling intelligent waste sorting in real-world urban environments.

Unlike traditional waste classification systems that work only in controlled laboratory conditions, CIRCVIS is designed to handle:

Variable lighting conditions
Mixed waste streams
Partial object visibility
Physically degraded waste materials
Real-world urban waste environments

The system integrates multiple deep learning architectures including Custom CNN, ResNet-50, MobileNetV2, and EfficientNet-B3 for comparative evaluation and deployment optimisation.

🚀 Key Features
Context-Aware Waste Classification
Multi-Architecture Deep Learning Pipeline
Real-Time Waste Categorisation
Smart Data Augmentation
Confidence Score Prediction
GPU Accelerated Model Training
Cloud and Edge Deployment Support
Sustainability Impact Analysis
🧠 Deep Learning Models Used
Architecture	Purpose
Custom CNN	Lightweight baseline model
ResNet-50	High-accuracy residual learning
MobileNetV2	Edge and IoT deployment
EfficientNet-B3	Best accuracy-efficiency tradeoff
📂 Dataset Information

The project uses a combined dataset created from:

TrashNet Dataset
Kaggle Waste Classification Dataset
Waste Categories
Plastic
Organic
Metal
Glass
Cardboard
Mixed Trash
Dataset Size

Approximately 25,000 processed images after cleaning and augmentation.

🔍 Data Preprocessing

The preprocessing pipeline includes:

Image Resizing (224×224)
Pixel Normalisation
Data Augmentation
Label Encoding
Stratified Dataset Splitting
Augmentation Techniques
Random Rotation
Horizontal and Vertical Flip
Brightness Adjustment
Contrast Variation
Zoom and Crop
Noise Injection
🧪 Technologies Used
Python
TensorFlow / Keras
OpenCV
NumPy
Pandas
Matplotlib
Seaborn
Google Colab
Git & GitHub
⚙️ Hardware Requirements
Component	Specification
CPU	Minimum 4-Core Processor
RAM	Minimum 8 GB
GPU	NVIDIA GPU with CUDA Support
Storage	Minimum 20 GB Free Space
📈 Model Performance
Model	Accuracy
Custom CNN	83.4%
ResNet-50	91.2%
MobileNetV2	88.7%
EfficientNet-B3	93.6%

EfficientNet-B3 achieved the best overall performance and was selected as the primary deployment model.

📊 Evaluation Metrics

The following metrics were used for model evaluation:

Accuracy
Precision
Recall
F1-Score
Confusion Matrix
🏗️ System Workflow
Waste image is captured
Image preprocessing is applied
Deep learning model extracts visual features
Waste category is predicted
Prediction confidence is generated
Classification results are mapped to recycling insights
⚡ Installation
Clone Repository

git clone https://github.com/your-username/CIRCVIS.git

Move to Project Directory

cd CIRCVIS

Install Dependencies

pip install -r requirements.txt

▶️ Run Project
Run Python Application

python app.py

Run Jupyter Notebook

jupyter notebook

🔮 Future Enhancements
Mobile Application Integration
IoT Smart Bin Deployment
Cloud-Based API Services
Drone Waste Monitoring
Real-Time Sustainability Dashboard
Advanced Waste Detection Models

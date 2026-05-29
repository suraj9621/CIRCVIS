# ♻️ CIRCVIS - Context-Aware Waste Classification

CIRCVIS is an AI-powered waste classification system designed to identify and categorize waste materials using deep learning and computer vision. The project aims to support smart waste management, recycling awareness, and sustainable environmental practices through automated image-based classification.

---

## 🚀 Features

* 🧠 AI-powered waste classification
* 📷 Image upload and prediction system
* 📊 Interactive dashboard interface
* ⚡ FastAPI backend integration
* 🎨 Responsive frontend design
* 📂 Automated dataset organization
* 📈 Prediction logging and analytics
* 🐳 Docker support for deployment

---

## 🛠️ Technologies Used

### Backend

* Python
* FastAPI
* TensorFlow / Keras
* Pydantic

### Frontend

* HTML5
* CSS3
* JavaScript

### Tools & Utilities

* Docker
* Git & GitHub
* SQLite
* Batch Scripts

---

## 📁 Project Structure

```bash
CIRCVIS/
│
├── backend/                 # Backend API and model services
├── frontend/                # Frontend webpages and assets
├── data/                    # Dataset and prediction logs
├── models/                  # Trained AI models
├── image/                   # Images and visual assets
├── venv/                    # Virtual environment
│
├── run.bat                  # Run project script
├── start.bat                # Startup automation
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Multi-container setup
│
└── README.md                # Project documentation
```

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/suraj9621/CIRCVIS.git
cd CIRCVIS
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

---

### 3️⃣ Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

---

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project

### Using Batch File

```bash
run.bat
```

or

```bash
start.bat
```

---

## 🌐 Access Application

After the server starts successfully:

```bash
API Base:   http://localhost:8001
Landing:    http://localhost:8001/
Dashboard:  http://localhost:8001/dashboard.html
Demo:       http://localhost:8001/demo.html
```

---

## 🧠 How It Works

1. User uploads a waste image
2. Backend processes the image
3. AI model predicts waste category
4. Result is displayed on dashboard

---

## 📊 Supported Waste Categories

* Paper/Cardboard
* Plastic
* Metal
* Glass
* Organic Waste
* Other Recyclables

---

## 🐳 Docker Support

### Build Docker Image

```bash
docker build -t circvis .
```

### Run Container

```bash
docker run -p 8001:8001 circvis
```

---

## 📌 Future Improvements

* Mobile application support
* Real-time camera detection
* Cloud deployment
* Advanced analytics dashboard
* Multi-language support

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

## 📜 License

This project is developed for educational and research purposes.

---

## 👨‍💻 Author

**Suraj Kumar**

* GitHub: https://github.com/suraj9621

---

## ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

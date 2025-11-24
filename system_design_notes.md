# Google Photos System Design & Interview Notes

## 1. System Architecture: Google Photos Clone

### **Agenda**
- Upload pictures
- Generate captions
- Store pictures
- Organize
- Search
- Generating tags

### **Phase 1: Upload Handling**
- **Client**: Mobile or Web App.
- **Entry Point**: **API Gateway** (Front door).
- **Processing**: **AWS Lambda** (Upload Handler).
    - Validates image.
    - Downgrading/Resizing.
    - Storage in **S3**.
    - Sends processing task to **SQS Queue**.

### **Phase 2: Storage (S3 Bucket)**
- **Photos-Original**: Raw version.
- **Photo-Thumbnails**: Smaller versions.
- **Lifecycle Management**: Move older data (e.g., 2012 photos) to **Glacier** for cheaper storage.

### **Phase 3: Real-time Processing**
- **Queue**: **SQS** holds pending image processing tasks.
- **Compute**: **Lambda** triggers on queue messages.
- **Vision Service**: **AWS Rekognition** (Heavy CV lifting).
    - **Object Detection**: "iPad", "Widget", "Dog", "Beach".
    - **Face Recognition**: Bounding boxes, identity.
    - **Text Extraction (OCR)**: Street signs, documents.
- **Output**: JSON Response (photo_id, objects, faces, text, timestamp).

### **Phase 4: Metadata Management**
- **Database**: **NoSQL (DynamoDB)**.
- **Data**: Stores metadata, tags, and analysis results.
- **Caching**: **DynamoDB Accelerator (DAX)** for frequent face vectors/storage.

### **Phase 5: Batch Processing**
- **Service**: **AWS Glue**.
    - Grouping of photos & videos.
    - Generating "Best Photo" scores.
    - Geotagging.
- **Custom Models**: **Amazon SageMaker**.
    - Host custom models.
    - Personalized pet recognition.
    - Domain-specific learning.

### **Phase 6: Searching**
- **Service**: **OpenSearch**.
    - Indexes metadata for fast querying.
    - **Text Search**: "dog", "beach", "2025".
    - **Vector Search**: Embeddings for semantic search.

### **Phase 7: Security & Privacy**
- **Authentication**: **AWS Cognito** (Managing user permissions).
- **Encryption**: Privacy handling.

---

## 2. Feature Mapping Table

| Feature | AWS Service | Data Scientist Task |
| :--- | :--- | :--- |
| **Object Detection** | Rekognition | Train a CNN (Transfer Learning) |
| **Face Analysis** | Rekognition | Face embeddings -> K-means clustering |
| **Text Extraction** | Rekognition/Textract | OCR Pipeline |
| **Personalization** | SageMaker | Fine-tune model on private data |

---

## 3. "Prompt to Generate the App"
**Goal**: End-to-end implementation of Google Photos: Image Recognition and Organization.
**Domain**: Computer Vision, Data Management.

**Key Design Principles:**
1.  **Massive-Scale Ingestion**: Scalable, fault-tolerant pipeline for billions of uploads.
2.  **Advanced CV Models**:
    *   Object Recognition (dog, sunset).
    *   Facial Recognition & Grouping (clustering).
    *   Landmark Recognition.
    *   OCR.
    *   Semantic Segmentation.
3.  **Real-time & Batch Processing**: Immediate basic features vs. deep semantic understanding over time.
4.  **Distributed Computing**: MapReduce, BigQuery, TensorFlow.
5.  **Personalization & Privacy**: Local processing for sensitive features.
6.  **Scalable Storage**: Distributed file systems.

---

## 4. Homework Projects
1.  `https://aistockanalyser.com/howto`
2.  `https://github.com/ngxson/smolvlm-realtime-webcam`

---

## 5. FAANG Exercise Questions

1.  **Story Difficulty Estimation (Duolingo)**: Design a system to assess language-learning story difficulty (linguistic metrics).
2.  **Editable Story Complexity (Duolingo)**: Automatically modify story complexity (vocabulary, sentence length).
3.  **Fraud Detection (FinTech)**: ML model for fraudulent credit card transactions.
4.  **Out-of-Stock Recommendation (E-commerce)**: Suggest replacements for unavailable items.
5.  **New User Follow Suggestions (Twitter)**: Recommend accounts for cold-start users.
6.  **Answer Ranking on Quora**: Rank most helpful answers.
7.  **Trending Hashtag Detection (Twitter)**: Real-time detection.
8.  **Query-Based Image Retrieval (Google Images)**: Relevant images from text query.
9.  **Search Autocomplete**: Suggest completions for partial queries.
10. **Rental Listing Search (Airbnb)**: Return top 10 relevant listings for a location.

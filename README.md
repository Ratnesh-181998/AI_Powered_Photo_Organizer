# AI-Powered Photo Organizer

A comprehensive System Design and Prototype for a scalable, AI-driven photo organization platform similar to Google Photos.

## 📂 Project Structure

- **`AI_Powered_Photo_Organizer_Design.md`**: The complete Machine Learning System Design document. Includes architecture diagrams (Mermaid.js), component breakdown (Lambda, Rekognition, OpenSearch), and data flow strategies.
- **`photo_organizer_prototype.py`**: A fully functional local prototype script. It simulates the cloud architecture (S3, DynamoDB, Rekognition) to demonstrate the ingestion, processing, and search workflows locally.
- **`system_design_notes.md`**: Raw notes and feature mapping tables derived from system design brainstorming sessions.

## 🚀 How to Run the Prototype

The prototype allows you to simulate the "Upload -> Process -> Search" loop on your local machine without needing an AWS account.

### Prerequisites
- Python 3.x

### Steps
1.  Place some `.png` images in the project directory (or use the dummy one created by the script).
2.  Run the script:
    ```bash
    python photo_organizer_prototype.py
    ```
3.  **What happens?**
    - The script creates a local `mock_s3_bucket` folder.
    - It "uploads" images and simulates AI object detection (e.g., detecting "Error", "Search", "Person").
    - It indexes metadata in a local `mock_dynamodb.json` file.
    - It performs sample search queries (e.g., searching for "error") and displays results.

## 🏗 System Architecture Overview

The system is designed to handle massive scale using AWS Serverless components:

-   **Ingestion**: API Gateway + Lambda + S3.
-   **Processing**: AWS Rekognition (Object/Face Detection) + SQS for buffering.
-   **Storage**: DynamoDB (Hot Metadata) + S3 Glacier (Archival).
-   **Search**: Amazon OpenSearch Service for sub-second text and vector queries.
-   **ML Ops**: Amazon SageMaker for retraining custom models based on user feedback.

## 📝 License
This project is for educational and system design demonstration purposes.

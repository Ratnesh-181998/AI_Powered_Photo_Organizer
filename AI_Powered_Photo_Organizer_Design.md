# AI-Powered Photo Organizer: ML System Design

## 1. Overview
This document outlines the end-to-end Machine Learning System Design for an AI-Powered Photo Organizer, similar to Google Photos. The system is designed to handle massive scale image ingestion, perform advanced computer vision tasks (object detection, face recognition), and provide sub-second search capabilities using natural language queries.

## 2. System Architecture

### High-Level Architecture Diagram

```mermaid
graph TD
    User[User (Mobile/Web)] -->|Upload Image| API[API Gateway]
    API -->|Trigger| UploadLambda[Lambda: Upload Handler]
    
    subgraph "Ingestion & Storage"
        UploadLambda -->|Validate & Resize| S3Originals[(S3: Originals)]
        UploadLambda -->|Save Thumbnail| S3Thumbnails[(S3: Thumbnails)]
        UploadLambda -->|Metadata| DDB[(DynamoDB: Metadata)]
        UploadLambda -->|Push Task| SQS[SQS: Processing Queue]
    end
    
    subgraph "Real-time Processing"
        SQS -->|Trigger| ProcessLambda[Lambda: Image Processor]
        ProcessLambda -->|Call| Rekognition[AWS Rekognition]
        Rekognition -->|Labels/Faces/Text| ProcessLambda
        ProcessLambda -->|Update| DDB
        ProcessLambda -->|Index| OpenSearch[OpenSearch Service]
    end
    
    subgraph "Batch Processing & ML"
        S3Originals -->|Batch Job| Glue[AWS Glue]
        Glue -->|Clustering/Geotagging| DDB
        Glue -->|Training Data| S3Train[(S3: Training Data)]
        S3Train -->|Train| SageMaker[Amazon SageMaker]
        SageMaker -->|Deploy Model| SageEndpoint[SageMaker Endpoint]
        User -->|Feedback| API
        API -->|Log Feedback| DDB
    end
    
    subgraph "Search & Retrieval"
        User -->|Search Query| API
        API -->|Query| OpenSearch
        OpenSearch -->|Results| API
        API -->|Get Image URL| S3Thumbnails
    end
    
    subgraph "Security"
        User -.->|Auth| Cognito[AWS Cognito]
    end
```

---

## 3. Detailed Component Design

### 3.1. Image Upload & Handling (Ingestion)
*   **Entry Point**: AWS API Gateway acts as the "front door", handling secure REST API calls from mobile and web clients.
*   **Compute**: AWS Lambda (`UploadHandler`) is triggered on upload.
*   **Responsibilities**:
    *   **Validation**: Ensure file type (JPG, PNG) and size limits.
    *   **Preprocessing**: Generate a low-res thumbnail immediately to save bandwidth for viewing.
    *   **Storage**:
        *   High-res original -> `S3 Bucket (Raw)`
        *   Thumbnail -> `S3 Bucket (Processed)`
    *   **Queueing**: Push a message to AWS SQS with `photo_id` and `s3_key` to decouple upload from heavy processing.

### 3.2. Real-time Processing (Computer Vision)
*   **Trigger**: AWS Lambda (`ProcessHandler`) consumes messages from SQS.
*   **Core Vision Service**: **AWS Rekognition**.
    *   **Object Detection**: Identifies "Dog", "Beach", "Car".
    *   **Face Recognition**: Detects faces and returns bounding boxes + 128d face embeddings.
    *   **OCR**: Extracts text from street signs or documents.
*   **Data Persistence**:
    *   Store raw JSON response (labels, confidence scores) in **DynamoDB**.
    *   Schema: `PartitionKey: UserID`, `SortKey: PhotoID`.

### 3.3. Metadata & Search (Indexing)
*   **Database**: **DynamoDB** stores the "source of truth" metadata.
*   **Search Engine**: **Amazon OpenSearch Service** (formerly ES).
    *   **Indexing**: The `ProcessHandler` Lambda formats the Rekognition output and indexes it into OpenSearch.
    *   **Querying**: Supports full-text search ("dog on beach") and filtering (Date: 2023, Location: Paris).
    *   **Performance**: Optimized for <100ms response times.

### 3.4. Batch Processing & Advanced ML
*   **Service**: **AWS Glue** (Serverless ETL).
*   **Tasks**:
    *   **Face Clustering**: Run DBSCAN or K-Means on face embeddings to group "Person A" across thousands of photos.
    *   **Geotagging**: Group photos by GPS coordinates to create "Trips" or "Events".
    *   **Curated Albums**: "Best of 2024" generation based on image quality scores.
*   **Lifecycle**: Move old photos (e.g., >5 years) to **S3 Glacier** for cost savings.

### 3.5. Model Retraining & Personalization (Feedback Loop)
*   **Problem**: Generic models might misidentify a specific pet or family member.
*   **Solution**: **Amazon SageMaker**.
*   **Workflow**:
    1.  User corrects a tag (e.g., "This is not a cat, it's a dog").
    2.  Feedback is logged to DynamoDB.
    3.  Scheduled SageMaker jobs retrain a custom classifier (Transfer Learning) on user-specific data.
    4.  Updated model is deployed to a SageMaker Endpoint for inference on new uploads.

---

## 4. Data Flow & API Contracts

### 4.1. Upload API
**POST** `/photos/upload`
```json
{
  "user_id": "user_123",
  "filename": "beach_trip.jpg",
  "image_data": "base64_encoded_string..."
}
```

### 4.2. Search API
**GET** `/photos/search?q=dog+beach&year=2023`
*   **Backend Logic**:
    1.  Convert query "dog beach" to OpenSearch DSL.
    2.  Retrieve `photo_ids` from OpenSearch.
    3.  Fetch signed URLs for thumbnails from S3.
    4.  Return list to client.

---

## 5. Security & Privacy
*   **Authentication**: **AWS Cognito** handles user sign-up, sign-in, and JWT token generation.
*   **Authorization**: IAM Policies ensure a user can ONLY access their own S3 objects and DynamoDB records.
*   **Encryption**:
    *   **At Rest**: S3 Server-Side Encryption (SSE-S3) and DynamoDB encryption.
    *   **In Transit**: TLS 1.2+ for all API calls.

## 6. Scalability Considerations
*   **S3**: Virtually infinite storage.
*   **Lambda**: Auto-scales to thousands of concurrent executions to handle upload spikes (e.g., after holidays).
*   **DynamoDB**: On-demand capacity mode to handle unpredictable read/write traffic.
*   **SQS**: Buffers requests so the downstream processing doesn't crash under load.

---

## 7. Implementation Snippet (Python/Boto3)

### Lambda: Image Processor (Simplified)

```python
import boto3
import json
import os

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
opensearch = boto3.client('opensearch')

TABLE_NAME = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    for record in event['Records']:
        # 1. Get info from SQS message
        payload = json.loads(record['body'])
        bucket = payload['bucket']
        key = payload['key']
        user_id = payload['user_id']
        
        # 2. Call Rekognition
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=10,
            MinConfidence=75
        )
        
        labels = [label['Name'] for label in response['Labels']]
        
        # 3. Save to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'user_id': user_id,
                'photo_id': key,
                'labels': labels,
                'timestamp': payload['timestamp']
            }
        )
        
        # 4. Index to OpenSearch (Pseudocode)
        # opensearch.index(index="photos", body={...})
        
        print(f"Processed {key}: Found {labels}")
```

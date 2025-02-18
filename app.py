import os
import json
import logging
import uuid
import asyncio
import threading

from flask import (Flask, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)

from src.models import ResponseStatus, ApiResponse
from src.storage import TempStorageClient
from src.utils import is_valid_uuid
from src.processingmode import ProcessingMode
from src.document_processor import DocumentProcessor

app = Flask(__name__)


@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


# API

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Initialize storage client and document processor
storage_client = TempStorageClient()
document_processor = DocumentProcessor(storage_client)



@app.route('/ping', methods=['POST'])
def ping():
    return ApiResponse(status=ResponseStatus.SUCCESS, message="Pong")

@app.route('/ProcessDocument', methods=['POST'])
def process_document():
    try:
        if 'file' not in request.files:
            logger.error("No file part in the request")
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="No file uploaded",
                error="No file part in the request"
            )
            return jsonify(response.to_dict()), 400

        file = request.files['file']
        if file.filename == '':
            logger.error("No file selected")
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="No file selected",
                error="Please select a file to upload"
            )
            return jsonify(response.to_dict()), 400

        # Check file size before reading content
        content_length = request.headers.get('content-length')
        if content_length:
            file_size = int(content_length)
            if file_size > MAX_FILE_SIZE:
                logger.error("File size too large. Max file size is 10MB.")
                response = ApiResponse(
                    status=ResponseStatus.ERROR,
                    message="File size too large",
                    error="Max file size is 10MB"
                )
                return jsonify(response.to_dict()), 400

        file_content = file.read()
        mode = ProcessingMode(request.args.get('mode', 'fast'))

        # Double-check actual content size after reading
        if len(file_content) > MAX_FILE_SIZE:
            logger.error("File size too large. Max file size is 10MB.")
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="File size too large",
                error="Max file size is 10MB"
            )
            return jsonify(response.to_dict()), 400

        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())

        # Save the file to temporary storage
        file_name = f"{request_id}/{file.filename}"
        storage_client.upload_file(file_name, file_content, overwrite=True)
        logger.info(f"File uploaded to temporary storage with ID: {request_id}")

        try:
            # Create a status file to track the processing status
            status_file_name = f"{request_id}/status.txt"
            storage_client.upload_file(status_file_name, ResponseStatus.IN_PROGRESS.value.encode(), overwrite=True)
        except Exception as e:
            logger.error(f"Error creating status file: {str(e)}")
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="Error creating status file",
                error=str(e)
            )
            return jsonify(response.to_dict()), 500

        # Start the background task properly
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create a background thread to run the async task
        def run_async_task():
            asyncio.run(document_processor.process_file(request_id, file_name, mode, status_file_name))

        thread = threading.Thread(target=run_async_task)
        thread.daemon = True
        thread.start()

        result_dto = ApiResponse(
            status=ResponseStatus.IN_PROGRESS,
            message="Document processing started",
            data={"request_id": request_id}
        )

        return jsonify(result_dto.to_dict()), 202

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        response = ApiResponse(
            status=ResponseStatus.ERROR,
            message="Error uploading file",
            error=str(e)
        )
        return jsonify(response.to_dict()), 500
        
@app.route('/CheckStatus', methods=['GET'])
def check_status():
    request_id = request.args.get('request_id')  
    if not request_id or not is_valid_uuid(request_id):
        response = ApiResponse(
            status=ResponseStatus.ERROR,
            message="Invalid request ID",
            error="request_id must be a valid UUID"
        )
        return jsonify(response.to_dict()), 400

    try:
        # Check if any files exist with this request_id prefix
        files = list(storage_client.list_files(prefix=request_id))
        if not files:
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="Request not found",
                error="Invalid request_id"
            )
            return jsonify(response.to_dict()), 404

        status_file_name = f"{request_id}/status.txt"
        try:
            status = storage_client.download_file(status_file_name).decode('utf-8').lower()
            
            # Simplified status mapping
            try:
                status_enum = ResponseStatus(status)
            except ValueError:
                logger.warning(f"Invalid status value received: {status}")
                status_enum = ResponseStatus.ERROR
            
            response = ApiResponse(
                status=status_enum,
                message="Status retrieved successfully",
                data={"status": status_enum.value}
            )
            return jsonify(response.to_dict()), 200

        except FileNotFoundError:
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="Status not found",
                error="Status information is missing"
            )
            return jsonify(response.to_dict()), 404

    except Exception as e:
        logger.error(f"Error checking status for request ID {request_id}: {str(e)}")
        response = ApiResponse(
            status=ResponseStatus.ERROR,
            message="Error checking status",
            error=str(e)
        )
        return jsonify(response.to_dict()), 500


@app.route('/DownloadResult', methods=['GET'])
def download_result():
    request_id = request.args.get('request_id')
    if not request_id or not is_valid_uuid(request_id):
        response = ApiResponse(
            status=ResponseStatus.ERROR,
            message="Invalid request ID",
            error="request_id must be a valid UUID"
        )
        return jsonify(response.to_dict()), 400

    try:
        # First check the status
        status_file_name = f"{request_id}/status.txt"
        try:
            status = storage_client.download_file(status_file_name).decode('utf-8').lower()
            if status != ResponseStatus.COMPLETED.value.lower():
                response = ApiResponse(
                    status=ResponseStatus.ERROR,
                    message="Result not ready",
                    error="Processing is not complete yet"
                )
                return jsonify(response.to_dict()), 400
        except FileNotFoundError:
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="Status not found",
                error="Status information is missing"
            )
            return jsonify(response.to_dict()), 404

        # Now try to get the result
        result_file_name = f"{request_id}/result.txt"
        try:
            result_content = storage_client.download_file(result_file_name)
            
            # Create ApiResponse with the result content
            response = ApiResponse(
                status=ResponseStatus.SUCCESS,
                message="Result retrieved successfully",
                data={
                    "content": result_content.decode('utf-8'),
                    "request_id": request_id
                }
            )
            
            return jsonify(response.to_dict()), 200
            
        except FileNotFoundError:
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="Result not found",
                error="Result file is missing"
            )
            return jsonify(response.to_dict()), 404

    except Exception as e:
        logger.error(f"Error downloading result for request ID {request_id}: {str(e)}")
        response = ApiResponse(
            status=ResponseStatus.ERROR,
            message="Error downloading result",
            error=str(e)
        )
        return jsonify(response.to_dict()), 500


@app.route('/CancelProcessing', methods=['POST'])
def cancel_processing():
    # Check both query parameters and request body for request_id
    request_id = request.args.get('request_id')
    if not request_id:
        try:
            req_body = request.get_json()
            request_id = req_body.get('request_id') if req_body else None
        except ValueError:
            pass

    if not request_id or not is_valid_uuid(request_id):
        response = ApiResponse(
            status=ResponseStatus.ERROR,
            message="Invalid request ID",
            error="request_id must be a valid UUID"
        )
        return jsonify(response.to_dict()), 400

    try:
        # Check if any files exist with this request_id prefix
        files = list(storage_client.list_files(prefix=request_id))
        if not files:
            response = ApiResponse(
                status=ResponseStatus.ERROR,
                message="Request not found",
                error="Invalid request_id"
            )
            return jsonify(response.to_dict()), 404

        # Update status to cancelled
        status_file_name = f"{request_id}/status.txt"
        try:
            storage_client.upload_file(status_file_name, ResponseStatus.CANCELLED.value.encode(), overwrite=True)
        except Exception as e:
            logger.warning(f"Failed to update status to cancelled: {str(e)}")

        # Clean up all files associated with this request
        for file_name in files:
            try:
                storage_client.delete_file(file_name)
            except Exception as e:
                logger.warning(f"Failed to delete file {file_name}: {str(e)}")

        response = ApiResponse(
            status=ResponseStatus.SUCCESS,
            message="Processing cancelled successfully",
            data={"request_id": request_id}
        )
        return jsonify(response.to_dict()), 200

    except Exception as e:
        logger.error(f"Error cancelling processing for request ID {request_id}: {str(e)}")
        response = ApiResponse(
            status=ResponseStatus.ERROR,
            message="Error cancelling processing",
            error=str(e)
        )
        return jsonify(response.to_dict()), 500


# if __name__ == '__main__':
# #    app.run()
#     app.run(host="0.0.0.0", port=8000)

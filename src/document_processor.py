import asyncio
import logging

from .models import ResponseStatus
from .storage import TempStorageClient
from .doclingwrapper import DoclingWrapper
from .markitdownwrapper import MarkItDownWrapper
from .processingmode import ProcessingMode

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, storage_client: TempStorageClient):
        self.storage_client = storage_client

    async def process_file(self, request_id: str, file_name: str, mode: ProcessingMode, status_file_name: str):
        try:
            # Get the file path from temporary storage
            file_path = self.storage_client.get_file_path(file_name)

            try:
                # Choose the appropriate converter based on the processing mode
                if mode == ProcessingMode.FAST:
                    converter = MarkItDownWrapper()
                elif mode == ProcessingMode.ACCURATE:
                    converter = DoclingWrapper()

                # Process the file using the local file path - make it async
                result = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: converter.convert(file_path)
                )
                logger.info(f"Conversion complete for request ID: {request_id}")

                # Update the status
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.storage_client.upload_file(status_file_name, ResponseStatus.COMPLETED.value.encode(), overwrite=True)
                )

                # Save the result to temporary storage
                output_file_name = f"{request_id}/result.txt"
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.storage_client.upload_file(output_file_name, result.encode() if isinstance(result, str) else result, overwrite=True)
                )

                # Cleanup the uploaded file
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.storage_client.delete_file(file_name)
                )
                logger.info(f"Temporary file {file_name} deleted.")

            except Exception as e:
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.storage_client.upload_file(status_file_name, ResponseStatus.FAILED.value.encode(), overwrite=True)
                )
                raise

        except Exception as e:
            logger.error(f"Error processing file for request ID {request_id}: {str(e)}")
            await asyncio.get_running_loop().run_in_executor(
                None, lambda: self.storage_client.upload_file(status_file_name, ResponseStatus.FAILED.value.encode(), overwrite=True)
            )

            try:
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.storage_client.delete_file(file_name)
                )
            except Exception as delete_error:
                logger.error(f"Failed to delete file after processing error: {str(delete_error)}") 
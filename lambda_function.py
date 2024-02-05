import os
import json
import boto3
from tempfile import NamedTemporaryFile
import pdfkit
import logging
from botocore.exceptions import ClientError
from templete_generator import get_formatted_templete
# from 
s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
options = {
    'page-size': 'Letter',
	 'orientation': 'Landscape',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ],
    'no-outline': None
}

def generate_pdf(html_template):
    # Generate PDF from HTML using pdfkit
    with NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_file:
        pdfkit.from_string(html_template,pdf_file.name,options)
        return pdf_file.name


def upload_file_to_s3(bucket,filepath,s3_file_path):
    """Uploads the generated PDF to s3.
    
    Args:
        bucket (str): Name of the s3 bucket to upload the PDF to.
        filename (str): Location of the file to upload to s3.
        
    Returns:
        The file key of the file in s3 if the upload was successful.
        If the upload failed, then `None` will be returned.
    """
    file_key = None 
    try:
        file_key = filepath.replace("/tmp/",f'{s3_file_path}/')
        s3.upload_file(Filename=filepath,Bucket=bucket,Key=file_key)
        logger.info("Successfully uploaded the pdf to %s as %s" %(bucket,file_key))
        
    except ClientError as e:
        logger.error("Failed to upload file to s3")
        logger.error(e)
        file_key= None 
    upload_location = f'https://{bucket}.s3.amazonaws.com/{file_key}'
    return file_key,upload_location


def lambda_handler(event,context):
    try:
        try:
            userDetails = event["user_details"]
            s3_file_path = event["file_path"]
        except KeyError:
            error_message = 'Missing required "compiled_template" parameter from request payload.'
            logger.error(error_message)
            return {
            'status': 400,
            'body': json.dumps(error_message),
            }
        compiled_template = get_formatted_templete(userDetails["name"],userDetails["country"],userDetails["startDate"],userDetails["endDate"])
        pdf_file_path = generate_pdf(compiled_template)
        print(pdf_file_path)
        
        # uploading PDF to s3
        # bucket_name = os.environ["AWS_S3_BUCKET"]
        # file_key,upload_location = upload_file_to_s3(bucket=bucket_name,filepath=pdf_file_path,s3_file_path=s3_file_path)
        # try:
        #     os.unlink(pdf_file_path)
        # except FileNotFoundError:
        #     error_message = ("Unable to unlink the file")
        #     logger.error(error_message)
        #     return {
        #     'status': 400,
        #     'body': json.dumps(error_message),
        #     }
            
        # return {
        #     "message":"PDF conversion and upload successful!",
        #     "s3_bucket":bucket_name,
        #     "s3_key":file_key,
        #     "s3_location":upload_location
        # }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise Exception('PDF conversion and upload failed') from e

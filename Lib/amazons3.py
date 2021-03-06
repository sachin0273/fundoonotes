from Fundoo.settings import base

from utils import build_url


class AmazonS3:
    """Upload or Delete file on amazon s3 bucket"""

    def upload_file(self, image, object_name):
        """

        :param image: File to upload
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False

        """
        # If S3 object_name was not specified, use file_name
        try:

            # Upload the file
            bucket = base.BUCKET
            base.s3.upload_fileobj(image, bucket, object_name)
            file_url = build_url(base.S3_BASE_URL, bucket + '/' + object_name + '/')
            print(file_url)
            return file_url
        except Exception:
            return False

    def delete_file(self, image_key):
        """
        
        :param image_key: here we passing object name exist in s3
        :return: this function used for delete the image from amazon s3 bucket from a

        """

        try:
            response = base.s3.delete_object(
                Bucket=base.BUCKET,
                Key=image_key,
            )
            return response
        except Exception:
            return False

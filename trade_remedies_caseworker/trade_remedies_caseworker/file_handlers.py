import re
import os
import boto3
import logging
from pathlib import Path
from django.utils import timezone
from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadedfile import (
    InMemoryUploadedFile, TemporaryUploadedFile,
)
from django.db.models import FileField
from storages.backends.s3boto3 import S3Boto3StorageFile, S3Boto3Storage
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger(__name__)


class S3Wrapper(object):
    _s3_client = None

    @classmethod
    def get_client(cls):
        if not cls._s3_client:
            logger.info('Instantiating S3 client')
            cls._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        return cls._s3_client


def s3_client():
    return S3Wrapper.get_client()


UUID4_REGEX = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')

class S3FileField(FileField):
    def save(self, name, content, save=True):
        name = self.field.generate_filename(self.instance, name)
        self.name = name  # self.storage.save(name, content, max_length=self.field.max_length)
        setattr(self.instance, self.field.name, self.name)
        self._committed = True

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()
    save.alters_data = True


def upload_document_to(request, filename):
    """
    Derive the upload path into S3.
    This is made of the root directory, partitioned into the case id.
    Current upload time is appended to the file name.
    """
    filename_base, filename_ext = os.path.splitext(filename)
    _now = timezone.now().strftime("%Y%m%d%H%M%S")
    _filename = f'{filename_base}_{_now}{filename_ext}'
    path = Path(settings.S3_DOCUMENT_ROOT_DIRECTORY)
    prefix = request.GET.get('__prefix')
    if prefix:
        path /= prefix
    # case_id = UUID4_REGEX.findall(request.path)
    # if case_id:
    #     path /= str(case_id[0])
    path /= _filename
    return str(path)


class ThreadedS3ChunkUploader(ThreadPoolExecutor):
    """
    A specialised ThreadPoolExecutor to upload
    files into S3 using up to 10 concurrent threads
    """
    def __init__(self, client, bucket, key, upload_id, max_workers=None):
        """Initialise a new ThreadedS3ChunkUploader

        Arguments:
            client {object} -- S3 client
            bucket {str} -- Bucket name
            key {str} -- File S3 key
            upload_id {str} -- MultiPart upload id from S3
            max_workers {int} -- Max number of threads
        """
        max_workers = max_workers or 10
        self.bucket = bucket
        self.key = key
        self.upload_id = upload_id
        self.client = client
        self.part_number = 0
        self.parts = []
        self.queue = []
        self.current_queue_size = 0
        super().__init__(max_workers=max_workers)

    def add(self, body):
        """Add a chunk to the internal queue. When the queue's size surpasses
        5MB (the min chunk size for S3), it is then packaged into a future
        and loaded into the threadpool.

        Arguments:
            body {bytes} -- A file chunk
        """
        content_length = 0
        if body:
            content_length = len(body)
            self.queue.append(body)
            self.current_queue_size += content_length
        if not body or self.current_queue_size > 5 * 1024 * 1024:
            self.part_number += 1
            _body = self.drain_queue()
            future = self.submit(
                self.client.upload_part,
                Bucket=self.bucket,
                Key=self.key,
                PartNumber=self.part_number,
                UploadId=self.upload_id,
                Body=_body,
                ContentLength=len(_body),
            )
            self.parts.append((self.part_number, future))

    def drain_queue(self):
        """Drain the internal queue. This happens when the internal queue
        passes 5MB in size

        Returns:
            [bytes] -- The current queue part
        """
        body = b''.join(self.queue)
        self.queue = []
        self.current_queue_size = 0
        return body

    def get_parts(self):
        """Return the result of all the futures held in self.parts

        Returns:
            [list<dict>] -- S3 ready list of part dicts
        """
        return [{
            'PartNumber': part[0],
            'ETag': part[1].result()['ETag'],
            } for part in self.parts
        ]


class S3FileUploadHandler(FileUploadHandler):
    """
    Upload handler that streams data direct into S3
    """
    def new_file(self, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        super().new_file(*args, **kwargs)
        self.parts = []
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.s3_key = upload_document_to(self.request, self.file_name)
        self.client = s3_client()
        self.multipart = self.client.create_multipart_upload(
            Bucket=self.bucket_name,
            Key=self.s3_key
        )
        self.upload_id = self.multipart['UploadId']
        self.executor = ThreadedS3ChunkUploader(
            self.client,
            self.bucket_name,
            key=self.s3_key,
            upload_id=self.upload_id)
        # prepare a storages object as a file placeholder
        self.storage = S3Boto3Storage()
        self.file = S3Boto3StorageFile(self.s3_key, 'w', self.storage)
        self.file.original_name = self.file_name

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding):
        self.request = input_data
        self.content_length = content_length
        self.META = META
        return None

    def receive_data_chunk(self, raw_data, start):
        """
        Receive a single file chunk from the browser
        and add it to the executor
        """
        self.executor.add(raw_data)

    def file_complete(self, file_size):
        """
        Triggered when the last chuck of the file is received and handled.
        """
        # Add an empty body to drain the executor queue
        self.executor.add(None)
        # close the file placeholder
        closed = self.file.close()
        # collect all the file parts from the executor
        parts = self.executor.get_parts()
        # complete the multiplart upload
        _result = self.client.complete_multipart_upload(
            Bucket=self.bucket_name,
            Key=self.s3_key,
            UploadId=self.upload_id,
            MultipartUpload={
                'Parts': parts
            }
        )
        # shutdown the executor and set the final file size on the file
        self.executor.shutdown()
        self.file.file_size = file_size
        return self.file

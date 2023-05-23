from django.apps import AppConfig


class CasesConfig(AppConfig):
    name = "core"

    def ready(self):
        from django_chunk_upload_handlers import clam_av
        from django.core.files import uploadhandler
        from django.conf import settings

        clam_av.ClamAVFileUploadHandler.chunk_size = settings.DEFAULT_CHUNK_SIZE
        uploadhandler.FileUploadHandler.chunk_size = settings.DEFAULT_CHUNK_SIZE

from django.http import StreamingHttpResponse


def proxy_stream_file_download(stream, filename):
    """
    Send a file back as a streamed response
    :param path: Full path to the file
    :param mime_type: The file's mime type
    :param chunk_size: Optional chunk size for sending the file [Default: 8192]
    :return: A StreamingHttpResponse streaming the file
    """
    response = StreamingHttpResponse(
        stream, content_type=stream.headers.get('Content-Type'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

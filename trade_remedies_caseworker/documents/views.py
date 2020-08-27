import json
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from documents.utils import proxy_stream_file_download
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from core.constants import SECURITY_GROUPS_TRA


class BaseDocumentTemplateView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    pass


class DocumentsView(BaseDocumentTemplateView):
    """
    A view into TRA uploaded system documents
    """
    def get(self, request, document_id=None, *args, **kwargs):
        fields = json.dumps({
            'Document': {
                'name':0,
                'id':0,
                'created_at':0,
                'size':0,
                'confidential':0,
            }
        })
        criteria = json.dumps({
            'confidential': False
        })
        content_type = request.META.get('CONTENT_TYPE')
        documents = self.client(request.user).get_system_documents(fields=fields, criteria=criteria) or []
        return HttpResponse(json.dumps(documents), content_type=content_type)


class DocumentStreamDownloadView(BaseDocumentTemplateView):
    groups_required = SECURITY_GROUPS_TRA

    def get(self, request, document_id, submission_id=None, *args, **kwargs):
        client = self.client(request.user)
        document = client.get_document(document_id)
        document_stream = client.get_document_download_stream(document_id, submission_id=submission_id)
        return proxy_stream_file_download(document_stream, filename=document.get('name'))


class DocumentDownloadView(BaseDocumentTemplateView):
    groups_required = SECURITY_GROUPS_TRA

    def get(self, request, document_id, submission_id=None, *args, **kwargs):
        document = self.client(request.user).get_document_download_url(document_id)
        return redirect(document.get('download_url'))



class ApplicationBundleView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    template_name = 'cases/bundles/application_bundles.html'

    def get(self, request, *args, **kwargs):
        status = request.GET.get('tab', 'LIVE')
        bundles = self.client(request.user).get_document_bundles(status=status)
        tabs = {
            "value": status,
            "tabList": [
                {"label": 'Live', "value": "LIVE", "sr_text": "Show live bundles"},
                {"label": 'Draft', "value": "DRAFT", "sr_text": "Show bundles in draft"}
            ],
        }

        context = {
            'body_classes': "full-width",
            'bundles': bundles,
            'tabs': tabs,
        }
        return render(request, self.template_name, context)


class ApplicationBundleFormView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    template_name = 'cases/bundles/bundle_form_type.html'

    def get(self, request, *args, **kwargs):
        enums = self.client(request.user).get_all_case_enums()
        context = {
            'body_classes': "full-width",
            'edit': 'type',
            'bundle': {'id': 'create'},
            'case_types': enums['case_types'],
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        case_type_id = request.POST.get('case_type_id')
        submission_type_id = None
        if case_type_id and case_type_id.startswith('SUB:'):
            submission_type_id = case_type_id.split(':')[-1]
            case_type_id = None
        bundle_id = request.POST.get('bundle_id')
        response = self.client(request.user).create_document_bundle(
            case_type_id=case_type_id,
            submission_type_id=submission_type_id)
        return redirect(f"/document/bundle/{response['id']}/")


class ApplicationBundleDocumentsFormView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    """
    The form view starts at the last stage that still requires information.
    For example, if a type and documents are already present the form
    will initially open up in the description entry stage.
    """
    def get(self, request, bundle_id=None, *args, **kwargs):
        client = self.client(request.user)
        bundle = client.get_document_bundle(bundle_id)
        edit_stage = request.GET.get('edit')
        if not edit_stage:
            if bundle.get('status') == 'LIVE':
                edit_stage = 'complete'
            elif bundle.get('documents'):
                edit_stage = 'finalise'
            elif bundle.get('case_type') or bundle.get('submission_type'):
                edit_stage = 'documents'
        template_name = f'cases/bundles/bundle_form_{edit_stage}.html'
        enums = client.get_all_case_enums()
        counts = {'virus': 0, 'unscanned': 0}
        for document in (bundle.get('documents') or []):
            safe = document.get('safe')
            if not safe:
                if safe == False:
                    counts['virus'] += 1
                else:
                    counts['unscanned'] += 1
        context = {
            'body_classes': "full-width",
            'edit': edit_stage,
            'force_delete_option': True,
            'case_types': enums['case_types'],
            'bundle': bundle,
            'bundle_id': bundle_id,
            'counts' : counts,
        }
        return render(request, template_name, context)

    def post(self, request, bundle_id=None,  *args, **kwargs):
        client = self.client(request.user)
        case_type_id = request.POST.get('case_type_id')
        submission_type_id = None
        if case_type_id and case_type_id.startswith('SUB:'):
            submission_type_id = case_type_id.split(':')[-1]
            case_type_id = None
        document_ids = request.POST.getlist('case_files')
        bundle_id = bundle_id or request.POST.get('bundle_id')
        description = request.POST.get('description')
        finalise = request.POST.get('finalise')
        draft = request.POST.get('draft')
        delete = request.POST.get('delete')
        confidential = request.POST.getlist('confidential', ['conf'])
        if delete == 'delete':
            client.delete_application_bundle(bundle_id)
            if request.POST.get('return-json'):
                return HttpResponse(json.dumps({'redirect_url': '/document/bundles/'}))
            else:
                return redirect('/document/bundles/')
        else:
            redirect_path = f"/document/bundle/{bundle_id}/"
            if request.FILES:
                for i, _file in enumerate(request.FILES.getlist('files')):
                    data = {
                        'bundle_id': bundle_id,
                        'confidential': confidential[i] == 'conf',
                        'document_name': _file.original_name,
                        'file_name': _file.name,
                        'file_size': _file.file_size,
                    }
                    try:
                        document = client.upload_document(
                            system=True,
                            data=data)
                    except Exception:
                        return redirect(f'/document/bundle/{bundle_id}/?error=upload')
            elif document_ids and bundle_id:
                for document_id in document_ids:
                    document = client.attach_document(
                        data={
                            'bundle_id': bundle_id,
                        },
                        document_id=document_id
                    )
            elif bundle_id:
                update_kwargs = {}
                if description != None:
                    update_kwargs['description'] = description
                if finalise:
                    update_kwargs['status'] = 'LIVE'
                    redirect_path = '/document/bundles/'
                elif draft:
                    update_kwargs['status'] = 'DRAFT'
                    redirect_path = '/document/bundles/?tab=DRAFT'
                response = client.update_document_bundle(bundle_id, update_kwargs)
        return redirect(redirect_path)

    def delete(self, request, bundle_id, document_id, *args, **kwargs):
        response = self.client(request.user).remove_bundle_document(bundle_id, document_id)
        return HttpResponse('true')


class DocumentSearchView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):
    """
    Global document search (above case level). Currently not yet in use.
    """
    template_name = 'documents/documents.html'

    def post(self, request):
        client = self.client(request.user)
        query = request.POST.get('query')
        case_id = request.POST.get('case_id')
        conf_status = request.POST.get('confidential_status')
        user_type = request.POST.get('user_type')
        response = client.search_documents(
            case_id=case_id,
            query=query,
            confidential_status=conf_status,
            user_type=user_type,
        )
        return render(request, self.template_name, {
            'body_classes': "full-width",
            'documents': response.pop('results', []),
            **response
        })

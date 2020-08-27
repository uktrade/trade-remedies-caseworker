import re
import json
from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from trade_remedies_client.mixins import TradeRemediesAPIClientMixin
from core.constants import SECURITY_GROUPS_TRA
from django.core.cache import cache
from django.utils import timezone
from core.utils import (
    deep_index_items_by,
    pluck,
    to_json, from_json,
    get,
)


class TaskView(LoginRequiredMixin, TemplateView, TradeRemediesAPIClientMixin):

    fields = {
	    'Task': {
	    	'id':0,
	    	'name':0,
	    	'case_id':0,
	    	'created_by':{
	    		'name':0
            },
            'due_date':0,
            'assignee': {
                'name': 0
            }
	    }
    }

    def get(self, request, task_id=None):
        last_update = cache.get('lasttaskupdate')
        if not last_update:
            cache.set('lasttaskupdate',timezone.now().strftime('%Y-%m-%dT%H:%M:%S'), 60*60)
            last_update = cache.get('lasttaskupdate')

        if(request.GET.get('last')):
            return HttpResponse(json.dumps({'result':last_update}), content_type='application/json')
        query = request.GET.get('query') or json.dumps([{'field':'id', 'value':str(task_id)}])
        fields = request.GET.get('fields') or json.dumps(self.fields)
        tasks = self.client(request.user).get_tasks(query=query, fields=fields)
        return HttpResponse(json.dumps({'result':{
            'tasks': tasks,
            'lastupdate': cache.get('lasttaskupdate')
        }}), content_type='application/json')

    def post(self, request, task_id=None):
        task_id = task_id or request.POST.get('task_id')
        data = pluck(request.POST, [
            'id', 'name','description','due_date','content_type','model_id',
            'model_key','assignee','assignee_id','case_id',
            'priority','status','data','btn_value', 'data_estimate', 'data_remaining'])

        json_data = data.get('data') or {}
        regex = r"^data_"
        for param_key in request.POST:
            matches = re.split(regex, param_key)
            if len(matches) > 1:
                sub_key = matches[1]
                value = request.POST[param_key]
                if value == '__remove':
                    if get(json_data, sub_key):
                        json_data.pop(sub_key)
                else:
                    json_data[sub_key] = value
        data['data'] = json.dumps(json_data)
        if data.get('btn_value') == 'save':
            cache.set('lasttaskupdate',timezone.now().strftime('%Y-%m-%dT%H:%M:%S'), 60*60)
            if not task_id:
                # we need the object attachments to create task
                result = self.client(request.user).create_update_task( content_type=request.POST.get('content_type'), model_id=request.POST.get('model_id'), data=data)
            else:
                result = self.client(request.user).create_update_task( task_id=task_id, data=data )
        elif get(data,'btn_value') == 'delete':
            result = self.client(request.user).delete_task( task_id=get(data,'id'))
        return HttpResponse(json.dumps({'result':result}), content_type='application/json')

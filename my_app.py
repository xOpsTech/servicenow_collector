from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS, cross_origin
import json

app = Flask(__name__)
api = Api(app)
CORS(app)

import requests  # Set the request parameters

user = 'admin'
pwd = 'RootAdmin1!'

TODOS = {
    'todo1': {'task': 'build an API'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))


headers = {"Accept": "application/json"}  # Do the HTTP request
parser = reqparse.RequestParser()

# parser.add_argument('data')

priority_mapping = {
    '1': 'P1',
    '2': 'P2',
    '3': 'P3',
    '4': 'P4',
    '5': 'P5',
}

active_status_mapping = {
    "true": "open",
    "false": "closed"
}


class Incident(Resource):
    def get(self):
        # Set proper headers

        url = 'https://dev33740.service-now.com/api/now/stats/incident?sysparm_count=true&sysparm_group_by=incident_state&sysparm_having=&sysparm_display_value=true'
        response = requests.get(url, auth=(user, pwd), headers=headers)

        # Check for HTTP codes other than 200
        if response.status_code != 200:
            result = {'status:', response.status_code, 'Error Response:', response.json()}
            return result, response.status_code

        result = {'status': response.status_code, 'data': response.json()}
        return result, response.status_code

    def get(self):
        url_args = request.args
        duration = url_args.get("duration")

        if duration:
            url = 'https://dev33740.service-now.com/api/now/stats/incident?sysparm_query=sys_created_onONLast%20{duration}%20minutes%40javascript%3Ags.minutesAgoStart({duration})%40javascript%3Ags.minutesAgoEnd(0)&sysparm_count=true&sysparm_sum_fields=&sysparm_group_by=active&sysparm_display_value=all'.format(
                duration=duration)
            aggs_by_active = call_api(url)

            url = 'https://dev33740.service-now.com/api/now/stats/incident?sysparm_query=sys_created_onONLast%20{duration}%20minutes%40javascript%3Ags.minutesAgoStart({duration})%40javascript%3Ags.minutesAgoEnd(0)&sysparm_count=true&sysparm_sum_fields=&sysparm_group_by=priority&sysparm_display_value=all'.format(
                duration=duration)
            aggs_by_priority = call_api(url)

            url = 'https://dev33740.service-now.com/api/now/table/incident?sysparm_query=severity%3D1%5Esys_created_onONLast%20{duration}%20minutes%40javascript%3Ags.minutesAgoStart({duration})%40javascript%3Ags.minutesAgoEnd(0)&sysparm_fields=number&sysparm_limit=1000'.format(
                duration=duration)
            incident_numbers = call_api(url)

            final_result = dict()
            final_result['data'] = []

            if aggs_by_active[1] == 200:
                final_result['status'] = 200
                aggs_by_active_dict = dict()
                aggs_by_active_dict['aggs_by_active'] = dict()
                total = 0
                for result in aggs_by_active[0]['data']['result']:
                    count = result['stats']['count']
                    value = result['groupby_fields'][0]['value']

                    total += int(count)
                    aggs_by_active_dict['aggs_by_active'][active_status_mapping[value]] = count

                aggs_by_active_dict['aggs_by_active']['total'] = total
                final_result['data'].append(aggs_by_active_dict)
            else:
                final_result['status'] = aggs_by_active[1]

            if aggs_by_priority[1] == 200:
                final_result['status'] = 200
                aggs_by_priority_dict = dict()
                aggs_by_priority_dict['aggs_by_priority'] = dict()
                total = sum([int(result['stats']['count']) for result in aggs_by_priority[0]['data']['result']])
                for result in aggs_by_priority[0]['data']['result']:
                    count = int(result['stats']['count'])
                    value = result['groupby_fields'][0]['value']

                    # total += count
                    aggs_by_priority_dict['aggs_by_priority'][priority_mapping[value]] = round(count / float(total) * 100, 2)

                aggs_by_priority_dict['aggs_by_priority']['total'] = total
                final_result['data'].append(aggs_by_priority_dict)
            else:
                final_result['status'] = aggs_by_priority[1]

            incident_dict = {}
            if incident_numbers[1] == 200:
                incident_list = [result['number'] for result in incident_numbers[0]['data']['result']]
                incident_dict['p1_incidents'] = incident_list
                incident_dict['total'] = len(incident_list)
                final_result['data'].append(incident_dict)
            else:
                final_result['status'] = incident_numbers[1]

            # if aggs_by_priority[1] == 200:
            #     final_result['status'] = 200
            #     final_result['data'].append({'aggs_by_priority': aggs_by_priority[0]})
            # else:
            #     final_result['status'] = aggs_by_priority[1]

            return final_result, final_result['status']
        else:
            return {'status': 400, 'error': 'duration field is missing'}

    def post(self):
        data = request.get_json()["data"]
        print data
        # response = requests.post(url, auth=(user, pwd), headers=headers, data='{"short_description":"Test"}')
        url = 'https://dev33740.service-now.com/api/now/table/incident'
        response = requests.post(url, auth=(user, pwd), headers=headers, data=json.dumps(data))

        # Check for HTTP codes other than 200
        if response.status_code != 201:
            result = {'status:', response.status_code, 'Error Response:', response.json()}
            return result, response.status_code

        result = {'status': response.status_code, 'data': response.json()}
        return result, response.status_code


def call_api(url):
    response = requests.get(url, auth=(user, pwd), headers=headers)
    # Check for HTTP codes other than 200
    if response.status_code != 200:
        result = {'status:', response.status_code, 'error:', response.json()}
        return result, response.status_code

    result = {'status': response.status_code, 'data': response.json()}
    return result, response.status_code


api.add_resource(Incident, '/incidents')
# api.add_resource(Incident, '/incidents/<duration>')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

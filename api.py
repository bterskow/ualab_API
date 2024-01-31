from env import ENV
from liqpay import LiqPay
from time import time
import json
import re
import boto3
import random
import string


# recieving constants fron ENV class
env = ENV()
constans = env.data()
smtp_server = constans.get('smtp_server')
smtp_account = constans.get('smtp_account')
smtp_password = constans.get('smtp_password')
aws_access_key_id = constans.get('aws_access_key_id')
aws_secret_access_key = constans.get('aws_secret_access_key')
dynamodb_table_name = constans.get('dynamodb_table_name')
liqpay_public_key = constans.get('liqpay_public_key')
liqpay_private_key = constans.get('liqpay_private_key')
server_url = constans.get('server_url')


dynamodb_client = boto3.client('dynamodb', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='us-east-1')
liqpay_client = LiqPay(liqpay_public_key, liqpay_private_key)


class OtherOperations:
	def init_secret_key(self):
		characters = string.ascii_letters + string.digits
		key = ''.join(random.choice(characters) for _ in range(32))
		return key


class Model:
	def __init__(self):
		self.otherOperations = OtherOperations()


	def register(self):
		try:
			secret_key = self.otherOperations.init_secret_key();
			key = dynamodb_client.get_item(TableName=dynamodb_table_name, Key={'secret_key': {'S': secret_key}})

			if 'Item' in key.keys():
				return self.register()

			created_at = round(time() * 1000)

			dynamodb_client.put_item(TableName=dynamodb_table_name, Item={'secret_key': {'S': secret_key}, 'created_at': {'S': str(created_at)}, 'subscription': {'S': 'false'}, 'links': {'S': json.dumps({'links': []})}})

			return {'status': 200, 'message': None, 'user': {'secret_key': secret_key, 'subscription': 'false', 'created_at': str(created_at), 'links': json.dumps({'links': []})}}
		except Exception as e:
			return {'status': 500, 'message': str(e), 'user': None}


	def auth(self, secret_key):
		try:
			user = dynamodb_client.get_item(TableName=dynamodb_table_name, Key={'secret_key': {'S': secret_key}})

			if 'Item' in user.keys():
				user = user.get('Item')
				for key, value in user.items():
					user[key] = user[key]['S']

				return {'status': 200, 'message': None, 'user': user}

			return {'status': 500, 'message': 'User not found!', 'user': None}
		except Exception as e:
			return {'status': 500, 'message': str(e), 'user': None}


	def redirect(self, domain_name):
		try:
			scan = dynamodb_client.scan(TableName=dynamodb_table_name)
			items = scan.get('Items')
			current_time = round(time() * 1000)

			if items is None:
				return {'status': 500, 'message': 'Error 404. No domain names!'}

			for item in items:
				links = json.loads(item['links']['S'])
				if len(links['links']) != 0:
					for link in links['links']:
						if link['domain_name'] == domain_name:
							if item['subscription']['S'] == 'false':
								if current_time - int(item['created_at']['S']) < 2592000000:
									return {'status': 200, 'message': link['href']}

								return {'status': 500, 'message': 'Error 403. Forbidden!'}
							else:
								return {'status': 200, 'message': link['href']}

			return {'status': 500, 'message': 'Error 404. Page not found!'}
		except Exception as e:
			return {'status': 500, 'message': f'Error: 500. {str(e)}'}


	def delete_domain(self, data):
	    try:
	        secret_key = data.get('secret_key')
	        domain_name = data.get('domain_name')

	        if None in [secret_key, domain_name]:
	            return {'status': 400, 'message': 'Incomplete request data!'}

	        user_response = dynamodb_client.get_item(TableName=dynamodb_table_name, Key={'secret_key': {'S': secret_key}})
	        user_item = user_response.get('Item')

	        if not user_item:
	            return {'status': 404, 'message': 'User not found!'}

	        links = json.loads(user_item.get('links', {}).get('S', '{"links": []}'))

	        if len(links['links']) != 0:
	            updated_links = {'links': []}

	            for link in links['links']:
	                if link['domain_name'] != domain_name:
	                    updated_links['links'].append(link)

	            dynamodb_client.update_item(
	                TableName=dynamodb_table_name,
	                Key={'secret_key': {'S': secret_key}},
	                AttributeUpdates={'links': {'Value': {'S': json.dumps(updated_links)}, 'Action': 'PUT'}}
	            )

	            return {'status': 200, 'message': 'Success! Custom link deleted!'}

	        return {'status': 404, 'message': 'Custom links not found!'}
	    except Exception as e:
	        return {'status': 500, 'message': str(e)}


	def create_new_domain(self, data):
	    try:
	        secret_key = data.get('secret_key')
	        href = data.get('href')
	        domain_name = data.get('domain_name')

	        if None in [secret_key, href, domain_name]:
	            return {'status': 400, 'message': 'Incomplete request data!'}

	        scan_response = dynamodb_client.scan(TableName=dynamodb_table_name)
	        items = scan_response.get('Items', [])

	        for item in items:
	            links = json.loads(item.get('links', {'S': '{"links": []}'}).get('S'))
	            for link in links['links']:
	                if link['domain_name'] == domain_name:
	                    return {'status': 409, 'message': 'This custom link already exists!'}

	        # Retrieve user information
	        user_response = dynamodb_client.get_item(TableName=dynamodb_table_name, Key={'secret_key': {'S': secret_key}})
	        user_item = user_response.get('Item')

	        if not user_item:
	            return {'status': 404, 'message': 'User not found!'}

	        links = json.loads(user_item.get('links', {'S': '{"links": []}'}).get('S'))
	        links['links'].append({'href': href, 'domain_name': domain_name})

	        dynamodb_client.update_item(
	            TableName=dynamodb_table_name,
	            Key={'secret_key': {'S': secret_key}},
	            AttributeUpdates={'links': {'Value': {'S': json.dumps(links)}, 'Action': 'PUT'}}
	        )

	        return {'status': 200, 'message': 'Success! New custom link created!'}
	    except Exception as e:
	        return {'status': 500, 'message': str(e)}


	def subscription(self, secret_key):
		try:
			user = dynamodb_client.get_item(TableName=dynamodb_table_name, Key={'secret_key': {'S': secret_key}})

			if 'Item' not in user.keys():
				return {'status': 500, 'message': 'User not found!', 'href': None}

			if user['Item']['subscription']['S'] == 'true':
				return {'status': 500, 'message': 'User has subscription!', 'href': None}

			order_id = round(time() * 1000)

			invoice = liqpay_client.api("request", {
				"action"    : "invoice_send",
				"version"   : "3",
				"email"     : smtp_account,
				"amount"    : "7",
				"description": f"elbo.live: infnity subscription. Buyer: {secret_key}",
				"currency"  : "USD",
				"order_id"  : order_id,
				"server_url": server_url,
				"language"  : 'en'
			})

			href = invoice.get('href')

			if href is None:
				return {'status': 500, 'message': "Invoice didn't create. Try again!", 'href': None}

			return {'status': 200, 'message': None, 'href': href}
		except Exception as e:
			return {'status': 500, 'message': str(e), 'href': None}


	async def fix_pay(self, request):
		try:
			form = await request.form()
			data = form.get('data')

			if data['status'] in ['error', 'failure']:
				return {'status': 500, 'message': data['err_description']}

			secret_key = data['description'].split('Buyer: ')[1]

			user = dynamodb_client.get_item(TableName=dynamodb_table_name, Key={'secret_key': {'S': secret_key}})

			if 'Item' in user.keys():
				dynamodb_client.update_item(
		            TableName=dynamodb_table_name,
		            Key={'secret_key': {'S': secret_key}},
		            AttributeUpdates={'subscription': {'Value': {'S': 'true'}, 'Action': 'PUT'}}
		        )

				return {'status': 200, 'message': 'Success! Subscription is up!'}

			return {'status': 500, 'message': 'User not found!'}
		except Exception as e:
			return {'status': 500, 'message': str(e)}
import os


class ENV:
	def data(self):
		return {
			'smtp_server': os.environ.get('smtp_server'),
			'smtp_account': os.environ.get('smtp_account'),
			'smtp_password': os.environ.get('smtp_password'),
			'aws_access_key_id': os.environ.get('aws_access_key_id'),
			'aws_secret_access_key': os.environ.get('aws_secret_access_key'),
			'dynamodb_table_name': os.environ.get('dynamodb_table_name'),
			'liqpay_public_key': os.environ.get('liqpay_public_key'),
			'liqpay_private_key': os.environ.get('liqpay_private_key'),
			'server_url': os.environ.get('server_url'),
		}
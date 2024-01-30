from fastapi import FastAPI, Request, Form, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from api import Model
from loguru import logger
import json 
import uvicorn 


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='application')
app.add_middleware(CORSMiddleware, allow_headers=['*'], allow_methods=['*'], allow_origins=['*'])
model = Model()


@app.get('/', name='default_api_page')
def default():
	return RedirectResponse('/docs')


@app.get('/register/proccessing', name='register')
def register():
	try:
		register = model.register()
		return JSONResponse(content={'status': register['status'], 'message': register['message'], 'user': register['user']}, status_code=200)
	except Exception as e:
		return JSONResponse(content={'status': 500, 'message': str(e), 'user': None}, status_code=500)


@app.get('/auth/proccessing', name='auth')
def auth(secret_key: str = Query(...)):
	try:
		auth = model.auth(secret_key)
		return JSONResponse(content={'status': auth['status'], 'message': auth['message'], 'user': auth['user']}, status_code=200)
	except Exception as e:
		return JSONResponse(content={'status': 500, 'message': str(e), 'user': None}, status_code=500)


@app.get('/{domain_name}', name='redirect')
def redirect(domain_name: str):
	try:
		redirect = model.redirect(domain_name)
		if redirect['status'] == 500:
			html = f"<div style='height: 100%; display: flex; align-items: center; justify-content: center; font-size: 25px; font-weight: bold;'><p>{redirect['message']}</p></div>"
			return HTMLResponse(html)

		return RedirectResponse(redirect['message'])
	except Exception as e:
		html = f"<div style='height: 100%; display: flex; align-items: center; justify-content: center; font-size: 25px; font-weight: bold;'><p>{str(e)}</p></div>"
		return HTMLResponse(html)


@app.post('/delete_domain', name='delete_domain')
def delete_domain(data: str = Form(...)):
	try:
		data = json.loads(data)
		delete_domain = model.delete_domain(data)
		return JSONResponse(content={'status': delete_domain['status'], 'message': delete_domain['message']}, status_code=200)
	except Exception as e:
		return JSONResponse(content={'status': 500, 'message': str(e)}, status_code=500)


@app.post('/create_new_domain', name='delete_domain')
def create_new_domain(data: str = Form(...)):
	try:
		data = json.loads(data)
		create_new_domain = model.create_new_domain(data)
		return JSONResponse(content={'status': create_new_domain['status'], 'message': create_new_domain['message']}, status_code=200)
	except Exception as e:
		return JSONResponse(content={'status': 500, 'message': str(e)}, status_code=500)


@app.get('/subscription/proccessing', name='subscription')
def subscription(secret_key: str = Query(...)):
	try:
		subscription = model.subscription(secret_key)
		return JSONResponse(content={'status': subscription['status'], 'message': subscription['message'], 'href': subscription['href']}, status_code=200)
	except Exception as e:
		return JSONResponse(content={'status': 500, 'message': str(e), 'href': None}, status_code=500)


@app.post('/fix_pay', name='fix_pay')
async def fix_pay(request: Request):
	try:
		fix_pay = await model.fix_pay(secret_key)
		message = fix_pay['message']
		if fix_pay['status'] == 500:
			logger.error(message)
		else:
			logger.info(message)

		return True
	except Exception as e:
		logger.error(str(e))
		return True


if __name__ == '__main__':
	uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)
import requests, os


def register(request):
    if not request.form:
        return "Missing Credentials", 400

    form_data = {
        "email": request.form["email"],
        "password": request.form["password"]
    }
    response = requests.post(
        url=f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/signup",
        data=form_data
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
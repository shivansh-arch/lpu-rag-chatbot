import requests

from mock_student_api.config import BASE_URL


def get_attendance(student_id):
    url = f"{BASE_URL}/students/{student_id}/attendance"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["attendance"]

    return None


def get_cgpa(student_id):
    url = f"{BASE_URL}/students/{student_id}/cgpa"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["cgpa"]

    return None


def get_fee_status(student_id):
    url = f"{BASE_URL}/students/{student_id}/fee-status"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["fee_status"]

    return None


def get_messages(student_id):
    url = f"{BASE_URL}/students/{student_id}/messages"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["messages"]

    return None